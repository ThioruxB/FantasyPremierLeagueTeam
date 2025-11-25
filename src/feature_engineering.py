import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import sys
import codecs
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpBinary
from collections import Counter

# --- 1. Cargar datos y Conexión a BD ---
def get_data():
    # Cargar el CSV principal
    try:
        main_df = pd.read_csv('data/processed/enriched_players.csv')
        if 'difficulty' not in main_df.columns:
            print("Advertencia: 'difficulty' no encontrada en data/processed/enriched_players.csv. Inicializando a 0.")
            main_df['difficulty'] = 0
        # print("Archivo 'resultados.csv' cargado exitosamente.")
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'data/processed/enriched_players.csv'. Ejecuta fpl_pipeline.py primero.")
        return None, None

    # Conectar a la base de datos para obtener el historial
    db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
    try:
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={'sslmode': 'require'})
        with engine.connect() as conn:
            # Necesitamos el mapeo de Nombre/Apellido a id
            players_df = pd.read_sql("SELECT id, \"Nombre\", \"Apellido\" FROM players", conn)
            history_df = pd.read_sql("SELECT element as id, total_points FROM player_history", conn)
        # print("Datos históricos cargados desde la base de datos.")
        
        # Unir nombres al historial
        history_df = history_df.merge(players_df, on='id')
        return main_df, history_df

    except Exception as e:
        print(f"Error al conectar o consultar la base de datos: {e}")
        return main_df, None

# --- 2. Ingeniería de Features: Volatilidad ---
def calculate_volatility(main_df, history_df):
    if history_df is None:
        main_df['volatilidad'] = 0
        main_df['rendimiento_ajustado'] = main_df['valor']
        return main_df

    volatility = history_df.groupby('id')['total_points'].rolling(10, min_periods=1).std().reset_index()
    volatility = volatility.groupby('id')['total_points'].last().reset_index()
    volatility.rename(columns={'total_points': 'volatilidad'}, inplace=True)
    volatility['volatilidad'] = volatility['volatilidad'].fillna(0)

    merged_df = main_df.merge(volatility, on='id', how='left')
    merged_df['volatilidad'] = merged_df['volatilidad'].fillna(0)

    min_volatility = merged_df[merged_df['volatilidad'] > 0]['volatilidad'].min()
    merged_df['volatilidad'] = merged_df['volatilidad'].replace(0, min_volatility)

    merged_df['rendimiento_ajustado'] = (merged_df['combined_form'] / merged_df['volatilidad']).fillna(0)

    # ... (código existente) ...

    # Justo antes del return
    if 'chance_of_playing_next_round' not in merged_df.columns and 'chance_of_playing_next_round' in main_df.columns:
        merged_df = merged_df.merge(main_df[['id', 'chance_of_playing_next_round']], on='id', how='left')

    return merged_df

# --- 4. Selección de Equipo Óptimo con ILP ---
def select_optimal_team(df, budget=1000, formation={'Goalkeeper': 2, 'Defender': 5, 'Midfielder': 5, 'Forward': 3}):
    
    players = df.to_dict('records')
    prob = LpProblem("FantasyTeamSelection", LpMaximize)
    player_vars = LpVariable.dicts("Player", [(p['Nombre'], p['Apellido']) for p in players], cat=LpBinary)
    
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] * p['rendimiento_ajustado'] for p in players]), "TotalRendimientoAjustado"
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] * p['Precio'] for p in players]) <= budget, "TotalCost"
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players]) == sum(formation.values()), "TotalPlayers"
    
    for pos, count in formation.items():
        prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players if p['Posicion'] == pos]) == count, f"Num{pos}"
        
    team_names = df['team_name'].unique()
    for team in team_names:
        prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players if p['team_name'] == team]) <= 3, f"Max3PerTeam_{team.replace(' ','_')}"
        
    prob.solve()
    
    selected_players = []
    for p in players:
        if player_vars[(p['Nombre'], p['Apellido'])].varValue == 1:
            selected_players.append(p)
            
    return selected_players

# --- 5. Robustificación con Monte Carlo ---
def run_monte_carlo_simulation(df, n_simulations=100):
    print(f"\n--- Iniciando Simulación de Monte Carlo con {n_simulations} iteraciones ---")
    all_selected_players = []
    
    for i in range(n_simulations):
        sim_df = df.copy()
        
        sim_df['simulated_form'] = np.random.normal(sim_df['form'], sim_df['volatilidad'])
        sim_df['simulated_form'] = sim_df['simulated_form'].clip(lower=0)
        
        sim_df['valor'] = sim_df['simulated_form'] / (sim_df['Precio'] / 10.0)
        sim_df['rendimiento_ajustado'] = sim_df['valor'] / sim_df['volatilidad']

        sim_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        sim_df['rendimiento_ajustado'].fillna(0, inplace=True)
        
        selected_players = select_optimal_team(sim_df)
        all_selected_players.extend([(p['Nombre'], p['Apellido']) for p in selected_players])
        
        sys.stdout.write(f"\rSimulación {i+1}/{n_simulations} completada.")
        sys.stdout.flush()

    # print("\n\n--- Equipo Robusto (Jugadores más frecuentes en la selección) ---")
    player_counts = Counter(all_selected_players)
    robust_team = player_counts.most_common(15)
    
    robust_df = pd.DataFrame(robust_team, columns=['Jugador', 'Selecciones'])
    robust_df['Nombre'] = robust_df['Jugador'].apply(lambda x: x[0])
    robust_df['Apellido'] = robust_df['Jugador'].apply(lambda x: x[1])
    robust_df['Frecuencia'] = (robust_df['Selecciones'] / n_simulations) * 100
    
    player_info = df.drop_duplicates(subset=['Nombre', 'Apellido'])[['Nombre', 'Apellido', 'Posicion', 'team_name', 'Precio']]
    robust_df = robust_df.merge(player_info, on=['Nombre', 'Apellido'])
    
    # print(robust_df[['Nombre', 'Apellido', 'Posicion', 'team_name', 'Precio', 'Selecciones', 'Frecuencia']].sort_values('Selecciones', ascending=False).to_string())
    return robust_df

if __name__ == '__main__':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    main_df, history_df = get_data()

    if main_df is not None:
        final_df = calculate_volatility(main_df, history_df)

        # print("\n--- Dataframe Final con Volatilidad y Rendimiento Ajustado (Top 15) ---")
        # try:
        #     print(final_df.sort_values('rendimiento_ajustado', ascending=False).head(15).to_string())
        # except UnicodeEncodeError:
        #     print("No se pudo mostrar el dataframe en la consola por problemas de codificación, pero los datos se guardaron en el archivo CSV.")

        final_df.to_csv('data/processed/resultados_fase2.csv', index=False, encoding='utf-8-sig')

        # --- Ejecutar Optimización --- #
        # 1. Selección Óptima Simple
        # print("\n--- Selección Óptima Simple (única ejecución) ---")
        optimal_team = select_optimal_team(final_df)
        if optimal_team:
            optimal_df = pd.DataFrame(optimal_team).sort_values(by='Posicion')
            total_cost = optimal_df['Precio'].sum()
            total_rendimiento = optimal_df['rendimiento_ajustado'].sum()
            # print(optimal_df[['Nombre', 'Apellido', 'Posicion', 'team_name', 'Precio', 'rendimiento_ajustado']].to_string())
            # print("\n--- Estadísticas del Equipo Óptimo ---")
            # print(f"Costo Total: {total_cost:.1f} / 1000")
            # print(f"Rendimiento Ajustado Total: {total_rendimiento:.2f}")

        # 2. Robustificación con Monte Carlo
        run_monte_carlo_simulation(final_df, n_simulations=100)