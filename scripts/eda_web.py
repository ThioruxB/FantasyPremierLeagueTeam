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

# --- Analysis ---
# (The analysis code remains the same)
players_df['cost_in_millions'] = players_df['now_cost'] / 10.0
players_df['points_per_million'] = players_df['total_points'] / players_df['cost_in_millions']
value_for_money = players_df[players_df['total_points'] > 0].sort_values('points_per_million', ascending=False).head(10)
position_names = {1: 'Portero', 2: 'Defensa', 3: 'Medio', 4: 'Delantero'}
players_df['position_name'] = players_df['element_type'].map(position_names)
top_performers = players_df.loc[players_df.groupby('position_name')['total_points'].idxmax()]
teams_df['strength_attack_overall'] = teams_df['strength_attack_home'] + teams_df['strength_attack_away']
teams_df['strength_defence_overall'] = teams_df['strength_defence_home'] + teams_df['strength_defence_away']
strongest_attack = teams_df.sort_values('strength_attack_overall', ascending=False).head(5)
strongest_defence = teams_df.sort_values('strength_defence_overall', ascending=False).head(5)
price_bins = [0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
price_labels = ['<5m', '5-6m', '6-7m', '7-8m', '8-9m', '9-10m', '10-11m', '11-12m', '12-13m', '13-14m', '>14m']
players_df['price_range'] = pd.cut(players_df['cost_in_millions'], bins=price_bins, labels=price_labels, right=False)
price_distribution = players_df['price_range'].value_counts().sort_index().reset_index()
price_distribution.columns = ['Rango de Precio', 'Cantidad de Jugadores']
correlation_cols = ['total_points', 'cost_in_millions', 'goals_scored', 'assists', 'minutes', 'bps']
correlation_matrix = players_df[correlation_cols].corr()

# --- Generate HTML with ER Diagram ---
html = f"""
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>FPL EDA - Professional Report</title>
    <link href='https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css' rel='stylesheet'>
    <link href='https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap' rel='stylesheet'>
    <style>
        body {{
            font-family: 'Lato', sans-serif;
            background-color: #f4f7f6;
            color: #333;
        }}
        .container {{
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-top: 2rem;
            margin-bottom: 2rem;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            font-weight: 700;
        }}
        .table thead th {{
            background-color: #e9ecef;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
        }}
        .table {{
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .table-striped tbody tr:nth-of-type(odd) {{
            background-color: rgba(0,0,0,.02);
        }}
        .mermaid {{
            text-align: center;
            margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <div class='container'>
        <h1 class='mt-4 mb-4'>Análisis Exploratorio de Datos FPL 2025</h1>

        <h2 class='mt-5'>Modelo Entidad-Relación</h2>
        <div class='mermaid'>
            erDiagram
                TEAM ||--o{{ PLAYER : "tiene"
                PLAYER ||--|{{ POSITION : "ocupa"

                TEAM {{
                    int id
                    string name
                    int strength_attack
                    int strength_defence
                }}

                PLAYER {{
                    int id
                    string first_name
                    string second_name
                    int now_cost
                    int total_points
                    int team_id
                    int element_type_id
                }}

                POSITION {{
                    int id
                    string name
                }}
        </div>
        
        <h2 class='mt-5'>1. Jugadores con mejor relación calidad-precio (Puntos por Millón)</h2>
        {value_for_money[['first_name', 'second_name', 'total_points', 'cost_in_millions', 'points_per_million']].to_html(index=False, classes='table table-striped')}
        
        <h2 class='mt-5'>2. Mejores jugadores por posición (Total de Puntos)</h2>
        {top_performers[['first_name', 'second_name', 'position_name', 'total_points', 'goals_scored', 'assists']].to_html(index=False, classes='table table-striped')}
        
        <h2 class='mt-5'>3. Análisis de Fortaleza de los Equipos</h2>
        <h3>Equipos con mejor ataque:</h3>
        {strongest_attack[['name', 'strength_attack_home', 'strength_attack_away', 'strength_attack_overall']].to_html(index=False, classes='table table-striped')}
        <h3 class='mt-4'>Equipos con mejor defensa:</h3>
        {strongest_defence[['name', 'strength_defence_home', 'strength_defence_away', 'strength_defence_overall']].to_html(index=False, classes='table table-striped')}
        
        <h2 class='mt-5'>4. Distribución de Precios de los Jugadores</h2>
        {price_distribution.to_html(index=False, classes='table table-striped')}
        
        <h2 class='mt-5'>5. Correlación entre estadísticas de jugadores</h2>
        {correlation_matrix.style.background_gradient(cmap='coolwarm').format('{:.2f}').set_properties(**{'border': '1px solid black', 'width': '100px', 'text-align': 'center'}).to_html()}
        
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
</body>
</html>
"""

with open('eda.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("El archivo eda.html ha sido actualizado con el Modelo Entidad-Relación.")