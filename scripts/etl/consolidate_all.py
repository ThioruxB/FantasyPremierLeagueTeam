
import json
import csv

def consolidate_all_data():
    """
    Reads all specified JSON data files, consolidates all data for all tables,
    and overwrites the original CSV files with the complete, combined data.
    """
    json_files = ['whoscored_data.json', 'whoscored_data_february.json', 'whoscored_data_march.json', 'whoscored_data_april.json', 'whoscored_data_may.json', 'whoscored_data_august.json', 'whoscored_data_september.json', 'whoscored_data_october.json']
    
    all_competitions = {}
    all_teams = {}
    all_players = {}
    all_partidos = []
    all_incidentes = []

    print("Iniciando la consolidación completa de Enero y Febrero...")

    for file_name in json_files:
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"- Procesando {file_name}")
                for game in data:
                    # Competitions
                    if game.get('stage_id'):
                        all_competitions[game['stage_id']] = 'Premier League'

                    # Teams
                    if game.get('home_team_id'):
                        all_teams[game['home_team_id']] = {
                            'nombre_equipo': game['home_team'],
                            'codigo_pais': game.get('home_team_country_code'),
                            'nombre_pais': game.get('home_team_country_name')
                        }
                    if game.get('away_team_id'):
                        all_teams[game['away_team_id']] = {
                            'nombre_equipo': game['away_team'],
                            'codigo_pais': game.get('away_team_country_code'),
                            'nombre_pais': game.get('away_team_country_name')
                        }

                    # Partidos
                    all_partidos.append({
                        'partido_id': game['game_id'], 'competicion_id': game.get('stage_id'), 'fecha_inicio': game.get('start_time'),
                        'estado': game.get('status'), 'equipo_local_id': game.get('home_team_id'), 'equipo_visitante_id': game.get('away_team_id'),
                        'goles_local': game.get('home_score'), 'goles_visitante': game.get('away_score'), 'tarjetas_amarillas_local': game.get('home_yellow_cards'),
                        'tarjetas_rojas_local': game.get('home_red_cards'), 'tarjetas_amarillas_visitante': game.get('away_yellow_cards'),
                        'tarjetas_rojas_visitante': game.get('away_red_cards'), 'tiempo_transcurrido': game.get('elapsed')
                    })

                    # Incidents and Players
                    if game.get('incidents'):
                        for incident in game['incidents']:
                            if incident.get('playerId') and incident['playerId'] != 0:
                                all_players[incident['playerId']] = incident['playerName']
                            if incident.get('participatingPlayerId') and incident['participatingPlayerId'] != 0:
                                all_players[incident['participatingPlayerId']] = incident.get('participatingPlayerName', 'N/A')
                            
                            participating_player_id = incident.get('participatingPlayerId')
                            all_incidentes.append({
                                'partido_id': game['game_id'], 'minuto': incident.get('minute'), 'tipo': incident.get('type'), 'subtipo': incident.get('subType'),
                                'jugador_id': incident.get('playerId'), 'jugador_participante_id': participating_player_id if participating_player_id != 0 else '',
                                'campo': incident.get('field'), 'periodo': incident.get('period')
                            })
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Advertencia: No se pudo leer el archivo {file_name}. Se omitirá. Error: {e}")
            continue

    # --- Escribir los datos consolidados a los 5 CSVs originales ---
    try:
        # Competitions
        comp_list = [{'competicion_id': cid, 'nombre_competicion': name} for cid, name in all_competitions.items()]
        with open('competiciones.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['competicion_id', 'nombre_competicion'])
            writer.writeheader()
            writer.writerows(comp_list)

        # Equipos
        team_list = [{'equipo_id': tid, **data} for tid, data in all_teams.items()]
        with open('equipos.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['equipo_id', 'nombre_equipo', 'codigo_pais', 'nombre_pais'])
            writer.writeheader()
            writer.writerows(team_list)

        # Jugadores
        player_list = [{'jugador_id': pid, 'nombre_jugador': name} for pid, name in all_players.items()]
        with open('jugadores.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['jugador_id', 'nombre_jugador'])
            writer.writeheader()
            writer.writerows(player_list)

        # Partidos
        with open('partidos.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_partidos[0].keys())
            writer.writeheader()
            writer.writerows(all_partidos)

        # Incidentes
        with open('incidentes.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['incidente_id'] + list(all_incidentes[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, row in enumerate(all_incidentes):
                writer.writerow({'incidente_id': i + 1, **row})
        
        print("\n¡Éxito! Se han sobrescrito los 5 CSVs con los datos consolidados de Enero y Febrero.")
        print(f"Totales: {len(comp_list)} competiciones, {len(team_list)} equipos, {len(player_list)} jugadores, {len(all_partidos)} partidos, {len(all_incidentes)} incidentes.")

    except Exception as e:
        print(f"Ocurrió un error al escribir los archivos CSV: {e}")

if __name__ == "__main__":
    consolidate_all_data()
