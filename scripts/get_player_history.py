
import requests
import json
import pandas as pd

def get_player_history_to_csv(player_name, file_path='player_history.csv'):
    """
    Fetches the last two seasons of FPL history for a given player and saves it to a CSV file.
    """
    # Step 1: Get all player data to find the player's ID
    try:
        bootstrap_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        response = requests.get(bootstrap_url)
        response.raise_for_status()
        data = response.json()
        players = data['elements']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bootstrap data: {e}")
        return

    # Step 2: Find the player's ID by their web name
    player = next((p for p in players if p['web_name'] == player_name), None)

    if not player:
        print(f"Player '{player_name}' not found.")
        return

    player_id = player['id']
    print(f"Found player: {player['first_name']} {player['second_name']} (ID: {player_id})")

    # Step 3: Get the player's historical data
    try:
        history_url = f'https://fantasy.premierleague.com/api/element-summary/{player_id}/'
        response = requests.get(history_url)
        response.raise_for_status()
        history_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player history: {e}")
        return

    past_seasons = history_data.get('history_past', [])

    if not past_seasons:
        print("No past season data found for this player.")
        return

    # Step 4: Process data and save to CSV
    last_two_seasons = past_seasons[-2:]
    if not last_two_seasons:
        print("Not enough historical data to save.")
        return

    df = pd.DataFrame(last_two_seasons)
    
    # Select and reorder columns for clarity
    columns_to_keep = [
        'season_name', 'total_points', 'minutes', 'goals_scored', 'assists',
        'clean_sheets', 'goals_conceded', 'bonus', 'yellow_cards', 'red_cards'
    ]
    # Filter to only columns that exist in the dataframe
    df_selected = df[[col for col in columns_to_keep if col in df.columns]]

    df_selected.to_csv(file_path, index=False)
    print(f"\nSuccessfully saved data to {file_path}")


if __name__ == "__main__":
    get_player_history_to_csv("Son", "D:\\ConectPremier\\son_history.csv")
