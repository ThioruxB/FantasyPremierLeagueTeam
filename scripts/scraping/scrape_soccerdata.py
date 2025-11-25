import soccerdata
import pandas as pd
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
import sys
import glob

# Helper function to load CSVs safely
def _load_csv_to_df(filepath, id_col=None, date_col=None):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        df = pd.read_csv(filepath)
        if id_col and id_col not in df.columns:
            print(f"Warning: ID column '{id_col}' not found in {filepath}. Skipping ID processing.")
        if date_col and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], format='mixed')
        return df
    return pd.DataFrame()

# Helper function to get existing game IDs and the latest date from partidos.csv
def _get_existing_game_ids_and_latest_date():
    partidos_df = _load_csv_to_df('partidos.csv', id_col='partido_id', date_col='fecha_inicio')
    
    existing_game_ids = set(partidos_df['partido_id']) if not partidos_df.empty else set()
    latest_date = partidos_df['fecha_inicio'].max() if not partidos_df.empty else None

    # Also load game IDs from all whoscored_data*.json files and consolidated_whoscored_data.json
    json_files = glob.glob('whoscored_data*.json')
    json_files.append('consolidated_whoscored_data.json') # Include the consolidated file

    for file in json_files:
        if os.path.exists(file) and os.path.getsize(file) > 0:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for game in data:
                        if 'game_id' in game:
                            existing_game_ids.add(game['game_id'])
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {file}. Skipping.")
            except Exception as e:
                print(f"Warning: Error reading {file}: {e}. Skipping.")
    
    return existing_game_ids, latest_date

# Helper function to delete data for a specific month from all relevant CSVs
def _delete_month_data_from_csv(year, month):
    print(f"\nEliminando datos del mes {month}/{year} de los archivos CSV existentes...")
    
    csv_files = {
        'partidos.csv': {'df': None, 'date_col': 'fecha_inicio', 'id_col': 'partido_id'},
        'incidentes.csv': {'df': None, 'date_col': 'minuto', 'id_col': 'incidente_id'}, # 'minuto' is not a date, need to link to partidos.csv
        'jugadores.csv': {'df': None, 'date_col': None, 'id_col': 'jugador_id'},
        'equipos.csv': {'df': None, 'date_col': None, 'id_col': 'equipo_id'}
    }

    # Load partidos_df first to link incidents
    partidos_df = _load_csv_to_df('partidos.csv', id_col='partido_id', date_col='fecha_inicio')
    if partidos_df.empty:
        print("partidos.csv está vacío o no existe, no hay datos que eliminar.")
        return

    # Identify game_ids to delete from partidos.csv
    partidos_df['fecha_inicio'] = pd.to_datetime(partidos_df['fecha_inicio'])
    games_to_delete_ids = partidos_df[
        (partidos_df['fecha_inicio'].dt.year == year) & 
        (partidos_df['fecha_inicio'].dt.month == month)
    ]['partido_id'].tolist()

    if not games_to_delete_ids:
        print(f"No se encontraron partidos para el mes {month}/{year} en partidos.csv. No se requiere eliminación.")
        return

    # Delete from partidos.csv
    partidos_df = partidos_df[~partidos_df['partido_id'].isin(games_to_delete_ids)]
    partidos_df.to_csv('partidos.csv', index=False)
    print(f"Eliminados partidos del mes {month}/{year} de partidos.csv.")

    # Delete from incidentes.csv
    incidentes_df = _load_csv_to_df('incidentes.csv', id_col='incidente_id')
    if not incidentes_df.empty:
        incidentes_df = incidentes_df[~incidentes_df['partido_id'].isin(games_to_delete_ids)]
        incidentes_df.to_csv('incidentes.csv', index=False)
        print(f"Eliminados incidentes relacionados del mes {month}/{year} de incidentes.csv.")
    
    # For jugadores.csv and equipos.csv, we don't delete directly by month.
    # These should be handled by append_data.py to add new ones and not duplicate existing ones.
    # If a player/team is no longer in any game, it will remain but won't cause issues.
    print("Eliminación de datos completada para el mes especificado.")

def scrape_new_whoscored_data():
    """
    Scrapes WhoScored data for the English Premier League, focusing only on new matches
    not yet present in the local data.
    """
    LEAGUE = "ENG-Premier League"
    # The script should be smart enough to handle season changes, 
    # but we can keep this as a fallback for the schedule query.
    CURRENT_SEASON = "2526" 
    NUEVOS_DATOS_JSON = 'nuevos_datos.json'

    print(f"--- Iniciando script de scraping automático de nuevos partidos ---")

    # --- Paso 1: Obtener IDs de partidos existentes y la última fecha ---
    existing_game_ids, latest_date = _get_existing_game_ids_and_latest_date()
    
    if latest_date:
        # Start scraping from the day of the last match to catch any later games on the same day
        start_date_for_scrape = latest_date.replace(hour=0, minute=0, second=0, microsecond=0)
        print(f"Última fecha de partido encontrada: {latest_date.strftime('%Y-%m-%d')}.")
        print(f"Buscando partidos nuevos desde: {start_date_for_scrape.strftime('%Y-%m-%d')}.")
    else:
        # Default start date if no data exists
        start_date_for_scrape = datetime(2025, 8, 1)
        print("No se encontraron partidos existentes. Buscando desde la fecha de inicio por defecto: 2025-08-01.")

    # --- Paso 2: Obtener calendario de la temporada y filtrar ---
    print(f"\nObteniendo calendario para la temporada {CURRENT_SEASON} de la {LEAGUE}...")
    try:
        # We can query multiple seasons to be robust against season changes
        ws = soccerdata.WhoScored(leagues=LEAGUE, seasons=[CURRENT_SEASON, str(int(CURRENT_SEASON)-101)])
        schedule = ws.read_schedule()
        
        schedule['date'] = pd.to_datetime(schedule['date']).dt.tz_localize(None)

        # Filter for matches that have already occurred up to now
        now = datetime.now()
        schedule_past_games = schedule[schedule['date'] <= now].copy()

        # Filter for matches from our calculated start date onwards
        schedule_new_period = schedule_past_games[schedule_past_games['date'] >= start_date_for_scrape].copy()

        # CRITICAL: Filter out games we already have the ID for
        new_games_schedule = schedule_new_period[~schedule_new_period['game_id'].isin(existing_game_ids)].copy()

        if new_games_schedule.empty:
            print(f"\nNo se encontraron partidos nuevos jugados desde {start_date_for_scrape.strftime('%Y-%m-%d')}.")
            # Create an empty JSON file to ensure the downstream script runs without errors
            with open(NUEVOS_DATOS_JSON, 'w') as f:
                json.dump([], f)
            print(f"Se ha creado un archivo '{NUEVOS_DATOS_JSON}' vacío.")
            return

        print(f"Se encontraron {len(new_games_schedule)} partidos nuevos para procesar.")

    except Exception as e:
        print(f"Error al obtener el calendario de partidos: {e}")
        # Ensure the process can continue gracefully
        with open(NUEVOS_DATOS_JSON, 'w') as f:
            json.dump([], f)
        return

    # --- Paso 3: Iterar sobre partidos nuevos y obtener datos detallados ---
    all_new_games_data = []
    print("\nProcesando cada partido nuevo...")
    for game in new_games_schedule.itertuples():
        game_id = game.game_id
        home_team = game.home_team
        away_team = game.away_team
        print(f"  - Obteniendo datos para: {home_team} vs {away_team} (ID: {game_id})")

        try:
            events = ws.read_events(match_id=game_id)
            
            game_data = {
                "game_id": game_id,
                "stage_id": game.stage_id,
                "start_time": game.date.strftime('%Y-%m-%dT%H:%M:%S'),
                "status": "FT",
                "elapsed": "FT",
                "home_team_id": None, 
                "home_team": home_team,
                "away_team_id": None, 
                "away_team": away_team,
                "home_score": game.home_score, 
                "away_score": game.away_score, 
                "home_yellow_cards": None, 
                "home_red_cards": None, 
                "away_yellow_cards": None, 
                "away_red_cards": None, 
                "incidents": events.to_dict(orient='records') if not events.empty else []
            }
            all_new_games_data.append(game_data)

        except Exception as e:
            print(f"    [!] Error al procesar el partido ID: {game_id}. Se omitirá. Error: {e}")

    # --- Paso 4: Guardar los datos nuevos en un archivo JSON ---
    if not all_new_games_data:
        print("\nNo se pudo recopilar información de ningún partido nuevo.")
        with open(NUEVOS_DATOS_JSON, 'w') as f:
            json.dump([], f)
        print(f"Se ha creado un archivo '{NUEVOS_DATOS_JSON}' vacío.")
        return

    print(f"\nGuardando los datos de {len(all_new_games_data)} partidos nuevos en '{NUEVOS_DATOS_JSON}'...")
    with open(NUEVOS_DATOS_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_new_games_data, f, ensure_ascii=False, indent=4)

    print("\n--- Proceso de scraping finalizado con éxito. ---")


if __name__ == "__main__":
    scrape_new_whoscored_data()