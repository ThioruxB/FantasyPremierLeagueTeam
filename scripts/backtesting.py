
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpBinary
import numpy as np
import warnings

# Suppress pulp informational messages
warnings.filterwarnings("ignore", category=UserWarning)

# --- 1. CONFIGURATION & DATABASE CONNECTION ---
DB_URL = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
TABLE_NAME = 'player_season_history'

def get_historical_data():
    """Loads all data from the player_season_history table."""
    try:
        engine = create_engine(DB_URL, pool_pre_ping=True, connect_args={'sslmode': 'require'})
        with engine.connect() as conn:
            # Also fetch current positions as an approximation for historical positions
            df = pd.read_sql(f'SELECT * FROM {TABLE_NAME}', conn)
            positions_df = pd.read_sql('SELECT id as player_id, "Posicion" as position FROM players', conn)
            df = df.merge(positions_df, on='player_id', how='left')
            df['position'].fillna('Unknown', inplace=True)
            print(f"Successfully loaded {len(df)} records from '{TABLE_NAME}' and merged positions.")
            return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# --- 2. TEAM SELECTION LOGIC ---
def select_optimal_team(df, budget=100.0):
    df = df[df['position'] != 'Unknown'].copy()
    df.loc[:, 'start_cost'] = df['start_cost'] / 10.0 # Convert cost to millions

    players = df.to_dict('records')
    prob = LpProblem("BacktestTeamSelection", LpMaximize)
    player_vars = LpVariable.dicts("Player", [p['player_id'] for p in players], cat=LpBinary)
    
    prob += lpSum([player_vars[p['player_id']] * p['xP'] for p in players]), "TotalXP"
    prob += lpSum([player_vars[p['player_id']] * p['start_cost'] for p in players]) <= budget, "TotalCost"
    prob += lpSum([player_vars[p['player_id']] for p in players]) == 15, "TotalPlayers"
    
    prob += lpSum([player_vars[p['player_id']] for p in players if p['position'] == 'Goalkeeper']) == 2
    prob += lpSum([player_vars[p['player_id']] for p in players if p['position'] == 'Defender']) == 5
    prob += lpSum([player_vars[p['player_id']] for p in players if p['position'] == 'Midfielder']) == 5
    prob += lpSum([player_vars[p['player_id']] for p in players if p['position'] == 'Forward']) == 3
    
    prob.solve(None) # Use default solver and hide logs
    
    selected_player_ids = [p['player_id'] for p in players if player_vars[p['player_id']].varValue == 1]
    return df[df['player_id'].isin(selected_player_ids)]

# --- 3. MAIN BACKTESTING LOGIC ---
def run_backtesting():
    df = get_historical_data()
    if df is None:
        return

    seasons = sorted(df['season_name'].unique())
    
    if len(seasons) < 2:
        print("Not enough historical data to run a backtest (need at least 2 seasons).")
        return

    # --- Feature Engineering: Create lagged features ---
    df['season_start_year'] = df['season_name'].str[:4].astype(int)
    df_prev = df.copy()
    df_prev['season_start_year'] = df_prev['season_start_year'] + 1
    prev_cols = {col: f"prev_{col}" for col in df_prev.columns if col not in ['player_id', 'player_name', 'season_start_year', 'position']}
    df_prev.rename(columns=prev_cols, inplace=True)
    
    merged_df = pd.merge(df, df_prev, on=['player_id', 'season_start_year'], suffixes=['', '_y'])

    # --- Loop and Backtest ---
    for i in range(1, len(seasons)):
        train_seasons = seasons[:i]
        test_season = seasons[i]

        print(f"\n{'='*60}")
        print(f"BACKTESTING: Training on {train_seasons}, Testing on {test_season}")
        print(f"{'='*60}")

        train_df = merged_df[merged_df['season_name'].isin(train_seasons)]
        test_df = merged_df[merged_df['season_name'] == test_season]

        if train_df.empty or test_df.empty:
            print("Skipping season, not enough data for train/test split.")
            continue

        features = ['prev_total_points', 'prev_minutes', 'prev_goals_scored', 'prev_assists', 'prev_start_cost']
        target = 'total_points'

        X_train = train_df[features].fillna(0)
        y_train = train_df[target]
        X_test = test_df[features].fillna(0)
        y_test_actual_points = test_df[target]

        print(f"Training model on {len(X_train)} samples...")
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        model.fit(X_train, y_train)

        print("Predicting points (xP) for test season...")
        predicted_xp = model.predict(X_test)
        mae = mean_absolute_error(y_test_actual_points, predicted_xp)
        print(f"-> Model Evaluation (MAE): {mae:.2f} points")

        test_df_with_xp = test_df.copy()
        test_df_with_xp['xP'] = predicted_xp
        
        print("Selecting optimal team based on predicted xP...")
        ideal_team_df = select_optimal_team(test_df_with_xp, budget=100.0)
        
        if not ideal_team_df.empty:
            actual_points_scored = ideal_team_df['total_points'].sum()
            print(f"-> Team Evaluation: The selected team would have scored {actual_points_scored} total points.")
        else:
            print("-> Team Evaluation: Could not select a valid team.")

if __name__ == "__main__":
    run_backtesting()
