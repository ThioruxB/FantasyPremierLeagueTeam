import json
import pandas as pd
import os

def append_new_data_from_json():
    """
    Reads a JSON file with new match data ('nuevos_datos.json'),
    compares it with existing CSVs, and appends only the new information
    (new matches, players, incidents, etc.) to avoid duplicates.
    """
    JSON_INPUT = 'nuevos_datos.json'
    
    print("--- Iniciando script para añadir nuevos datos a los CSVs ---")

    # --- Paso 1: Cargar los nuevos datos desde el JSON ---
    try:
        with open(JSON_INPUT, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Archivo '{JSON_INPUT}' no encontrado. Ejecuta el script de scraping primero.")
        return
    except json.JSONDecodeError:
        print(f"Error: No se pudo decodificar el JSON de '{JSON_INPUT}'.")
        return

    if not new_data:
        print("El archivo JSON no contiene datos nuevos. No hay nada que añadir.")
        print("\n--- Proceso de apendizado finalizado. ---")
        return

    print(f"Se encontraron {len(new_data)} nuevos partidos en '{JSON_INPUT}'.")

    # --- Paso 2: Definir archivos CSV y sus claves primarias ---
    csv_files = {
        'competiciones': {'name': 'competiciones.csv', 'id': 'competicion_id'},
        'equipos': {'name': 'equipos.csv', 'id': 'equipo_id'},
        'jugadores': {'name': 'jugadores.csv', 'id': 'jugador_id'},
        'partidos': {'name': 'partidos.csv', 'id': 'partido_id'},
        'incidentes': {'name': 'incidentes.csv', 'id': 'incidente_id'}
    }

    # --- Paso 3: Leer IDs existentes de cada CSV ---
    existing_ids = {}
    for key, val in csv_files.items():
        try:
            if os.path.exists(val['name']) and os.path.getsize(val['name']) > 0:
                df = pd.read_csv(val['name'])
                existing_ids[key] = set(df[val['id']])
            else:
                existing_ids[key] = set()
        except (FileNotFoundError, pd.errors.EmptyDataError, KeyError):
            existing_ids[key] = set()
    
    last_incident_id = max(existing_ids.get('incidentes', {0})) if existing_ids.get('incidentes') else 0

    # --- Paso 4: Procesar datos nuevos y prepararlos para apendizar ---
    new_rows = {key: [] for key in csv_files}
    processed_this_run = {
        'competiciones': set(), 'equipos': set(), 'jugadores': set()
    }

    for game in new_data:
        # 1. Partidos
        if game.get('game_id') and game['game_id'] not in existing_ids['partidos']:
            new_rows['partidos'].append({
                'partido_id': game.get('game_id'),
                'competicion_id': game.get('stage_id'),
                'fecha_inicio': game.get('start_time'),
                'estado': game.get('status'),
                'equipo_local_id': game.get('home_team_id'),
                'equipo_visitante_id': game.get('away_team_id'),
                'goles_local': game.get('home_score'),
                'goles_visitante': game.get('away_score'),
                'tarjetas_amarillas_local': game.get('home_yellow_cards'),
                'tarjetas_rojas_local': game.get('home_red_cards'),
                'tarjetas_amarillas_visitante': game.get('away_yellow_cards'),
                'tarjetas_rojas_visitante': game.get('away_red_cards'),
                'tiempo_transcurrido': game.get('elapsed')
            })

        # 2. Competiciones
        if game.get('stage_id') and game['stage_id'] not in existing_ids['competiciones'] and game['stage_id'] not in processed_this_run['competiciones']:
            new_rows['competiciones'].append({'competicion_id': game['stage_id'], 'nombre_competicion': 'Premier League'})
            processed_this_run['competiciones'].add(game['stage_id'])

        # 3. Equipos
        team_keys = [('home_team_id', 'home_team'), ('away_team_id', 'away_team')]
        for id_key, name_key in team_keys:
            if game.get(id_key) and game[id_key] not in existing_ids['equipos'] and game[id_key] not in processed_this_run['equipos']:
                new_rows['equipos'].append({'equipo_id': game[id_key], 'nombre_equipo': game[name_key]})
                processed_this_run['equipos'].add(game[id_key])

        # 4. Jugadores e Incidentes
        if game.get('incidents'):
            for incident in game['incidents']:
                # Jugadores
                player_keys = [('playerId', 'playerName'), ('participatingPlayerId', 'participatingPlayerName')]
                for id_key, name_key in player_keys:
                    if incident.get(id_key) and incident[id_key] not in existing_ids['jugadores'] and incident[id_key] not in processed_this_run['jugadores']:
                        new_rows['jugadores'].append({'jugador_id': incident[id_key], 'nombre_jugador': incident.get(name_key, 'N/A')})
                        processed_this_run['jugadores'].add(incident[id_key])
                
                # Incidentes (se asume que si el partido es nuevo, todos sus incidentes lo son)
                new_rows['incidentes'].append({
                    'partido_id': game['game_id'],
                    'minuto': incident.get('minute'),
                    'tipo': incident.get('type'),
                    'subtipo': incident.get('subType'),
                    'jugador_id': incident.get('playerId'),
                    'jugador_participante_id': incident.get('participatingPlayerId') or '',
                    'campo': incident.get('field'),
                    'periodo': incident.get('period')
                })

    # --- Paso 5: Apendizar los datos nuevos a los archivos CSV ---
    print("\nAñadiendo nuevos datos a los archivos CSV...")
    for key, rows in new_rows.items():
        if rows:
            file_path = csv_files[key]['name']
            is_new_file = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
            
            df_new = pd.DataFrame(rows).drop_duplicates()

            # Llenar NaNs en columnas que no son de ID para evitar problemas
            if key in ['equipos', 'jugadores']:
                 df_new = df_new.fillna({'nombre_equipo': 'N/A', 'nombre_jugador': 'N/A'})

            if key == 'incidentes':
                df_new.insert(0, 'incidente_id', range(last_incident_id + 1, last_incident_id + 1 + len(df_new)))
                df_new['jugador_participante_id'] = df_new['jugador_participante_id'].fillna('')


            print(f"  - Añadiendo {len(df_new)} fila(s) a '{file_path}'")
            df_new.to_csv(file_path, mode='a', header=is_new_file, index=False, encoding='utf-8')
        else:
            print(f"  - No hay datos nuevos para '{csv_files[key]['name']}'.")

    print("\n--- Proceso de apendizado finalizado con éxito. ---")

if __name__ == '__main__':
    append_new_data_from_json()