
import pandas as pd
from sqlalchemy import create_engine
from fuzzywuzzy import process
import os

TEAM_NAME_MAPPING = {
    'Man City': 'Manchester City',
    'Man Utd': 'Manchester United',
    'Nott\'m Forest': 'Nottingham Forest',
    'Spurs': 'Tottenham',
}

def enrich_data():
    """
    Enriches the FPL data with historical stats from the user-provided CSVs.
    """
    # --- 1. Load FPL data from database ---
    try:
        fpl_players_df = pd.read_csv('data/processed/filtered_players.csv')
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'data/processed/filtered_players.csv'. Ejecuta data_pipeline.py primero.")
        return

    db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
    try:
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={'sslmode': 'require'})
        with engine.connect() as conn:
            fpl_teams_df = pd.read_sql("SELECT * FROM teams", conn)
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return

    # --- 2. Load user CSVs ---
    try:
        jugadores_df = pd.read_csv('data/raw/jugadores.csv')
        incidentes_df = pd.read_csv('data/raw/incidentes.csv')
    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo {e.filename}.")
        return

    db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
    engine = create_engine(db_url, pool_pre_ping=True, connect_args={'sslmode': 'require'})
    try:
        with engine.connect() as conn:
            db_data = {name: pd.read_sql(f"SELECT * FROM {name}", conn) for name in ["players", "teams", "gameweeks", "player_history", "fixtures"]}
    except Exception as e:
        print(f"An error occurred while loading data: {e}")
        db_data = None

    # --- 3. Calculate FPL form ---
    if 'form' not in fpl_players_df.columns:
        fpl_players_df['form'] = 0

    # --- 4. Match Players ---
    fpl_players_df['full_name'] = fpl_players_df['Nombre'] + ' ' + fpl_players_df['Apellido']
    csv_player_names = list(jugadores_df['nombre_jugador'].unique())

    player_mapping = {}
    for fpl_player_name in fpl_players_df['full_name']:
        match = process.extractOne(fpl_player_name, csv_player_names)
        if match and match[1] > 85: # Use a threshold of 85 for matching
            player_mapping[fpl_player_name] = match[0]
    
    # Create a mapping DataFrame
    player_map_df = pd.DataFrame(player_mapping.items(), columns=['fpl_name', 'csv_name'])
    player_map_df = player_map_df.merge(fpl_players_df[['id', 'full_name']], left_on='fpl_name', right_on='full_name').drop(columns=['full_name'])
    player_map_df = player_map_df.merge(jugadores_df, left_on='csv_name', right_on='nombre_jugador').drop(columns=['nombre_jugador'])
    player_map_df.rename(columns={'id': 'fpl_id', 'jugador_id': 'csv_id'}, inplace=True)

    # --- 5. Calculate historical stats from CSVs ---
    def calculate_points(row):
        if row['tipo'] == 1 and row['subtipo'] == 1: # Goal
            return 5
        elif row['tipo'] == 2: # Card
            return -1
        else:
            return 0
    incidentes_df['points'] = incidentes_df.apply(calculate_points, axis=1)
    
    # We need to map csv player ids to fpl player ids in the incidents table
    incidentes_df = incidentes_df.merge(player_map_df[['csv_id', 'fpl_id']], left_on='jugador_id', right_on='csv_id', how='inner')

    # Calculate form (average points in last 5 games from CSVs)
    csv_history = incidentes_df.sort_values(by=['fpl_id', 'partido_id'])
    csv_form = csv_history.groupby('fpl_id')['points'].apply(lambda x: x.rolling(5, min_periods=1).mean()).reset_index()
    csv_form.rename(columns={'points': 'csv_form'}, inplace=True)
    csv_form = csv_form.groupby('fpl_id')['csv_form'].last().reset_index()

    # --- 6. Enrich FPL Data ---
    enriched_players_df = fpl_players_df.merge(csv_form, left_on='id', right_on='fpl_id', how='left')
    if 'chance_of_playing_next_round' in fpl_players_df.columns:
        enriched_players_df['chance_of_playing_next_round'] = fpl_players_df['chance_of_playing_next_round']
    enriched_players_df['csv_form'] = enriched_players_df['csv_form'].fillna(0)
    
    # We can decide to use the csv_form to override the fpl form, or combine them.
    # For now, let's create a new column 'combined_form'
    enriched_players_df['form'] = enriched_players_df['form'].fillna(0)
    enriched_players_df['combined_form'] = (enriched_players_df['form'] + enriched_players_df['csv_form']) / 2

    # --- 7. Save Enriched Data ---
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # The next script expects 'resultados.csv', let's create a compatible file.
    # We need to get opponent and difficulty from the FPL data.
    enriched_players_df = enriched_players_df.merge(fpl_players_df[['id', 'opponent', 'is_home', 'difficulty']], on='id', how='left')

    # Add team name
    team_map = fpl_teams_df.set_index('id')['name'].to_dict()
    enriched_players_df['team_name'] = enriched_players_df['team_id'].map(team_map)


    enriched_players_df['valor'] = (enriched_players_df['combined_form'] / (enriched_players_df['Precio'] / 10.0)).fillna(0)
    player_map_df.to_csv('data/processed/player_mapping.csv', index=False)
    enriched_players_df.to_csv('data/processed/enriched_players.csv', index=False)
    print("Enriched player data saved to data/processed/enriched_players.csv")


if __name__ == "__main__":
    enrich_data()
