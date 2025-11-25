import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpBinary
import sys
import codecs

# --- 1. Cargar Datos ---
def get_data():
    print("--- Cargando datos de fases anteriores ---")
    try:
        current_df = pd.read_csv('data/processed/resultados_fase2.csv')
        print("Archivo 'data/processed/resultados_fase2.csv' cargado exitosamente.")
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'data/processed/resultados_fase2.csv'. Ejecuta feature_engineering.py primero.")
        return None, None

    db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
    try:
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={'sslmode': 'require'})
        with engine.connect() as conn:
            history_df = pd.read_sql("SELECT * FROM player_history", conn)
            players_df = pd.read_sql("SELECT id, \"Posicion\" FROM players", conn)
            teams_df = pd.read_sql("SELECT * FROM teams", conn)
        print("Datos históricos para entrenamiento cargados desde la base de datos.")

        history_df = history_df.merge(players_df, left_on='element', right_on='id', how='left')
        
        # --- Feature Engineering for Historical Data ---
        history_df = history_df.sort_values(by=['element', 'round'])
        
        # Form
        history_df['form'] = history_df.groupby('element')['total_points'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())

        # Difficulty
        strength_mapping_home = teams_df.set_index('id')['strength_overall_home'].to_dict()
        strength_mapping_away = teams_df.set_index('id')['strength_overall_away'].to_dict()

        home_difficulty = history_df[history_df['was_home']]['opponent_team'].map(strength_mapping_away)
        away_difficulty = history_df[~history_df['was_home']]['opponent_team'].map(strength_mapping_home)
        
        history_df['difficulty'] = home_difficulty.combine_first(away_difficulty)

        # Add combined_form to historical data
        try:
            incidentes_df = pd.read_csv('data/raw/incidentes.csv')
            jugadores_df = pd.read_csv('data/raw/jugadores.csv')
            player_map_df = pd.read_csv('data/processed/player_mapping.csv')

            def calculate_points(row):
                if row['tipo'] == 1 and row['subtipo'] == 1: return 5
                elif row['tipo'] == 2: return -1
                else: return 0
            incidentes_df['points'] = incidentes_df.apply(calculate_points, axis=1)
            incidentes_df = incidentes_df.merge(player_map_df[['csv_id', 'fpl_id']], left_on='jugador_id', right_on='csv_id', how='inner')
            csv_history = incidentes_df.sort_values(by=['fpl_id', 'partido_id'])
            csv_form = csv_history.groupby('fpl_id')['points'].apply(lambda x: x.rolling(5, min_periods=1).mean()).reset_index()
            csv_form.rename(columns={'points': 'csv_form'}, inplace=True)
            csv_form = csv_form.groupby('fpl_id')['csv_form'].last().reset_index()

            history_df = history_df.merge(csv_form, left_on='element', right_on='fpl_id', how='left')
            history_df['csv_form'] = history_df['csv_form'].fillna(0)
            history_df['form'] = history_df['form'].fillna(0)
            history_df['combined_form'] = (history_df['form'] + history_df['csv_form']) / 2
        except FileNotFoundError:
            print("Could not calculate combined_form for historical data. Using FPL form only.")
            history_df['combined_form'] = history_df['form']


        history_df.dropna(subset=['form', 'difficulty', 'total_points'], inplace=True)

        return current_df, history_df

    except Exception as e:
        print(f"Error al procesar los datos históricos: {e}")
        return current_df, None

# --- 2. Modelo Predictivo de Puntos Esperados (xP) ---
def train_and_predict_xp(current_df, history_df):
    if history_df is None or history_df.empty:
        print("No hay datos históricos para entrenar el modelo. No se pueden predecir los xP.")
        current_df['xP'] = 0
        return current_df

    print("--- Entrenando modelo de Gradient Boosting para predecir Puntos Esperados (xP) ---")
    
    features = ['combined_form', 'difficulty', 'Posicion']
    target = 'total_points'

    X = history_df[features]
    y = history_df[target]

    preprocessor = ColumnTransformer(
        transformers=[
            ('pos', OneHotEncoder(handle_unknown='ignore'), ['Posicion'])
        ], 
        remainder='passthrough'
    )

    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', GradientBoostingRegressor(n_estimators=100, random_state=42))
    ])

    model_pipeline.fit(X, y)

    print("--- Prediciendo xP para la próxima jornada ---")
    current_features = current_df[features].copy()

    # Impute NaN values before prediction
    current_features['combined_form'].fillna(0, inplace=True)
    median_difficulty = current_features['difficulty'].median()
    current_features['difficulty'].fillna(median_difficulty, inplace=True)

    predictions = model_pipeline.predict(current_features)
    current_df['xP'] = predictions.round(2)

    # Ajustar xP por la probabilidad de jugar
    current_df['chance_of_playing_next_round'] = current_df['chance_of_playing_next_round'].fillna(100)
    current_df['xP'] = current_df['xP'] * (current_df['chance_of_playing_next_round'] / 100)

    return current_df

# --- 3. Selección de Equipo Ideal con ILP ---
def select_ideal_team(df, budget=1000, objective_col='xP', formation={'Goalkeeper': 2, 'Defender': 5, 'Midfielder': 5, 'Forward': 3}):
    print(f"\n--- Iniciando Selección de Equipo Ideal maximizando '{objective_col}' ---")
    
    players = df.to_dict('records')
    prob = LpProblem("IdealTeamSelection", LpMaximize)
    player_vars = LpVariable.dicts("Player", [(p['Nombre'], p['Apellido']) for p in players], cat=LpBinary)
    
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] * p[objective_col] for p in players]), f"Total_{objective_col}"
    
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] * p['Precio'] for p in players]) <= budget, "TotalCost"
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players]) == sum(formation.values()), "TotalPlayers"
    
    for pos, count in formation.items():
        prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players if p['Posicion'] == pos]) == count, f"Num{pos}"
        
    team_names = df['team_name'].unique()
    for team in team_names:
        prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players if p['team_name'] == team]) <= 3, f"Max3PerTeam_{team.replace(' ','_')}"
        
    prob.solve()
    
    print("\n--- Equipo Ideal Seleccionado ---")
    selected_players = []
    for p in players:
        if player_vars[(p['Nombre'], p['Apellido'])].varValue == 1:
            selected_players.append(p)
            
    if selected_players:
        selected_df = pd.DataFrame(selected_players).sort_values(by='Posicion')
        total_cost = selected_df['Precio'].sum()
        total_objective = selected_df[objective_col].sum()
        
        print(selected_df[['Nombre', 'Apellido', 'Posicion', 'team_name', 'Precio', objective_col]].to_string())
        print("\n--- Estadísticas del Equipo Ideal ---")
        print(f"Costo Total: {total_cost:.1f} / {budget}")
        print(f"{objective_col} Total: {total_objective:.2f}")
    else:
        print("No se pudo encontrar una solución óptima.")

if __name__ == '__main__':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    current_data, historical_data = get_data()

    if current_data is not None:
        data_with_xp = train_and_predict_xp(current_data, historical_data)
        
        print("\n--- Top 15 Jugadores por Puntos Esperados (xP) ---")
        print(data_with_xp.sort_values('xP', ascending=False).head(15)[['Nombre', 'Apellido', 'team_name', 'Posicion', 'form', 'difficulty', 'xP']].to_string())

        data_with_xp.to_csv('data/processed/resultados_fase3.csv', index=False, encoding='utf-8-sig')
        print("\nResultados de la Fase 3 guardados en 'data/processed/resultados_fase3.csv'")

        if 'xP' in data_with_xp.columns and data_with_xp['xP'].sum() > 0:
            select_ideal_team(data_with_xp, objective_col='xP')
        else:
            print("\nNo se ejecutó la selección de equipo ideal porque no se pudieron predecir los puntos (xP).")
