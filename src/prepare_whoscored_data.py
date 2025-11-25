
import json
import pandas as pd
import numpy as np
from datetime import datetime

def prepare_whoscored_data():
    """
    Reads the consolidated whoscored data, transforms it into the required
    DataFrames, and saves them as CSV files.
    """
    try:
        with open('consolidated_whoscored_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: consolidated_whoscored_data.json not found. Run consolidate_whoscored_data.py first.")
        return

    matches_df = pd.DataFrame(data)

    # --- 1. Create teams_df ---
    home_teams = matches_df[['home_team_id', 'home_team']].rename(columns={'home_team_id': 'id', 'home_team': 'name'})
    away_teams = matches_df[['away_team_id', 'away_team']].rename(columns={'away_team_id': 'id', 'away_team': 'name'})
    teams_df = pd.concat([home_teams, away_teams]).drop_duplicates().reset_index(drop=True)
    # Add dummy strength columns, as they are expected by the pipeline
    teams_df['strength_overall_home'] = np.random.randint(1000, 1400, size=len(teams_df))
    teams_df['strength_overall_away'] = np.random.randint(900, 1300, size=len(teams_df))
    teams_df.to_csv('data/teams.csv', index=False)
    print("teams.csv created.")

    # --- 2. Create fixtures_df ---
    fixtures_df = matches_df[['game_id', 'start_time', 'home_team_id', 'away_team_id', 'home_score', 'away_score']].copy()
    fixtures_df.rename(columns={'game_id': 'id', 'start_time': 'kickoff_time', 'home_team_id': 'team_h', 'away_team_id': 'team_a',
                               'home_score': 'team_h_score', 'away_score': 'team_a_score'}, inplace=True)
    fixtures_df.to_csv('data/fixtures.csv', index=False)
    print("fixtures.csv created.")

    # --- 3. Create players_df and player_history_df ---
    all_incidents = []
    for index, row in matches_df.iterrows():
        for incident in row['incidents']:
            incident['game_id'] = row['game_id']
            all_incidents.append(incident)

    if not all_incidents:
        print("No incidents found in the data. Cannot create players and player_history.")
        return

    incidents_df = pd.DataFrame(all_incidents)

    players = {}
    for index, row in incidents_df.iterrows():
        player_id = row['playerId']
        if player_id and player_id not in players:
            players[player_id] = {
                'id': player_id,
                'Nombre': row['playerName'],
                'Apellido': '',  # WhoScored data does not have first/last name separated
                'Posicion': 'Midfielder', # Dummy position
                'Precio': np.random.randint(40, 130), # Dummy price
                'team_id': -1 # Placeholder, to be filled later
            }

    # Try to infer team_id from the match data
    for index, row in matches_df.iterrows():
        for incident in row['incidents']:
            player_id = incident['playerId']
            if player_id in players:
                if incident['field'] == 0: # Home team
                    players[player_id]['team_id'] = row['home_team_id']
                elif incident['field'] == 1: # Away team
                    players[player_id]['team_id'] = row['away_team_id']

    players_df = pd.DataFrame(list(players.values()))
    players_df.to_csv('data/players.csv', index=False)
    print("players.csv created.")

    player_history_df = incidents_df[['game_id', 'playerId', 'type', 'subType']].copy()
    player_history_df.rename(columns={'game_id': 'fixture', 'playerId': 'element'}, inplace=True)
    # Add dummy points for events
    player_history_df['total_points'] = player_history_df['type'].apply(lambda x: 5 if x == 1 else (2 if x==2 else 0))
    player_history_df.to_csv('data/player_history.csv', index=False)
    print("player_history.csv created.")

    # --- 4. Create gameweeks_df ---
    matches_df['start_time'] = pd.to_datetime(matches_df['start_time'])
    matches_df['gameweek'] = matches_df['start_time'].dt.isocalendar().week
    gameweeks_df = pd.DataFrame(matches_df['gameweek'].unique(), columns=['id'])
    gameweeks_df['name'] = 'Gameweek ' + gameweeks_df['id'].astype(str)
    gameweeks_df['deadline_time'] = matches_df.groupby('gameweek')['start_time'].min().values
    gameweeks_df['finished'] = True
    gameweeks_df['is_previous'] = False
    gameweeks_df['is_current'] = False
    gameweeks_df['is_next'] = False
    gameweeks_df.to_csv('data/gameweeks.csv', index=False)
    print("gameweeks.csv created.")

if __name__ == "__main__":
    prepare_whoscored_data()
