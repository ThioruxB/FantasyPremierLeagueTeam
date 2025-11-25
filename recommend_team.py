import pandas as pd
from thefuzz import fuzz, process
from datetime import datetime
import numpy as np
import pulp
import os
from collections import Counter
import sys

# --- Configuration ---
FPL_BUDGET = 1000 # £100.0m (FPL prices are in 0.1m, so 100.0m is 1000)
SQUAD_SIZE = 15
GK_COUNT = 2
DEF_COUNT = 5
MID_COUNT = 5
FWD_COUNT = 3
MAX_PLAYERS_PER_TEAM = 3
N_SIMULATIONS = 100

# Weights for performance score (and volatility calculation)
WEIGHTS = {
    'xP': 0.6, # xP is not in incidents, handled separately
    'Goal': 10,
    'Assist': 7,
    'ShotOnTarget': 0.5,
    'KeyPass': 0.3,
    'YellowCard': -2,
    'RedCard': -5,
    # Map internal metric names to incident types if needed, or just use incident types
}

# --- Helper Functions ---
def _load_csv_to_df(filepath, date_cols=None):
    """Loads a CSV file into a pandas DataFrame."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        df = pd.read_csv(filepath)
        if date_cols:
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    return pd.DataFrame()

def map_players(fpl_df, whoscored_players_df, threshold=85):
    """
    Maps FPL players to WhoScored players using fuzzy string matching on names.
    """
    mapped_ids = {}
    fpl_df['fpl_full_name_lower'] = fpl_df['full_name'].str.lower().str.strip()
    whoscored_players_df['whoscored_full_name_lower'] = whoscored_players_df['nombre_jugador'].str.lower().str.strip()
    whoscored_names = whoscored_players_df[['whoscored_full_name_lower', 'jugador_id']].drop_duplicates().set_index('whoscored_full_name_lower')

    print("Iniciando mapeo de jugadores FPL a WhoScored...")
    for index, fpl_player in fpl_df.iterrows():
        fpl_name = fpl_player['fpl_full_name_lower']
        match_result = process.extractOne(fpl_name, whoscored_names.index, scorer=fuzz.token_sort_ratio)

        if match_result and match_result[1] >= threshold:
            whoscored_name_match = match_result[0]
            jugador_id = whoscored_names.loc[whoscored_name_match, 'jugador_id']
            if isinstance(jugador_id, pd.Series):
                jugador_id = jugador_id.iloc[0]
            mapped_ids[fpl_player['id']] = jugador_id

    fpl_df['whoscored_jugador_id'] = fpl_df['id'].map(mapped_ids)
    print(f"Mapeo completado. {fpl_df['whoscored_jugador_id'].count()} de {len(fpl_df)} jugadores mapeados.")
    return fpl_df

def calculate_volatility(incidents_df):
    """
    Calculates the standard deviation of 'match scores' for each player based on incidents.
    """
    print("Calculando volatilidad de jugadores basada en incidentes históricos...")
    
    # Filter only relevant incident types
    relevant_types = [k for k in WEIGHTS.keys() if k != 'xP']
    df = incidents_df[incidents_df['tipo'].isin(relevant_types)].copy()
    
    # Calculate score contribution for each incident
    df['incident_score'] = df['tipo'].map(WEIGHTS)
    
    # Group by player and match to get match scores
    match_scores = df.groupby(['jugador_id', 'partido_id'])['incident_score'].sum().reset_index()
    
    # Calculate standard deviation per player
    volatility = match_scores.groupby('jugador_id')['incident_score'].std().reset_index()
    volatility.rename(columns={'incident_score': 'volatility'}, inplace=True)
    
    # Fill NaN volatility (players with 1 or 0 matches) with a default or 0
    volatility['volatility'] = volatility['volatility'].fillna(0)
    
    return volatility

def calculate_performance_metrics(unified_df, incidents_df):
    """
    Calculates advanced performance metrics from incident data and merges into unified_df.
    """
    print("Calculando métricas de rendimiento a partir de incidentes...")
    incidents_df['minuto'] = pd.to_numeric(incidents_df['minuto'], errors='coerce')

    # Mapping incident types to our metric names
    metrics_map = {
        'Goal': 'total_goles',
        'PenaltyGoal': 'total_goles', # Treat penalty goals as goals for count
        'Assist': 'total_asistencias',
        'ShotOnTarget': 'total_tiros_a_puerta',
        'KeyPass': 'total_pases_clave',
        'YellowCard': 'total_tarjetas_amarillas',
        'RedCard': 'total_tarjetas_rojas'
    }
    
    # Prepare aggregation dict
    agg_dict = {v: ('tipo', lambda x, t=k: x.isin([t] if isinstance(t, str) else t).sum()) 
                for k, v in metrics_map.items() if k not in ['Goal', 'PenaltyGoal']} # Handle simple ones
    
    # Handle Goals specifically to include both types
    agg_dict['total_goles'] = ('tipo', lambda x: x.isin(['Goal', 'PenaltyGoal']).sum())
    agg_dict['partidos_jugados'] = ('partido_id', 'nunique')

    player_stats = incidents_df.groupby('jugador_id').agg(**agg_dict).reset_index()

    # Calculate per-match averages
    metric_cols = ['total_goles', 'total_asistencias', 'total_tiros_a_puerta', 'total_pases_clave', 'total_tarjetas_amarillas', 'total_tarjetas_rojas']
    for col in metric_cols:
        player_stats[f'avg_{col}'] = player_stats[col] / player_stats['partidos_jugados']
        player_stats[f'avg_{col}'] = player_stats[f'avg_{col}'].fillna(0)

    unified_df = unified_df.merge(player_stats, left_on='whoscored_jugador_id', right_on='jugador_id', how='left')
    unified_df = unified_df.drop(columns=['jugador_id_y'], errors='ignore')
    unified_df = unified_df.rename(columns={'jugador_id_x': 'jugador_id'})
    
    cols_to_fill = metric_cols + ['partidos_jugados'] + [f'avg_{c}' for c in metric_cols]
    unified_df[cols_to_fill] = unified_df[cols_to_fill].fillna(0)
    
    return unified_df

def engineer_performance_score(unified_df):
    """
    Engineers a composite performance score.
    """
    print("Ingeniería del Puntaje de Rendimiento (Performance Score)...")

    # Initialize Score with xP
    unified_df['performance_score'] = unified_df['xP'] * WEIGHTS['xP']

    # Add weighted incident-based metrics (using averages)
    # Note: WEIGHTS keys match incident types, but we have avg_total_... columns.
    # We need to map them.
    
    metric_to_weight_map = {
        'avg_total_goles': WEIGHTS['Goal'],
        'avg_total_asistencias': WEIGHTS['Assist'],
        'avg_total_tiros_a_puerta': WEIGHTS['ShotOnTarget'],
        'avg_total_pases_clave': WEIGHTS['KeyPass'],
        'avg_total_tarjetas_amarillas': WEIGHTS['YellowCard'],
        'avg_total_tarjetas_rojas': WEIGHTS['RedCard']
    }

    for metric, weight in metric_to_weight_map.items():
        if metric in unified_df.columns:
            unified_df['performance_score'] += unified_df[metric] * weight
            
    unified_df['performance_score'] = unified_df['performance_score'].fillna(0)
    return unified_df

def solve_optimization_problem(available_players, score_col='performance_score'):
    """
    Solves the FPL Team Selection problem using PuLP.
    Returns a list of selected player indices (from available_players).
    """
    # Ensure score column has no NaNs or Infs
    available_players[score_col] = available_players[score_col].fillna(0).replace([np.inf, -np.inf], 0)

    # Map positions
    pos_map = {'Goalkeeper': 'GK', 'Defender': 'DEF', 'Midfielder': 'MID', 'Forward': 'FWD'}
    available_players['Posicion_short'] = available_players['Posicion'].map(pos_map)
    available_players['Precio_int'] = (available_players['Precio']).astype(int)

    prob = pulp.LpProblem("FPL_Selection", pulp.LpMaximize)
    player_vars = pulp.LpVariable.dicts("p", available_players.index, 0, 1, pulp.LpBinary)

    # Objective
    prob += pulp.lpSum(available_players.loc[i, score_col] * player_vars[i] for i in available_players.index)

    # Constraints
    prob += pulp.lpSum(player_vars[i] for i in available_players.index) == SQUAD_SIZE
    prob += pulp.lpSum(available_players.loc[i, 'Precio_int'] * player_vars[i] for i in available_players.index) <= FPL_BUDGET
    prob += pulp.lpSum(player_vars[i] for i in available_players.index if available_players.loc[i, 'Posicion_short'] == 'GK') == GK_COUNT
    prob += pulp.lpSum(player_vars[i] for i in available_players.index if available_players.loc[i, 'Posicion_short'] == 'DEF') == DEF_COUNT
    prob += pulp.lpSum(player_vars[i] for i in available_players.index if available_players.loc[i, 'Posicion_short'] == 'MID') == MID_COUNT
    prob += pulp.lpSum(player_vars[i] for i in available_players.index if available_players.loc[i, 'Posicion_short'] == 'FWD') == FWD_COUNT

    for team_id in available_players['team_id'].unique():
        prob += pulp.lpSum(player_vars[i] for i in available_players.index if available_players.loc[i, 'team_id'] == team_id) <= MAX_PLAYERS_PER_TEAM

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    if prob.status == pulp.LpStatusOptimal:
        return [i for i in available_players.index if player_vars[i].varValue == 1]
    else:
        return []

def run_monte_carlo_simulation(unified_df, n_simulations=100):
    """
    Runs Monte Carlo simulations to find the most robust team.
    """
    print(f"\n--- Iniciando Simulación de Monte Carlo ({n_simulations} iteraciones) ---")
    
    # Ensure volatility is present
    if 'volatility' not in unified_df.columns:
        unified_df['volatility'] = 0
    
    # Replace 0 volatility with a small epsilon to allow some variation (or keep 0 for stable players)
    # Let's use a small baseline volatility for everyone to account for general uncertainty
    min_vol = unified_df[unified_df['volatility'] > 0]['volatility'].min()
    if pd.isna(min_vol): min_vol = 0.5
    unified_df['volatility'] = unified_df['volatility'].replace(0, min_vol * 0.5)

    selection_counts = Counter()
    
    for i in range(n_simulations):
        sim_df = unified_df.copy()
        
        # Perturb scores based on volatility
        # New Score = Base Score + Noise(0, Volatility)
        noise = np.random.normal(0, sim_df['volatility'], size=len(sim_df))
        sim_df['simulated_score'] = sim_df['performance_score'] + noise
        
        # Solve for this simulation
        selected_indices = solve_optimization_problem(sim_df, score_col='simulated_score')
        
        # Track selections (using Player ID to be safe)
        selected_ids = sim_df.loc[selected_indices, 'id'].tolist()
        selection_counts.update(selected_ids)
        
        sys.stdout.write(f"\rSimulación {i+1}/{n_simulations} completada.")
        sys.stdout.flush()
        
    print("\nSimulaciones completadas.")
    
    # Add selection frequency to original dataframe
    unified_df['selection_frequency'] = unified_df['id'].map(selection_counts).fillna(0)
    unified_df['selection_prob'] = unified_df['selection_frequency'] / n_simulations
    
    print("Optimizando equipo final basado en Robustez (Frecuencia de Selección)...")
    # Final optimization using Selection Frequency as the score
    # This ensures we pick the most "popular" players across simulations while respecting constraints
    final_indices = solve_optimization_problem(unified_df, score_col='selection_frequency')
    
    if not final_indices:
        print("Error: No se pudo encontrar un equipo final válido.")
        return
        
    selected_team_df = unified_df.loc[final_indices].copy()
    
    # Sort and Display
    selected_team_df['Posicion_order'] = selected_team_df['Posicion'].map({'Goalkeeper': 0, 'Defender': 1, 'Midfielder': 2, 'Forward': 3})
    selected_team_df = selected_team_df.sort_values(by=['Posicion_order', 'selection_frequency'], ascending=[True, False])
    
    print("\n--- EQUIPO RECOMENDADO (ROBUSTO - MONTE CARLO) ---")
    print(selected_team_df[['full_name', 'Posicion', 'team_name', 'Precio', 'performance_score', 'volatility', 'selection_prob']])
    
    total_cost = selected_team_df['Precio'].astype(int).sum()
    total_score = selected_team_df['performance_score'].sum()
    avg_prob = selected_team_df['selection_prob'].mean()
    
    print(f"\n--- Estadísticas del Equipo ---")
    print(f"Costo Total: £{total_cost / 10.0:.1f}m")
    print(f"Score Promedio: {total_score:.2f}")
    print(f"Robustez Promedio (Prob. Selección): {avg_prob:.1%}")
    
    # Suggest Lineup
    suggest_lineup(selected_team_df)

def suggest_lineup(selected_team_df):
    print("\n--- Sugerencia de Alineación (Basado en Score Base) ---")
    # Map positions for easier filtering
    pos_map = {'Goalkeeper': 'GK', 'Defender': 'DEF', 'Midfielder': 'MID', 'Forward': 'FWD'}
    selected_team_df['Posicion_short'] = selected_team_df['Posicion'].map(pos_map)

    gk_starters = selected_team_df[selected_team_df['Posicion_short'] == 'GK'].nlargest(1, 'performance_score')
    def_starters = selected_team_df[selected_team_df['Posicion_short'] == 'DEF'].nlargest(3, 'performance_score') # Min 3 DEFs
    mid_starters = selected_team_df[selected_team_df['Posicion_short'] == 'MID'].nlargest(2, 'performance_score') # Min 2 MIDs
    fwd_starters = selected_team_df[selected_team_df['Posicion_short'] == 'FWD'].nlargest(1, 'performance_score') # Min 1 FWD
    
    # Fill remaining spots (4 spots left for 11 total)
    current_starters = pd.concat([gk_starters, def_starters, mid_starters, fwd_starters])
    remaining_pool = selected_team_df[~selected_team_df.index.isin(current_starters.index)]
    
    # Pick best 4 from remaining, regardless of position (valid formation rules usually allow this flexibility)
    # Actually, FPL rules are specific, but usually 3-4-3, 3-5-2, 4-4-2, 4-3-3 etc are valid.
    # Simplification: Just pick top 4 scorers from remaining.
    flex_starters = remaining_pool.nlargest(4, 'performance_score')
    starting_xi = pd.concat([current_starters, flex_starters])
    
    bench_players = selected_team_df[~selected_team_df.index.isin(starting_xi.index)].sort_values('performance_score', ascending=False)
    
    captain = starting_xi.nlargest(1, 'performance_score').iloc[0]
    vice_captain = starting_xi[starting_xi.index != captain.name].nlargest(1, 'performance_score').iloc[0]

    print(f"Capitán (C): {captain['full_name']}")
    print(f"Vice-Capitán (VC): {vice_captain['full_name']}")
    
    print("\n--- Titulares ---")
    for _, player in starting_xi.sort_values('Posicion_order').iterrows():
        print(f"{player['Posicion'][:3].upper()} | {player['full_name']} (Score: {player['performance_score']:.1f}, Vol: {player['volatility']:.1f})")
        
    print("\n--- Suplentes ---")
    for _, player in bench_players.iterrows():
        print(f"{player['Posicion'][:3].upper()} | {player['full_name']} (Score: {player['performance_score']:.1f})")

def main():
    print("--- Iniciando el Recomendador de Equipo FPL (con Monte Carlo) ---")

    # --- 1. Load Data ---
    print("Cargando datos...")
    fpl_players_df = _load_csv_to_df('data/processed/resultados_fase3.csv')
    whoscored_players_df = _load_csv_to_df('data/raw/jugadores.csv')
    whoscored_incidents_df = _load_csv_to_df('data/raw/incidentes.csv')
    
    if fpl_players_df.empty or whoscored_players_df.empty or whoscored_incidents_df.empty:
        print("Error: Faltan archivos de datos.")
        return

    fpl_players_df = fpl_players_df[fpl_players_df['status'] == 'a'].copy()

    # --- 2. Player Mapping ---
    unified_df = map_players(fpl_players_df, whoscored_players_df)
    unified_df = unified_df.dropna(subset=['whoscored_jugador_id'])
    unified_df['whoscored_jugador_id'] = unified_df['whoscored_jugador_id'].astype(int)

    # --- 3. Calculate Volatility ---
    volatility_df = calculate_volatility(whoscored_incidents_df)
    unified_df = unified_df.merge(volatility_df, left_on='whoscored_jugador_id', right_on='jugador_id', how='left')

    # --- 4. Calculate Performance Metrics & Score ---
    unified_df = calculate_performance_metrics(unified_df, whoscored_incidents_df)
    unified_df = engineer_performance_score(unified_df)

    # --- 5. Run Monte Carlo & Optimize ---
    run_monte_carlo_simulation(unified_df, n_simulations=N_SIMULATIONS)

    print("\n--- Proceso Finalizado ---")

if __name__ == "__main__":
    main()
