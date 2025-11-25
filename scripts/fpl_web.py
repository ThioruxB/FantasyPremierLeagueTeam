
import requests
import pandas as pd
import http.server
import socketserver
import threading

# Fetch data from the FPL API
url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
response = requests.get(url)
data = response.json()

# Create DataFrames
teams_df = pd.DataFrame(data['teams'])
players_df = pd.DataFrame(data['elements'])

# Select and rename columns for players
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
players_df = players_df[player_columns.keys()].rename(columns=player_columns)

# Map team and position IDs to names
team_names = teams_df.set_index('id')['name'].to_dict()
position_names = {1: 'Portero', 2: 'Defensa', 3: 'Medio', 4: 'Delantero'}
players_df['Equipo'] = players_df['Equipo'].map(team_names)
players_df['Posicion'] = players_df['Posicion'].map(position_names)

# Convert DataFrames to HTML tables
teams_html = teams_df[['id', 'name', 'strength_overall_home', 'strength_overall_away']].to_html(index=False, classes='table table-striped')
players_html = players_df.to_html(index=False, classes='table table-striped')

# Create the HTML content
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FPL Data</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        <h1 class="mt-4">Equipos de la Premier League</h1>
        {teams_html}
        <h1 class="mt-4">Jugadores de la Premier League</h1>
        {players_html}
    </div>
</body>
</html>
"""

# Write the HTML content to a file
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

# Start a simple web server
PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

def run_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Servidor iniciado en http://localhost:{PORT}")
        httpd.serve_forever()

# Run the server in a background thread
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

print("El archivo index.html ha sido creado. El servidor está ejecutándose en segundo plano.")
print("Puedes abrir la página en tu navegador: http://localhost:8000")
import time
time.sleep(3600) # Keep the main thread alive for an hour
