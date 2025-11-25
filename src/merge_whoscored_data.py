
import json
import pandas as pd
from sqlalchemy import create_engine
from fuzzywuzzy import process

TEAM_NAME_MAPPING = {
    'Man City': 'Manchester City',
    'Man Utd': 'Manchester United',
    'Nott\'m Forest': 'Nottingham Forest',
    'Spurs': 'Tottenham',
}

def merge_data():
    """
    Merges the FPL data from the database with the WhoScored data.
    """
    # --- 1. Load FPL data from database ---
    db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
    try:
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={'sslmode': 'require'})
        with engine.connect() as conn:
            fpl_players_df = pd.read_sql("SELECT * FROM players", conn)
            fpl_teams_df = pd.read_sql("SELECT * FROM teams", conn)
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return

    # --- 2. Load WhoScored data ---
    try:
        with open('consolidated_whoscored_data.json', 'r', encoding='utf-8') as f:
            whoscored_data = json.load(f)
    except FileNotFoundError:
        print("Error: consolidated_whoscored_data.json not found.")
        return
    whoscored_df = pd.DataFrame(whoscored_data)

    # --- 3. Match Teams ---
    fpl_teams_df['whoscored_name'] = fpl_teams_df['name'].replace(TEAM_NAME_MAPPING)

    # --- 4. Match Players ---
    fpl_players_df['full_name'] = fpl_players_df['Nombre'] + ' ' + fpl_players_df['Apellido']
    whoscored_players = set()
    for incidents in whoscored_df['incidents']:
        for incident in incidents:
            whoscored_players.add(incident['playerName'])

    player_mapping = {}
    for fpl_player_name in fpl_players_df['full_name']:
        match = process.extractOne(fpl_player_name, list(whoscored_players))
        if match and match[1] > 80: # Using a threshold of 80 for matching
            player_mapping[fpl_player_name] = match[0]

    fpl_players_df['whoscored_name'] = fpl_players_df['full_name'].map(player_mapping)

    # --- 5. Augment Player Data ---
    whoscored_stats = []
    for index, row in whoscored_df.iterrows():
        for incident in row['incidents']:
            player_name = incident['playerName']
            if player_name in player_mapping.values():
                fpl_name = [k for k, v in player_mapping.items() if v == player_name][0]
                fpl_player_id = fpl_players_df[fpl_players_df['full_name'] == fpl_name]['id'].iloc[0]
                whoscored_stats.append({
                    'player_id': fpl_player_id,
                    'game_id': row['game_id'],
                    'type': incident['type'],
                    'subType': incident.get('subType'),
                })

    whoscored_stats_df = pd.DataFrame(whoscored_stats)

    # --- 6. Save augmented data ---
    # For now, let's just save the player mapping and whoscored stats to csv to check them
    fpl_players_df[['id', 'full_name', 'whoscored_name']].to_csv('data/player_mapping.csv', index=False)
    whoscored_stats_df.to_csv('data/whoscored_stats.csv', index=False)

    print("Player mapping and WhoScored stats saved to CSV files.")

if __name__ == "__main__":
    merge_data()
