
import pandas as pd
from sqlalchemy import create_engine, text
import os

def upload_season_history():
    """
    Connects to the database, creates the 'player_season_history' table if it doesn't exist,
    and upserts the aggregated season data from the CSV file to avoid duplicates.
    """
    # --- Configuration ---
    db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
    csv_file_path = 'D:\\ConectPremier\\all_players_history_resumable.csv'
    table_name = 'player_season_history'

    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        return

    # --- Database Engine ---
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            connect_args={'sslmode': 'require'}
        )
        print("Database engine created.")
    except Exception as e:
        print(f"Error creating database engine: {e}")
        return

    # --- CREATE TABLE Statement with Primary Key ---
    create_table_query = text(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        player_id INT,
        player_name VARCHAR(255),
        season_name VARCHAR(50),
        start_cost INT,
        total_points INT,
        minutes INT,
        goals_scored INT,
        assists INT,
        clean_sheets INT,
        goals_conceded INT,
        bonus INT,
        yellow_cards INT,
        red_cards INT,
        PRIMARY KEY (player_id, season_name)
    );
    """)

    try:
        with engine.begin() as connection:
            print(f"Ensuring table '{table_name}' exists...")
            connection.execute(create_table_query)
            print("Table is ready.")

            print("Reading data from CSV...")
            df = pd.read_csv(csv_file_path)

            # --- Data Cleaning and Selection ---
            columns_to_upload = [
                'player_id', 'player_name', 'season_name', 'start_cost', 'total_points', 'minutes', 
                'goals_scored', 'assists', 'clean_sheets', 'goals_conceded', 
                'bonus', 'yellow_cards', 'red_cards'
            ]
            
            df_to_upload = df[[col for col in columns_to_upload if col in df.columns]]

            # --- Upsert Logic ---
            temp_table_name = "temp_season_history"
            df_to_upload.to_sql(temp_table_name, connection, if_exists='replace', index=False)
            print(f"Data loaded into temporary table '{temp_table_name}'.")

            upsert_query = text(f"""
            INSERT INTO {table_name} (
                player_id, player_name, season_name, start_cost, total_points, minutes, goals_scored, 
                assists, clean_sheets, goals_conceded, bonus, yellow_cards, red_cards
            )
            SELECT 
                t.player_id, t.player_name, t.season_name, t.start_cost, t.total_points, t.minutes, t.goals_scored, 
                t.assists, t.clean_sheets, t.goals_conceded, t.bonus, t.yellow_cards, t.red_cards
            FROM {temp_table_name} t
            ON CONFLICT (player_id, season_name) 
            DO UPDATE SET
                player_name = EXCLUDED.player_name,
                start_cost = EXCLUDED.start_cost,
                total_points = EXCLUDED.total_points,
                minutes = EXCLUDED.minutes,
                goals_scored = EXCLUDED.goals_scored,
                assists = EXCLUDED.assists,
                clean_sheets = EXCLUDED.clean_sheets,
                goals_conceded = EXCLUDED.goals_conceded,
                bonus = EXCLUDED.bonus,
                yellow_cards = EXCLUDED.yellow_cards,
                red_cards = EXCLUDED.red_cards;
            """)
            
            print("Inserting or updating data into final table to avoid duplicates...")
            connection.execute(upsert_query)
            
            connection.execute(text(f"DROP TABLE {temp_table_name};"))
            print("Temporary table dropped.")
            
            print(f"Data successfully uploaded to '{table_name}'.")

    except Exception as e:
        print(f"An error occurred during the database operation: {e}")

if __name__ == "__main__":
    upload_season_history()
