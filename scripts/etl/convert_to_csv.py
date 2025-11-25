import json
import csv

def convert_json_to_csv():
    """
    Reads the whoscored_data.json file, processes it, and creates
    five CSV files corresponding to the database tables.
    It converts participatingPlayerId=0 to NULL for database import.
    """
    try:
        with open('whoscored_data_february.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: whoscored_data_february.json not found.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from whoscored_data_february.json.")
        return

    # Sets to keep track of existing IDs to avoid duplicates
    existing_competitions = set()
    existing_teams = set()
    existing_players = set()

    # Lists to hold the data for each CSV
    competiciones = []
    equipos = []
    jugadores = []
    partidos = []
    incidentes = []

    for game in data:
        # 1. Competitions
        if game.get('stage_id') and game['stage_id'] not in existing_competitions:
            competiciones.append({
                'competicion_id': game['stage_id'],
                'nombre_competicion': 'Premier League'
            })
            existing_competitions.add(game['stage_id'])

        # 2. Teams
        if game.get('home_team_id') and game['home_team_id'] not in existing_teams:
            equipos.append({
                'equipo_id': game['home_team_id'],
                'nombre_equipo': game['home_team'],
                'codigo_pais': game.get('home_team_country_code'),
                'nombre_pais': game.get('home_team_country_name')
            })
            existing_teams.add(game['home_team_id'])
        
        if game.get('away_team_id') and game['away_team_id'] not in existing_teams:
            equipos.append({
                'equipo_id': game['away_team_id'],
                'nombre_equipo': game['away_team'],
                'codigo_pais': game.get('away_team_country_code'),
                'nombre_pais': game.get('away_team_country_name')
            })
            existing_teams.add(game['away_team_id'])

        # 3. Partidos
        partidos.append({
            'partido_id': game['game_id'],
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

        # 4. Incidents and Players
        if game.get('incidents'):
            for incident in game['incidents']:
                # Players
                if incident.get('playerId') and incident['playerId'] not in existing_players:
                    jugadores.append({
                        'jugador_id': incident['playerId'],
                        'nombre_jugador': incident['playerName']
                    })
                    existing_players.add(incident['playerId'])
                
                if incident.get('participatingPlayerId') and incident['participatingPlayerId'] not in existing_players:
                    jugadores.append({
                        'jugador_id': incident['participatingPlayerId'],
                        'nombre_jugador': incident.get('participatingPlayerName', 'N/A')
                    })
                    existing_players.add(incident['participatingPlayerId'])

                # Incidents
                participating_player_id = incident.get('participatingPlayerId')
                incidentes.append({
                    'partido_id': game['game_id'],
                    'minuto': incident.get('minute'),
                    'tipo': incident.get('type'),
                    'subtipo': incident.get('subType'),
                    'jugador_id': incident.get('playerId'),
                    'jugador_participante_id': participating_player_id if participating_player_id != 0 else '', # <-- ESTA ES LA CORRECCIÓN
                    'campo': incident.get('field'),
                    'periodo': incident.get('period')
                })

    # Write to CSV files
    try:
        if competiciones:
            with open('competiciones.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=competiciones[0].keys())
                writer.writeheader()
                writer.writerows(competiciones)
        
        if equipos:
            with open('equipos.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=equipos[0].keys())
                writer.writeheader()
                writer.writerows(equipos)

        if jugadores:
            with open('jugadores.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=jugadores[0].keys())
                writer.writeheader()
                writer.writerows(jugadores)

        if partidos:
            with open('partidos.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=partidos[0].keys())
                writer.writeheader()
                writer.writerows(partidos)

        if incidentes:
            with open('incidentes.csv', 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['incidente_id'] + list(incidentes[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for i, row in enumerate(incidentes):
                    row_with_id = {'incidente_id': i + 1, **row}
                    writer.writerow(row_with_id)

        print("Successfully created the following CSV files (v2):")
        print("- competiciones.csv, equipos.csv, jugadores.csv, partidos.csv, incidentes.csv")

    except IOError as e:
        print(f"Error writing to CSV file: {e}")
    except (IndexError, KeyError) as e:
        print(f"Warning: Could not process a file, likely due to empty data. Details: {e}")


if __name__ == '__main__':
    convert_json_to_csv()