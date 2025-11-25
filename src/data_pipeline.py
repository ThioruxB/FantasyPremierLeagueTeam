import pandas as pd
import os
from sqlalchemy import create_engine, text
import requests
import time

# --- 1. Database Connection ---
db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    connect_args={'sslmode': 'require'}
)

def refresh_data():
    print("--- Starting Data Refresh ---")
    bootstrap_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    try:
        response = requests.get(bootstrap_url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bootstrap data: {e}")
        return

    teams_df = pd.DataFrame(data['teams'])
    original_players_df = pd.DataFrame(data['elements'])
    gameweeks_df = pd.DataFrame(data['events'])
    player_types_df = pd.DataFrame(data['element_types'])

    next_gw_df = gameweeks_df[gameweeks_df['is_next'] == True]
    fixtures_df = pd.DataFrame()
    if not next_gw_df.empty:
        next_gw_id = next_gw_df['id'].iloc[0]
        try:
            fixtures_url = f'https://fantasy.premierleague.com/api/fixtures/?event={next_gw_id}'
            fixtures_df = pd.DataFrame(requests.get(fixtures_url).json())
        except requests.exceptions.RequestException as e:
            print(f"Error fetching fixtures data: {e}")

    player_history_data = []
    player_ids = original_players_df['id'].tolist()
    for i, player_id in enumerate(player_ids):
        try:
            player_url = f'https://fantasy.premierleague.com/api/element-summary/{player_id}/'
            history = requests.get(player_url).json().get('history', [])
            for item in history:
                item['element'] = player_id
                player_history_data.append(item)
            time.sleep(0.02)
        except requests.exceptions.RequestException:
            continue
    player_history_df = pd.DataFrame(player_history_data)

    gameweek_cols = ['id', 'name', 'deadline_time', 'finished', 'is_previous', 'is_current', 'is_next']
    gameweeks_df = gameweeks_df[gameweek_cols]

    player_cols = {
        'id': 'id', 'first_name': 'Nombre', 'second_name': 'Apellido', 'team': 'team_id', 
        'element_type': 'Posicion', 'now_cost': 'Precio', 'total_points': 'Puntos Totales',
        'cost_change_event': 'tendencia', 'status': 'status', 'news': 'news',
        'chance_of_playing_next_round': 'chance_of_playing_next_round'
    }
    players_df = original_players_df[list(player_cols.keys())].rename(columns=player_cols)
    players_df['Posicion'] = players_df['Posicion'].map(player_types_df.set_index('id')['singular_name'])
    # Filtrar jugadores no disponibles o con noticias
    players_df = players_df[players_df['status'] == 'a']
    players_df = players_df[players_df['news'].str.len() == 0]

    try:
        with engine.begin() as conn:
            for table in ["fixtures", "player_history", "players", "teams", "gameweeks", "player_types"]:
                conn.execute(text(f"DROP TABLE IF EXISTS {table};"))
            teams_df.to_sql('teams', conn, index=False, if_exists='replace')
            gameweeks_df.to_sql('gameweeks', conn, index=False, if_exists='replace')
            player_types_df.to_sql('player_types', conn, index=False, if_exists='replace')
            players_df.to_sql('players', conn, index=False, if_exists='replace')
            if not player_history_df.empty: player_history_df.to_sql('player_history', conn, index=False, if_exists='replace')
            if not fixtures_df.empty: fixtures_df.to_sql('fixtures', conn, index=False, if_exists='replace')
        print("--- Data Refresh Complete ---")
    except Exception as e:
        print(f"An error occurred during database operations: {e}")

def get_data_from_db():
    print("--- Loading data from database ---")
    try:
        with engine.connect() as conn:
            return {name: pd.read_sql(f"SELECT * FROM {name}", conn) for name in ["players", "teams", "gameweeks", "player_history", "fixtures"]}
    except Exception as e:
        print(f"An error occurred while loading data: {e}")
        return None

def calculate_features(db_data):
    print("--- Calculating features ---")
    players_df = db_data['players'].set_index('id')
    teams_df = db_data['teams'].set_index('id')
    history_df = db_data['player_history']
    fixtures_df = db_data['fixtures']

    # Form
    if not history_df.empty:
        history_df = history_df.sort_values(by=['element', 'round'])
        form = history_df.groupby('element')['total_points'].apply(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
        players_df['form'] = form.groupby('element').last()

    # Difficulty
    if not fixtures_df.empty:
        opp_map = {row['team_h']: {'opp': row['team_a'], 'home': True} for _, row in fixtures_df.iterrows()}
        opp_map.update({row['team_a']: {'opp': row['team_h'], 'home': False} for _, row in fixtures_df.iterrows()})
        players_df['opponent'] = players_df['team_id'].map(lambda x: opp_map.get(x, {}).get('opp'))
        players_df['is_home'] = players_df['team_id'].map(lambda x: opp_map.get(x, {}).get('home'))
        def get_strength(row):
            if pd.isna(row['opponent']): return None
            strength = teams_df.loc[row['opponent']]
            return strength['strength_overall_away'] if row['is_home'] else strength['strength_overall_home']
        players_df['difficulty'] = players_df.apply(get_strength, axis=1)

    # Value
    players_df['valor'] = (players_df['form'] / (players_df['Precio'] / 10.0)).fillna(0)
    return players_df.reset_index()

if __name__ == '__main__':
    refresh_data()
    db_data = get_data_from_db()

    if db_data:
        players_df = calculate_features(db_data)
        players_df = players_df[players_df['status'] == 'a']

        # --- 5. Save and Display Results ---
        if not os.path.exists('data/processed'):
            os.makedirs('data/processed')
        players_df.to_csv('data/processed/filtered_players.csv', index=False, encoding='utf-8-sig')