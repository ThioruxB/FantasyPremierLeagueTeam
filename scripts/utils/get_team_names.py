
import json
import pandas as pd
from sqlalchemy import create_engine

def get_team_names():
    """
    Reads team names from the database and from the consolidated whoscored data
    and prints them to help create a mapping.
    """
    # Get team names from the database
    db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
    try:
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={'sslmode': 'require'})
        with engine.connect() as conn:
            fpl_teams_df = pd.read_sql("SELECT name FROM teams", conn)
            fpl_team_names = set(fpl_teams_df['name'])
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return

    # Get team names from the whoscored data
    try:
        with open('consolidated_whoscored_data.json', 'r', encoding='utf-8') as f:
            whoscored_data = json.load(f)
    except FileNotFoundError:
        print("Error: consolidated_whoscored_data.json not found.")
        return

    whoscored_teams_df = pd.DataFrame(whoscored_data)
    whoscored_home_teams = set(whoscored_teams_df['home_team'])
    whoscored_away_teams = set(whoscored_teams_df['away_team'])
    whoscored_team_names = whoscored_home_teams.union(whoscored_away_teams)

    print("--- FPL Team Names ---")
    for team in sorted(list(fpl_team_names)):
        print(team)

    print("\n--- WhoScored Team Names ---")
    for team in sorted(list(whoscored_team_names)):
        print(team)

    print("\n--- Teams in WhoScored but not in FPL ---")
    for team in sorted(list(whoscored_team_names - fpl_team_names)):
        print(team)

    print("\n--- Teams in FPL but not in WhoScored ---")
    for team in sorted(list(fpl_team_names - whoscored_team_names)):
        print(team)

if __name__ == "__main__":
    get_team_names()
