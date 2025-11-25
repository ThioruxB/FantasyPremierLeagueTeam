import requests
import pandas as pd
from sqlalchemy import create_engine, text
from pandas.io.sql import get_schema

# --- 1. Fetch data from the FPL API ---
url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
print("Fetching data from FPL API...")
response = requests.get(url)
data = response.json()
print("Data fetched successfully.")

# --- 2. Process Data into Pandas DataFrames ---
print("Processing data into DataFrames...")
teams_df = pd.DataFrame(data['teams'])
players_df = pd.DataFrame(data['elements'])
gameweeks_df = pd.DataFrame(data['events'])
player_types_df = pd.DataFrame(data['element_types'])

# Clean and prepare players data
player_columns = {
    'first_name': 'Nombre',
    'second_name': 'Apellido',
    'team': 'Equipo',
    'element_type': 'Posicion',
    'now_cost': 'Precio',
    'total_points': 'Puntos Totales',
    'goals_scored': 'Goles',
    'assists': 'Asistencias'
}
players_df = players_df[list(player_columns.keys())].rename(columns=player_columns)

team_names = teams_df.set_index('id')['name'].to_dict()
# Use the full player_types_df for mapping before it's modified
position_names = player_types_df.set_index('id')['singular_name'].to_dict()

players_df['Equipo'] = players_df['Equipo'].map(team_names)
players_df['Posicion'] = players_df['Posicion'].map(position_names)

# Clean and prepare gameweeks data
gameweek_columns = ['id', 'name', 'deadline_time', 'finished', 'is_previous', 'is_current', 'is_next']
gameweeks_df = gameweeks_df[gameweek_columns]

print("Data processing complete.")

# --- 3. Database Operations ---

# Database connection
db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    connect_args={'sslmode': 'require'}
)

# Dynamically generate the CREATE TABLE statement for player_types
# This ensures all columns from the API are included
player_types_schema = get_schema(player_types_df.reset_index(), 'player_types', con=engine)

print("Connecting to the database and starting transaction...")
with engine.begin() as connection:
    print("Connection successful.")
    
    # Drop all tables in order
    print("Dropping existing tables (if any)...")
    connection.execute(text("DROP TABLE IF EXISTS players;"))
    connection.execute(text("DROP TABLE IF EXISTS teams;"))
    connection.execute(text("DROP TABLE IF EXISTS gameweeks;"))
    connection.execute(text("DROP TABLE IF EXISTS player_types;"))

    # Create all tables
    print("Creating tables...")
    
    # teams table (manual schema)
    connection.execute(text("""
    CREATE TABLE teams (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        strength_overall_home INT,
        strength_overall_away INT
    )
    """))

    # player_types table (dynamic schema)
    connection.execute(text(player_types_schema))

    # gameweeks table (manual schema)
    connection.execute(text("""
    CREATE TABLE gameweeks (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        deadline_time TIMESTAMP WITH TIME ZONE,
        finished BOOLEAN,
        is_previous BOOLEAN,
        is_current BOOLEAN,
        is_next BOOLEAN
    )
    """))

    # players table (manual schema)
    connection.execute(text("""
    CREATE TABLE players (
        id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        "Nombre" VARCHAR(255),
        "Apellido" VARCHAR(255),
        "Equipo" VARCHAR(255),
        "Posicion" VARCHAR(255),
        "Precio" INT,
        "Puntos Totales" INT,
        "Goles" INT,
        "Asistencias" INT
    )
    """))
    print("Tables created successfully.")

    # Insert data into tables
    print("Inserting data into tables...")
    
    teams_df[['id', 'name', 'strength_overall_home', 'strength_overall_away']].to_sql('teams', con=connection, if_exists='append', index=False, method='multi')
    print("- Data inserted into 'teams'.")
    
    player_types_df.to_sql('player_types', con=connection, if_exists='append', index=False, method='multi')
    print("- Data inserted into 'player_types'.")
    
    gameweeks_df.to_sql('gameweeks', con=connection, if_exists='append', index=False, method='multi')
    print("- Data inserted into 'gameweeks'.")
    
    players_df.to_sql('players', con=connection, if_exists='append', index=False, method='multi', chunksize=1000)
    print("- Data inserted into 'players'.")

print("\nTransaction committed. All tables created and data inserted successfully.")