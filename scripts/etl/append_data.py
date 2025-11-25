import pandas as pd
import json
import os

def append_data():
    # --- 1. Cargar datos existentes ---
    try:
        partidos_df = pd.read_csv('partidos.csv')
        competiciones_df = pd.read_csv('competiciones.csv')
        equipos_df = pd.read_csv('equipos.csv')
        incidentes_df = pd.read_csv('incidentes.csv')
        jugadores_df = pd.read_csv('jugadores.csv')
    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo {e.filename}. Asegúrate de que todos los CSVs existan.")
        return

    # Crear sets para búsqueda rápida de IDs existentes
    existing_partido_ids = set(partidos_df['partido_id']) if not partidos_df.empty else set()
    existing_equipo_nombres = set(equipos_df['nombre_equipo']) if not equipos_df.empty else set()
    existing_jugador_ids = set(jugadores_df['jugador_id']) if not jugadores_df.empty else set()

    
    # --- 2. Cargar nuevos datos desde JSON ---
    try:
        with open('nuevos_datos.json', 'r', encoding='utf-8') as f:
            nuevos_datos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error al cargar 'nuevos_datos.json': {e}")
        return

    # --- 3. Preparar listas para nuevos datos ---
    nuevos_partidos = []
    nuevos_equipos = []
    nuevos_jugadores = []
    nuevos_incidentes = []
    all_players_in_new_data = {} # Initialize dictionary for collecting new players

    # Obtener el máximo ID existente para generar nuevos
    max_equipo_id = equipos_df['equipo_id'].max() if not equipos_df.empty else 0
    max_jugador_id = jugadores_df['jugador_id'].max() if not jugadores_df.empty else 0
    max_incidente_id = incidentes_df['incidente_id'].max() if not incidentes_df.empty else 0

    # --- 4. Procesar cada partido del JSON ---
    for game in nuevos_datos:
        game_id = game.get('game_id')
        if game_id in existing_partido_ids:
            print(f"El partido con ID {game_id} ya existe. Omitiendo.")
            continue

        # --- Equipos ---
        home_team_name = game.get('home_team')
        away_team_name = game.get('away_team')
        
        home_team_id = None
        if home_team_name not in existing_equipo_nombres:
            max_equipo_id += 1
            home_team_id = max_equipo_id
            nuevos_equipos.append({'equipo_id': home_team_id, 'nombre_equipo': home_team_name})
            existing_equipo_nombres.add(home_team_name)
        else:
            home_team_id_series = equipos_df[equipos_df['nombre_equipo'] == home_team_name]['equipo_id']
            if not home_team_id_series.empty:
                home_team_id = home_team_id_series.iloc[0]
            else:
                for e in nuevos_equipos:
                    if e['nombre_equipo'] == home_team_name:
                        home_team_id = e['equipo_id']
                        break

        away_team_id = None
        if away_team_name not in existing_equipo_nombres:
            max_equipo_id += 1
            away_team_id = max_equipo_id
            nuevos_equipos.append({'equipo_id': away_team_id, 'nombre_equipo': away_team_name})
            existing_equipo_nombres.add(away_team_name)
        else:
            away_team_id_series = equipos_df[equipos_df['nombre_equipo'] == away_team_name]['equipo_id']
            if not away_team_id_series.empty:
                away_team_id = away_team_id_series.iloc[0]
            else:
                for e in nuevos_equipos:
                    if e['nombre_equipo'] == away_team_name:
                        away_team_id = e['equipo_id']
                        break

        # --- Partidos ---
        nuevos_partidos.append({
            'partido_id': game_id,
            'competicion_id': 23400,  # Asumiendo Premier League
            'fecha_inicio': game.get('start_time'),
            'estado': 6, # Asumiendo FT
            'equipo_local_id': home_team_id,
            'equipo_visitante_id': away_team_id,
            'goles_local': game.get('home_score'),
            'goles_visitante': game.get('away_score'),
            'tiempo_transcurrido': game.get('elapsed')
        })

        # Collect all unique players from incidents for this game
        for incident in game.get('incidents', []):
            json_player_id = incident.get('player_id')
            json_player_name = incident.get('player')
            if json_player_id is not None and pd.notna(json_player_id) and json_player_name is not None:
                if json_player_id not in all_players_in_new_data:
                    all_players_in_new_data[json_player_id] = json_player_name
            
            json_related_player_id = incident.get('related_player_id')
            json_related_player_name = incident.get('related_player') # Assuming 'related_player' field exists in JSON
            if json_related_player_id is not None and pd.notna(json_related_player_id) and json_related_player_name is not None:
                if json_related_player_id not in all_players_in_new_data:
                    all_players_in_new_data[json_related_player_id] = json_related_player_name

    # --- Collect new players for jugadores_df from all incidents ---
    for player_id, player_name in all_players_in_new_data.items():
        if player_id not in existing_jugador_ids:
            nuevos_jugadores.append({'jugador_id': player_id, 'nombre_jugador': player_name})
            existing_jugador_ids.add(player_id) # Add to existing_jugador_ids for future checks in this run

    # Reset max_incidente_id for this run as we re-iterate incidents
    # Obtener el máximo ID existente para generar nuevos
    max_incidente_id = incidentes_df['incidente_id'].max() if not incidentes_df.empty else 0


    # --- 4. Procesar cada partido del JSON (Second pass for incidents) ---
    for game in nuevos_datos:
        game_id = game.get('game_id')
        if game_id in existing_partido_ids:
            continue # Already processed, skip


        # --- Incidentes ---
        for incident in game.get('incidents', []):
            max_incidente_id += 1
            nuevos_incidentes.append({
                'incidente_id': max_incidente_id,
                'partido_id': game_id,
                'minuto': incident.get('minute'),
                'tipo': incident.get('type'),
                'subtipo': incident.get('outcome_type'),
                'jugador_id': incident.get('player_id'), # Use original player_id from JSON
                'jugador_participante_id': incident.get('related_player_id'), # Use original related_player_id from JSON
                'periodo': incident.get('period')
            })

    # --- 5. Añadir nuevos datos a los DataFrames y guardarlos ---
    if nuevos_partidos:
        partidos_df = pd.concat([partidos_df, pd.DataFrame(nuevos_partidos)], ignore_index=True)
        # Ensure integer columns are Int64 before saving
        for col in ['partido_id', 'competicion_id', 'estado', 'equipo_local_id', 'equipo_visitante_id', 'goles_local', 'goles_visitante']:
            if col in partidos_df.columns:
                partidos_df[col] = partidos_df[col].astype('Int64')
        partidos_df.to_csv('partidos.csv', index=False)
        print(f"Se añadieron {len(nuevos_partidos)} nuevos partidos.")

    if nuevos_equipos:
        equipos_df = pd.concat([equipos_df, pd.DataFrame(nuevos_equipos)], ignore_index=True)
        # Ensure integer columns are Int64 before saving
        for col in ['equipo_id']:
            if col in equipos_df.columns:
                equipos_df[col] = equipos_df[col].astype('Int64')
        equipos_df.to_csv('equipos.csv', index=False)
        print(f"Se añadieron {len(nuevos_equipos)} nuevos equipos.")

    if nuevos_jugadores:
        jugadores_df = pd.concat([jugadores_df, pd.DataFrame(nuevos_jugadores)], ignore_index=True)
        # Ensure integer columns are Int64 before saving
        for col in ['jugador_id']:
            if col in jugadores_df.columns:
                jugadores_df[col] = jugadores_df[col].astype('Int64')
        jugadores_df.to_csv('jugadores.csv', index=False)
        print(f"Se añadieron {len(nuevos_jugadores)} nuevos jugadores.")

    if nuevos_incidentes:
        incidentes_df = pd.concat([incidentes_df, pd.DataFrame(nuevos_incidentes)], ignore_index=True)
        # Ensure integer columns are Int64 before saving
        for col in ['incidente_id', 'partido_id', 'minuto', 'jugador_id', 'jugador_participante_id']:
            if col in incidentes_df.columns:
                incidentes_df[col] = incidentes_df[col].astype('Int64')
        incidentes_df.to_csv('incidentes.csv', index=False)
        print(f"Se añadieron {len(nuevos_incidentes)} nuevos incidentes.")

    print("\n--- Proceso de actualización de CSVs finalizado. ---")

if __name__ == "__main__":
    append_data()
