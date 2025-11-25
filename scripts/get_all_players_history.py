
import requests
import json
import pandas as pd
import time
import os

def get_all_players_history(file_path):
    """
    Fetches the FPL history for all players for the last 2 seasons and saves it to a CSV file.
    Includes a delay to be respectful to the API.
    """
    # Step 1: Get all player data
    try:
        print("Fetching list of all players...")
        bootstrap_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        response = requests.get(bootstrap_url)
        response.raise_for_status()
        data = response.json()
        players = data['elements']
        print(f"Found {len(players)} players.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bootstrap data: {e}")
        return

    all_history_records = []
    total_players = len(players)

    # Loop through each player
    for i, player in enumerate(players):
        player_id = player['id']
        player_name = f"{player['first_name']} {player['second_name']}"
        
        print(f"Processing player {i+1}/{total_players}: {player_name.encode('ascii', 'replace').decode('ascii')} (ID: {player_id})")

        # Step 2: Get the player's historical data
        try:
            history_url = f'https://fantasy.premierleague.com/api/element-summary/{player_id}/'
            response = requests.get(history_url)
            response.raise_for_status()
            history_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"  -> Could not fetch history for {player_name.encode('ascii', 'replace').decode('ascii')}: {e}")
            time.sleep(1) # Still sleep even on error
            continue # Move to the next player

        past_seasons = history_data.get('history_past', [])

        if not past_seasons:
            print(f"  -> No past season data found for {player_name.encode('ascii', 'replace').decode('ascii')}.")
            time.sleep(1) # Still sleep
            continue

        # Add player info to each season record and append to master list
        for season in past_seasons[-2:]:
            season['player_id'] = player_id
            season['player_name'] = player_name
            all_history_records.append(season)
        
        # Be respectful to the API
        time.sleep(1)

    if not all_history_records:
        print("No historical data was collected for any player.")
        return

    # Step 3: Create DataFrame and save to CSV
    print("\nProcessing complete. Creating CSV file...")
    df = pd.DataFrame(all_history_records)

    # Reorder columns to have player info first
    if 'player_id' in df.columns and 'player_name' in df.columns:
        cols = df.columns.tolist()
        id_col_index = cols.index('player_id')
        name_col_index = cols.index('player_name')
        cols.insert(0, cols.pop(name_col_index))
        cols.insert(0, cols.pop(id_col_index))
        df = df[cols]

    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"\nSuccessfully saved all players' history to {file_path}")


if __name__ == "__main__":
    output_directory = "D:\\ConectPremier"
    output_filename = "all_players_2_seasons_history.csv"
    full_path = os.path.join(output_directory, output_filename)
    get_all_players_history(full_path)
