
import requests
import json
import pandas as pd
import time
import os

def get_all_players_history_resumable(file_path):
    """
    Fetches the FPL history for all players for the last 2 seasons and saves it to a CSV file.
    This version saves incrementally and can be resumed if interrupted.
    """
    # Step 1: Get all player data from the bootstrap endpoint
    try:
        print("Fetching list of all players...")
        bootstrap_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        response = requests.get(bootstrap_url)
        response.raise_for_status()
        data = response.json()
        players = data['elements']
        print(f"Found {len(players)} players.")
    except requests.exceptions.RequestException as e:
        print(f"Fatal Error: Could not fetch bootstrap data: {e}")
        return

    # Step 2: Check for existing file to determine where to resume
    processed_player_ids = set()
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        print(f"Output file found. Reading processed players to resume...")
        try:
            df_existing = pd.read_csv(file_path)
            if 'player_id' in df_existing.columns:
                processed_player_ids = set(df_existing['player_id'].unique())
            print(f"Resuming. {len(processed_player_ids)} players already in CSV.")
        except (pd.errors.EmptyDataError, FileNotFoundError):
            print("Could not read existing CSV, starting from scratch.")
    else:
        print("No existing data found. Starting from scratch.")

    total_players = len(players)

    # Step 3: Loop through each player
    for i, player in enumerate(players):
        player_id = player['id']
        player_name = f"{player['first_name']} {player['second_name']}"

        if player_id in processed_player_ids:
            continue

        print(f"Processing player {i+1}/{total_players}: {player_name.encode('ascii', 'replace').decode('ascii')} (ID: {player_id})")

        try:
            history_url = f'https://fantasy.premierleague.com/api/element-summary/{player_id}/'
            response = requests.get(history_url)
            response.raise_for_status()
            history_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"  -> Could not fetch history for {player_name.encode('ascii', 'replace').decode('ascii')}: {e}")
            time.sleep(1)
            continue

        past_seasons = history_data.get('history_past', [])

        if not past_seasons:
            print(f"  -> No past season data found for {player_name.encode('ascii', 'replace').decode('ascii')}.")
            time.sleep(1)
            continue
        
        # Robustly prepare data for appending
        player_seasons_data = []
        for season in past_seasons[-2:]:
            record = {
                'player_id': player_id,
                'player_name': player_name,
                'season_name': season.get('season_name'),
                'start_cost': season.get('start_cost', 0),
                'total_points': season.get('total_points', 0),
                'minutes': season.get('minutes', 0),
                'goals_scored': season.get('goals_scored', 0),
                'assists': season.get('assists', 0),
                'clean_sheets': season.get('clean_sheets', 0),
                'goals_conceded': season.get('goals_conceded', 0),
                'bonus': season.get('bonus', 0),
                'yellow_cards': season.get('yellow_cards', 0),
                'red_cards': season.get('red_cards', 0)
            }
            player_seasons_data.append(record)

        if not player_seasons_data:
            time.sleep(1)
            continue

        # Step 4: Append to CSV incrementally
        df_player = pd.DataFrame(player_seasons_data)
        
        cols_order = ['player_id', 'player_name', 'season_name', 'start_cost', 'total_points', 'minutes', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded', 'bonus', 'yellow_cards', 'red_cards']
        df_player = df_player[cols_order]

        write_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
        
        try:
            df_player.to_csv(file_path, mode='a', header=write_header, index=False, encoding='utf-8-sig')
            print(f"  -> Successfully appended data for {player_name.encode('ascii', 'replace').decode('ascii')}")
        except IOError as e:
            print(f"  -> ERROR: Could not write to file {file_path}: {e}")

        time.sleep(1)

    print("\n--- Processing Complete ---")

if __name__ == "__main__":
    output_directory = "D:\\ConectPremier"
    output_filename = "all_players_history_resumable.csv"
    full_path = os.path.join(output_directory, output_filename)
    get_all_players_history_resumable(full_path)
