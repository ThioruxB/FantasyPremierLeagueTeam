
import requests
import json
import pandas as pd

player_id = 579 # Son
player_name = "Son Heung-min"

print(f"--- Debugging for player {player_name} ---")

try:
    history_url = f'https://fantasy.premierleague.com/api/element-summary/{player_id}/'
    response = requests.get(history_url)
    response.raise_for_status()
    history_data = response.json()
    print("1. Successfully fetched API data.")
except Exception as e:
    print(f"Error fetching API data: {e}")
    exit()

past_seasons = history_data.get('history_past', [])
if not past_seasons:
    print("No past seasons found.")
    exit()

print("\n2. Looping through the last 2 seasons from API response...")
player_seasons_data = []
for i, season in enumerate(past_seasons[-2:]):
    print(f"\n--- Season {i+1} ---")
    print("3. Raw 'season' dictionary from API:")
    print(season)
    
    start_cost_raw = season.get('start_cost')
    print(f"4. Value of season.get('start_cost'): {start_cost_raw}")

    record = {
        'player_id': player_id,
        'player_name': player_name,
        'season_name': season.get('season_name'),
        'start_cost': season.get('start_cost', 0),
        'total_points': season.get('total_points', 0)
    }
    print("5. 'record' dictionary created:")
    print(record)
    player_seasons_data.append(record)

print("\n--- Post-Loop ---")
print("6. Final list of records to be put in DataFrame:")
print(player_seasons_data)

df_player = pd.DataFrame(player_seasons_data)
print("7. DataFrame created.")
print(df_player)

print("\n8. Final check of the 'start_cost' column in the DataFrame:")
print(df_player['start_cost'])
