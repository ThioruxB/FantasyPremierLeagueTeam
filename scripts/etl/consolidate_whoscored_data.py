
import json
import glob
import pandas as pd

def consolidate_data():
    """
    Reads all whoscored_data*.json files, consolidates them into a single
    DataFrame, removes duplicates, and saves the result to a new JSON file.
    """
    json_files = ['consolidated_whoscored_data.json', 'nuevos_datos.json']
    all_data = []
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_data.extend(data)

    if not all_data:
        print("No data found in any of the whoscored_data*.json files.")
        return

    # Use pandas to handle duplicates and sorting
    df = pd.DataFrame(all_data)
    df.drop_duplicates(subset='game_id', inplace=True)
    df['start_time'] = pd.to_datetime(df['start_time'])
    df.sort_values(by='start_time', inplace=True)
    df['start_time'] = df['start_time'].astype(str) # Convert back to string for JSON serialization

    # Convert to dictionary for saving
    consolidated_data = df.to_dict(orient='records')

    with open('consolidated_whoscored_data.json', 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, ensure_ascii=False, indent=4)

    print(f"Consolidated {len(consolidated_data)} unique matches into 'consolidated_whoscored_data.json'")

if __name__ == "__main__":
    consolidate_data()
