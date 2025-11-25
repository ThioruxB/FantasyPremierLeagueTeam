import requests
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# Fetch data from the FPL API
url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
response = requests.get(url)
data = response.json()

# Create DataFrames
teams_df = pd.DataFrame(data['teams'])
players_df = pd.DataFrame(data['elements'])

# --- 1. Value for Money --- 
print("--- 1. Jugadores con mejor relación calidad-precio (Puntos por Millón) ---")
players_df['cost_in_millions'] = players_df['now_cost'] / 10.0
players_df['points_per_million'] = players_df['total_points'] / players_df['cost_in_millions']
value_for_money = players_df[players_df['total_points'] > 0].sort_values('points_per_million', ascending=False)
print(value_for_money[['first_name', 'second_name', 'total_points', 'cost_in_millions', 'points_per_million']].head(10))
print("\n")

# --- 2. Top Performers by Position ---
print("--- 2. Mejores jugadores por posición (Total de Puntos) ---")
position_names = {1: 'Portero', 2: 'Defensa', 3: 'Medio', 4: 'Delantero'}
players_df['position_name'] = players_df['element_type'].map(position_names)
top_performers = players_df.loc[players_df.groupby('position_name')['total_points'].idxmax()]
print(top_performers[['first_name', 'second_name', 'position_name', 'total_points', 'goals_scored', 'assists']])
print("\n")

# --- 3. Team Strength Analysis ---
print("--- 3. Análisis de Fortaleza de los Equipos ---")
teams_df['strength_attack_overall'] = teams_df['strength_attack_home'] + teams_df['strength_attack_away']
teams_df['strength_defence_overall'] = teams_df['strength_defence_home'] + teams_df['strength_defence_away']
strongest_attack = teams_df.sort_values('strength_attack_overall', ascending=False).head(5)
strongest_defence = teams_df.sort_values('strength_defence_overall', ascending=False).head(5)
print("Equipos con mejor ataque:")
print(strongest_attack[['name', 'strength_attack_home', 'strength_attack_away', 'strength_attack_overall']])
print("\nEquipos con mejor defensa:")
print(strongest_defence[['name', 'strength_defence_home', 'strength_defence_away', 'strength_defence_overall']])
print("\n")

# --- 4. Price Distribution ---
print("--- 4. Distribución de Precios de los Jugadores ---")
price_bins = [0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
price_labels = ['<5m', '5-6m', '6-7m', '7-8m', '8-9m', '9-10m', '10-11m', '11-12m', '12-13m', '13-14m', '>14m']
players_df['price_range'] = pd.cut(players_df['cost_in_millions'], bins=price_bins, labels=price_labels, right=False)
price_distribution = players_df['price_range'].value_counts().sort_index()
print(price_distribution)
print("\n")

# --- 5. Correlation Analysis ---
print("--- 5. Correlación entre estadísticas de jugadores ---")
correlation_cols = ['total_points', 'cost_in_millions', 'goals_scored', 'assists', 'minutes', 'bps']
correlation_matrix = players_df[correlation_cols].corr()
print(correlation_matrix)