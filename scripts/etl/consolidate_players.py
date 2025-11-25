import json
import csv

def consolidate_players():
    """
    Reads both the January and February JSON data files, collects all unique
    players, and overwrites the main jugadores.csv with the complete list.
    """
    json_files = ['whoscored_data.json', 'whoscored_data_february.json', 'nuevos_datos.json']
    all_players = {}

    # Load existing players from jugadores.csv
    try:
        with open('jugadores.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_players[int(row['jugador_id'])] = row['nombre_jugador']
        print("Cargados jugadores existentes de 'jugadores.csv'.")
    except FileNotFoundError:
        print("jugadores.csv no encontrado. Se creará uno nuevo.")
    except Exception as e:
        print(f"Error al cargar jugadores existentes: {e}. Se procederá con una lista vacía.")

    print("Iniciando la consolidación de jugadores de todos los archivos JSON...")

    for file_name in json_files:
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"- Leyendo jugadores de {file_name}")
                for game in data:
                    if game.get('incidents'):
                        for incident in game['incidents']:
                            if incident.get('playerId') and incident['playerId'] != 0:
                                all_players[incident['playerId']] = incident['playerName']
                            if incident.get('participatingPlayerId') and incident['participatingPlayerId'] != 0:
                                all_players[incident['participatingPlayerId']] = incident.get('participatingPlayerName', 'N/A')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Advertencia: No se pudo leer el archivo {file_name}. Se omitirá. Error: {e}")
            continue

    if not all_players:
        print("No se encontraron jugadores para procesar.")
        return

    # Convertir el diccionario a una lista de diccionarios para el CSV
    player_list = [{'jugador_id': pid, 'nombre_jugador': name} for pid, name in all_players.items()]

    # Escribir la lista consolidada a jugadores.csv
    try:
        with open('jugadores.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['jugador_id', 'nombre_jugador'])
            writer.writeheader()
            writer.writerows(player_list)
        print(f"\n¡Éxito! Se ha sobrescrito 'jugadores.csv' con una lista consolidada de {len(player_list)} jugadores.")
    except IOError as e:
        print(f"Error al escribir en jugadores.csv: {e}")

if __name__ == "__main__":
    consolidate_players()
