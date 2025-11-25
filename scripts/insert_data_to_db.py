import pandas as pd
import psycopg2
from psycopg2 import extras
import json
import re
import ast

# Database connection string
DATABASE_URL = "postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def find_script_content_recursive(node):
    """Recursively searches for the script content in the JSON DOM."""
    if isinstance(node, dict):
        if node.get('tag') == 'script' and node.get('children'):
            for child in node['children']:
                if isinstance(child, dict) and 'text' in child:
                    if 'require.config.params["args"]' in child['text']:
                        return child['text']
        if node.get('children'):
            for child in node['children']:
                result = find_script_content_recursive(child)
                if result:
                    return result
    elif isinstance(node, list):
        for item in node:
            result = find_script_content_recursive(item)
            if result:
                return result
    return None

def extract_data_from_json_dom(json_dom_path):
    """Reads a JSON DOM representation and extracts the JavaScript object string."""
    try:
        with open(json_dom_path, 'r', encoding='utf-8') as f:
            dom_data = json.load(f)
        print(f"DOM JSON cargado exitosamente desde {json_dom_path}")
    except FileNotFoundError:
        print(f"Error: El archivo {json_dom_path} no fue encontrado.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON DOM desde {json_dom_path}: {e}")
        return None
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo JSON DOM: {e}")
        return None

    script_tag_content = find_script_content_recursive(dom_data)

    if not script_tag_content:
        print("Error: No se encontró el contenido del script con 'require.config.params[\"args\"]' en el JSON DOM.")
        return None

    # Apply the same cleaning and parsing logic as before
    try:
        start_index = script_tag_content.index('require.config.params["args"] = {')
        end_index = script_tag_content.rfind('}') + 1
        data_txt = script_tag_content[start_index:end_index]
        data_txt = data_txt.split('=', 1)[1].strip()

        data_txt = re.sub(r'([{\s,])(\w+)(\s*:)', r'\1"\2"\3', data_txt)
        data_txt = data_txt.replace('true', 'True').replace('false', 'False')
        data_txt = data_txt.replace('"timeStamp":"2025-10-04 "17":13:13"', '"timeStamp":"2025-10-04T17:13:13"')
        data_txt = data_txt.replace('"timeStamp":"2025-10-06 "00":11:07"', '"timeStamp":"2025-10-06T00:11:07"')
        
        data = ast.literal_eval(data_txt)
        return data
    except (ValueError, SyntaxError) as e:
        print(f"Error al procesar el contenido del script extraído del JSON DOM: {e}")
        return None

def extract_data_from_dict(data):
    # load data from json
    event_types_json = data["matchCentreEventTypeJson"]
    formation_mappings = data["formationIdNameMappings"]
    events_dict = data["matchCentreData"]["events"]
    teams_dict = {data["matchCentreData"]['home']['teamId']: data["matchCentreData"]['home']['name'],
                  data["matchCentreData"]['away']['teamId']: data["matchCentreData"]['away']['name']}
    players_dict = data["matchCentreData"]["playerIdNameDictionary"]
    # create players dataframe
    players_home_df = pd.DataFrame(data["matchCentreData"]['home']['players'])
    players_home_df["teamId"] = data["matchCentreData"]['home']['teamId']
    players_away_df = pd.DataFrame(data["matchCentreData"]['away']['players'])
    players_away_df["teamId"] = data["matchCentreData"]['away']['teamId']
    players_df = pd.concat([players_home_df, players_away_df])
    players_ids = data["matchCentreData"]["playerIdNameDictionary"]
    return events_dict, players_df, teams_dict

def connect_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Conexión a la base de datos exitosa.")
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def create_tables(conn):
    """Crea las tablas si no existen."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS equipos (
                id_equipo BIGINT PRIMARY KEY,
                nombre_equipo VARCHAR(255) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS jugadores (
                id_jugador BIGINT PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                numero_camiseta INTEGER,
                posicion VARCHAR(50),
                altura INTEGER,
                peso INTEGER,
                edad INTEGER,
                es_titular BOOLEAN,
                es_hombre_del_partido BOOLEAN,
                campo VARCHAR(50),
                id_equipo BIGINT NOT NULL,
                FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo)
            );

            CREATE TABLE IF NOT EXISTS partidos (
                id_partido BIGINT PRIMARY KEY,
                id_equipo_local BIGINT NOT NULL,
                id_equipo_visitante BIGINT NOT NULL,
                marcador VARCHAR(10),
                marcador_medio_tiempo VARCHAR(10),
                marcador_tiempo_completo VARCHAR(10),
                tiempo_transcurrido VARCHAR(50),
                hora_inicio TIMESTAMP,
                fecha_inicio DATE,
                asistencia INTEGER,
                nombre_estadio VARCHAR(255),
                nombre_arbitro VARCHAR(255),
                apellido_arbitro VARCHAR(255),
                codigo_clima VARCHAR(50),
                FOREIGN KEY (id_equipo_local) REFERENCES equipos(id_equipo),
                FOREIGN KEY (id_equipo_visitante) REFERENCES equipos(id_equipo)
            );

            CREATE TABLE IF NOT EXISTS eventos (
                id_evento BIGINT PRIMARY KEY,
                id_partido BIGINT NOT NULL,
                minuto INTEGER,
                segundo INTEGER,
                id_equipo BIGINT NOT NULL,
                id_jugador BIGINT,
                x NUMERIC(5,2),
                y NUMERIC(5,2),
                minuto_expandido INTEGER,
                periodo VARCHAR(50),
                tipo VARCHAR(50),
                tipo_resultado VARCHAR(50),
                calificadores TEXT,
                tipos_eventos_satisfechos TEXT,
                es_toque BOOLEAN,
                fin_x NUMERIC(5,2),
                fin_y NUMERIC(5,2),
                id_evento_relacionado BIGINT,
                id_jugador_relacionado BIGINT,
                x_bloqueado NUMERIC(5,2),
                y_bloqueado NUMERIC(5,2),
                z_boca_porteria NUMERIC(5,2),
                y_boca_porteria NUMERIC(5,2),
                es_disparo BOOLEAN,
                es_gol BOOLEAN,
                tipo_tarjeta VARCHAR(50),
                FOREIGN KEY (id_partido) REFERENCES partidos(id_partido),
                FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo),
                FOREIGN KEY (id_jugador) REFERENCES jugadores(id_jugador),
                FOREIGN KEY (id_evento_relacionado) REFERENCES eventos(id_evento),
                FOREIGN KEY (id_jugador_relacionado) REFERENCES jugadores(id_jugador)
            );

            CREATE TABLE IF NOT EXISTS formaciones (
                id_formacion BIGSERIAL PRIMARY KEY,
                id_partido BIGINT NOT NULL,
                id_equipo BIGINT NOT NULL,
                nombre_formacion VARCHAR(50),
                id_jugador_capitan BIGINT,
                periodo VARCHAR(50),
                minuto_inicio_expandido INTEGER,
                minuto_fin_expandido INTEGER,
                numeros_camiseta TEXT,
                slots_formacion TEXT,
                ids_jugadores TEXT,
                posiciones_formacion TEXT,
                FOREIGN KEY (id_partido) REFERENCES partidos(id_partido),
                FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo),
                FOREIGN KEY (id_jugador_capitan) REFERENCES jugadores(id_jugador)
            );
        """)
        conn.commit()
        print("Tablas verificadas/creadas exitosamente.")

def insert_equipos(conn, id_equipo, nombre_equipo):
    """Inserta un equipo si no existe."""
    with conn.cursor() as cur:
        cur.execute("INSERT INTO equipos (id_equipo, nombre_equipo) VALUES (%s, %s) ON CONFLICT (id_equipo) DO NOTHING;",
                    (id_equipo, nombre_equipo))
        conn.commit()

def insert_jugadores(conn, player_df):
    """Inserta jugadores, actualizando si ya existen."""
    with conn.cursor() as cur:
        for index, row in player_df.iterrows():
            team_id = row['id_equipo'] if pd.notna(row['id_equipo']) else None
            if team_id is None:
                print(f"Skipping player {row['id_jugador']} due to missing teamId.")
                continue

            # Convert es_titular to proper boolean or None
            es_titular_val = None
            if pd.notna(row['es_titular']):
                if isinstance(row['es_titular'], str):
                    es_titular_val = True if row['es_titular'].lower() == 'true' else False
                else:
                    es_titular_val = bool(row['es_titular'])
            
            # Convert es_hombre_del_partido to proper boolean or None
            es_hombre_del_partido_val = None
            if pd.notna(row['es_hombre_del_partido']):
                if isinstance(row['es_hombre_del_partido'], str):
                    es_hombre_del_partido_val = True if row['es_hombre_del_partido'].lower() == 'true' else False
                else:
                    es_hombre_del_partido_val = bool(row['es_hombre_del_partido'])

            cur.execute("""
                INSERT INTO jugadores (id_jugador, nombre, numero_camiseta, posicion, altura, peso, edad, es_titular, es_hombre_del_partido, campo, id_equipo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_jugador) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    numero_camiseta = EXCLUDED.numero_camiseta,
                    posicion = EXCLUDED.posicion,
                    altura = EXCLUDED.altura,
                    peso = EXCLUDED.peso,
                    edad = EXCLUDED.edad,
                    es_titular = EXCLUDED.es_titular,
                    es_hombre_del_partido = EXCLUDED.es_hombre_del_partido,
                    campo = EXCLUDED.campo,
                    id_equipo = EXCLUDED.id_equipo;
            """, (
                row['id_jugador'], row['name'], row['numero_camiseta'], row['position'],
                row['height'], row['weight'], row['age'], es_titular_val,
                es_hombre_del_partido_val, row['field'], team_id
            ))
        conn.commit()

def insert_partidos(conn, metadata):
    """Inserta un partido."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO partidos (id_partido, id_equipo_local, id_equipo_visitante, marcador, marcador_medio_tiempo,
                                  marcador_tiempo_completo, tiempo_transcurrido, hora_inicio, fecha_inicio,
                                  asistencia, nombre_estadio, nombre_arbitro, apellido_arbitro, codigo_clima)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_partido) DO NOTHING;
        """, (
            metadata['id_partido'],
            metadata['id_equipo_local'],
            metadata['id_equipo_visitante'],
            metadata['marcador'],
            metadata['marcador_medio_tiempo'],
            metadata['marcador_tiempo_completo'],
            metadata['tiempo_transcurrido'],
            metadata['hora_inicio'],
            metadata['fecha_inicio'],
            metadata['asistencia'],
            metadata['nombre_estadio'],
            metadata['nombre_arbitro'],
            metadata['apellido_arbitro'],
            metadata['codigo_clima']
        ))
        conn.commit()

def insert_formaciones(conn, id_partido, id_equipo, formaciones_data):
    """Inserta las formaciones para un equipo en un partido."""
    with conn.cursor() as cur:
        records = []
        for formation in formaciones_data:
            # Convert list/dict fields to JSON strings for TEXT columns
            jersey_numbers_val = None
            if formation.get('jerseyNumbers') is not None:
                try:
                    jersey_numbers_val = json.dumps(formation.get('jerseyNumbers'))
                except TypeError:
                    jersey_numbers_val = None

            slots_formacion_val = None
            if formation.get('formationSlots') is not None:
                try:
                    slots_formacion_val = json.dumps(formation.get('formationSlots'))
                except TypeError:
                    slots_formacion_val = None

            ids_jugadores_val = None
            if formation.get('playerIds') is not None:
                try:
                    ids_jugadores_val = json.dumps(formation.get('playerIds'))
                except TypeError:
                    ids_jugadores_val = None

            posiciones_formacion_val = None
            if formation.get('formationPositions') is not None:
                try:
                    posiciones_formacion_val = json.dumps(formation.get('formationPositions'))
                except TypeError:
                    posiciones_formacion_val = None

            records.append((
                id_partido,
                id_equipo,
                formation.get('formationName'),
                            formation.get('captainPlayerId'),
                            formation.get('period') if isinstance(formation.get('period'), dict) and formation.get('period').get('displayName') else None,
                            formation.get('startMinuteExpanded'),                formation.get('endMinuteExpanded'),
                jersey_numbers_val,
                slots_formacion_val,
                ids_jugadores_val,
                posiciones_formacion_val
            ))
        
        insert_query = """
            INSERT INTO formaciones (id_partido, id_equipo, nombre_formacion, id_jugador_capitan, periodo,
                                         minuto_inicio_expandido, minuto_fin_expandido, numeros_camiseta,
                                         slots_formacion, ids_jugadores, posiciones_formacion)
            VALUES %s;
        """
        extras.execute_values(cur, insert_query, records, page_size=1000)
        conn.commit()

def insert_eventos(conn, event_df):
    """Inserta los eventos del partido uno por uno para depuración."""
    with conn.cursor() as cur:
        for index, row in event_df.iterrows():
            id_evento_relacionado = row.get('id_evento_relacionado')
            if pd.isna(id_evento_relacionado):
                id_evento_relacionado = None

            id_jugador_relacionado = row.get('id_jugador_relacionado')
            if pd.isna(id_jugador_relacionado):
                id_jugador_relacionado = None

            es_toque_val = None if pd.isna(row.get('es_toque')) else bool(row.get('es_toque'))
            es_disparo_val = None if pd.isna(row.get('es_disparo')) else bool(row.get('es_disparo'))
            es_gol_val = None if pd.isna(row.get('es_gol')) else bool(row.get('es_gol'))

            id_evento_val = None if pd.isna(row.get('id_evento')) else int(row.get('id_evento'))
            id_partido_val = None if pd.isna(row.get('id_partido')) else int(row.get('id_partido'))
            id_equipo_val = None if pd.isna(row.get('id_equipo')) else int(row.get('id_equipo'))
            id_jugador_val = None if pd.isna(row.get('id_jugador')) else int(row.get('id_jugador'))
            id_evento_relacionado_val = None if pd.isna(id_evento_relacionado) else int(id_evento_relacionado)
            id_jugador_relacionado_val = None if pd.isna(id_jugador_relacionado) else int(id_jugador_relacionado)

            es_toque_val = None if pd.isna(row.get('es_toque')) else bool(row.get('es_toque'))
            es_disparo_val = None if pd.isna(row.get('es_disparo')) else bool(row.get('es_disparo'))
            es_gol_val = None if pd.isna(row.get('es_gol')) else bool(row.get('es_gol'))

            record = (
                id_evento_val,
                id_partido_val,
                row.get('minuto'),
                row.get('segundo'),
                id_equipo_val,
                id_jugador_val,
                row.get('x'),
                row.get('y'),
                row.get('minuto_expandido'),
                row.get('periodo'),
                row.get('tipo'),
                row.get('tipo_resultado'),
                json.dumps(row.get('calificadores')),
                json.dumps(row.get('tipos_eventos_satisfechos')),
                es_toque_val,
                row.get('fin_x'),
                row.get('fin_y'),
                row.get('x_bloqueado'),
                row.get('y_bloqueado'),
                row.get('z_boca_porteria'),
                row.get('y_boca_porteria'),
                es_disparo_val,
                es_gol_val,
                row.get('tipo_tarjeta'),
                id_evento_relacionado_val,
                id_jugador_relacionado_val
            )
            
            try:
                print(f"Inserting record: {record}")
                cur.execute("""
                    INSERT INTO eventos (id_evento, id_partido, minuto, segundo, id_equipo, id_jugador, x, y, minuto_expandido, periodo, tipo, tipo_resultado, calificadores, tipos_eventos_satisfechos, es_toque, fin_x, fin_y, x_bloqueado, y_bloqueado, z_boca_porteria, y_boca_porteria, es_disparo, es_gol, tipo_tarjeta, id_evento_relacionado, id_jugador_relacionado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id_evento) DO NOTHING;
                """, record)
            except Exception as e:
                print(f"Error inserting event {row.get('id_evento')}: {e}")
                conn.rollback()
                # We are not re-raising the exception to see all errors
    conn.commit()


def main():
    json_dom_file_path = 'D:\\ConectPremier\\pag3.json'
    
    # 1. Extract data from JSON DOM
    data = extract_data_from_json_dom(json_dom_file_path)
    if data is None:
        print("Error: No se pudieron extraer los datos esenciales del partido del JSON DOM.")
        return

    # Extract events_dict and players_df directly from the parsed data
    events_dict, raw_players_df, teams_dict = extract_data_from_dict(data)

    # Create event_df and player_df from the extracted data
    event_df = pd.DataFrame(events_dict)
    player_df = pd.DataFrame(raw_players_df)

    # Create a mapping from eventId to id and update relatedEventId
    if 'eventId' in event_df.columns and 'id' in event_df.columns:
        event_id_map = pd.Series(event_df.id.values, index=event_df.eventId).to_dict()
        if 'relatedEventId' in event_df.columns:
            event_df['relatedEventId'] = event_df['relatedEventId'].apply(lambda x: event_id_map.get(x) if pd.notna(x) else None)

    # Add matchId to event_df for foreign key
    event_df['id_partido'] = data.get('matchId')
    # Rename columns to match database schema
    event_df.rename(columns={'id': 'id_evento', 'teamId': 'id_equipo', 'playerId': 'id_jugador',
                             'expandedMinute': 'minuto_expandido', 'period': 'periodo', 'type': 'tipo',
                             'outcomeType': 'tipo_resultado',
                             'qualifiers': 'calificadores', 'satisfiedEventsTypes': 'tipos_eventos_satisfechos',
                             'isTouch': 'es_toque', 'endX': 'fin_x', 'endY': 'fin_y',
                             'relatedEventId': 'id_evento_relacionado', 'relatedPlayerId': 'id_jugador_relacionado',
                             'blockedX': 'x_bloqueado', 'blockedY': 'y_bloqueado', 'goalMouthZ': 'z_boca_porteria',
                             'goalMouthY': 'y_boca_porteria', 'isShot': 'es_disparo', 'isGoal': 'es_gol',
                             'cardType': 'tipo_tarjeta'}, inplace=True)

    # Sort events by id_evento to ensure correct insertion order
    event_df.sort_values(by='id_evento', inplace=True)

    # Flatten dictionary columns
    if 'periodo' in event_df.columns:
        event_df['periodo'] = event_df['periodo'].apply(lambda x: x.get('displayName') if isinstance(x, dict) else None)
    if 'tipo' in event_df.columns:
        event_df['tipo'] = event_df['tipo'].apply(lambda x: x.get('displayName') if isinstance(x, dict) else None)
    if 'tipo_resultado' in event_df.columns:
        event_df['tipo_resultado'] = event_df['tipo_resultado'].apply(lambda x: x.get('displayName') if isinstance(x, dict) else None)
    if 'tipo_tarjeta' in event_df.columns:
        event_df['tipo_tarjeta'] = event_df['tipo_tarjeta'].apply(lambda x: x.get('displayName') if isinstance(x, dict) else None)

    player_df.rename(columns={'playerId': 'id_jugador', 'shirtNo': 'numero_camiseta', 'isFirstEleven': 'es_titular',
                              'isManOfTheMatch': 'es_hombre_del_partido', 'teamId': 'id_equipo'}, inplace=True)


    # --- DATA INTEGRITY CHECKS ---
    print("\n--- Verificando la integridad de los datos de eventos ---")

    # Check for missing players
    jugadores_existentes = set(player_df['id_jugador'])
    jugadores_en_eventos = set(event_df['id_jugador'].dropna())
    jugadores_faltantes = jugadores_en_eventos - jugadores_existentes
    if jugadores_faltantes:
        print(f"Error: Se encontraron {len(jugadores_faltantes)} jugadores en eventos que no existen en la tabla de jugadores: {jugadores_faltantes}")

    # Check for missing teams
    equipos_existentes = set(teams_dict.keys())
    equipos_en_eventos = set(event_df['id_equipo'].dropna())
    equipos_faltantes = equipos_en_eventos - equipos_existentes
    if equipos_faltantes:
        print(f"Error: Se encontraron {len(equipos_faltantes)} equipos en eventos que no existen en la tabla de equipos: {equipos_faltantes}")

    # Check for missing related players
    jugadores_relacionados_en_eventos = set(event_df['id_jugador_relacionado'].dropna())
    jugadores_relacionados_faltantes = jugadores_relacionados_en_eventos - jugadores_existentes
    if jugadores_relacionados_faltantes:
        print(f"Error: Se encontraron {len(jugadores_relacionados_faltantes)} jugadores relacionados en eventos que no existen en la tabla de jugadores: {jugadores_relacionados_faltantes}")

    # Check for missing related events
    eventos_existentes = set(event_df['id_evento'])
    eventos_relacionados_en_eventos = set(event_df['id_evento_relacionado'].dropna())
    eventos_relacionados_faltantes = eventos_relacionados_en_eventos - eventos_existentes
    if eventos_relacionados_faltantes:
        print(f"Error: Se encontraron {len(eventos_relacionados_faltantes)} eventos relacionados que no existen en la lista de eventos: {eventos_relacionados_faltantes}")

    print("--- Fin de la verificación de integridad ---\n")
    # --- END DATA INTEGRITY CHECKS ---

    conn = None
    try:
        conn = connect_db()
        if conn:
            create_tables(conn) # Create tables if they don't exist

            # Insertar equipos
            insert_equipos(conn, data['matchCentreData']['home']['teamId'], data['matchCentreData']['home']['name'])
            insert_equipos(conn, data['matchCentreData']['away']['teamId'], data['matchCentreData']['away']['name'])
            print("Equipos insertados/actualizados.")

            # Insertar jugadores
            insert_jugadores(conn, player_df)
            print("Jugadores insertados/actualizados.")

            # Insertar partido
            metadata = {
                'id_partido': data.get('matchId'),
                'id_equipo_local': data['matchCentreData']['home']['teamId'],
                'id_equipo_visitante': data['matchCentreData']['away']['teamId'],
                'marcador': data['matchCentreData'].get('score'),
                'marcador_medio_tiempo': data['matchCentreData'].get('htScore'),
                'marcador_tiempo_completo': data['matchCentreData'].get('ftScore'),
                'tiempo_transcurrido': data['matchCentreData'].get('elapsed'),
                'hora_inicio': data['matchCentreData'].get('startTime'),
                'fecha_inicio': data['matchCentreData'].get('startDate'),
                'asistencia': data['matchCentreData'].get('attendance'),
                'nombre_estadio': data['matchCentreData'].get('venueName'),
                'nombre_arbitro': data['matchCentreData']['referee'].get('firstName'),
                'apellido_arbitro': data['matchCentreData']['referee'].get('lastName'),
                'codigo_clima': data['matchCentreData'].get('weatherCode')
            }
            insert_partidos(conn, metadata)
            print("Partido insertado/actualizado.")

            # Insertar formaciones
            if data['matchCentreData']['home'].get('formations'):
                insert_formaciones(conn, metadata['id_partido'], metadata['id_equipo_local'], data['matchCentreData']['home']['formations'])
                print("Formaciones locales insertadas.")
            if data['matchCentreData']['away'].get('formations'):
                insert_formaciones(conn, metadata['id_partido'], metadata['id_equipo_visitante'], data['matchCentreData']['away']['formations'])
                print("Formaciones visitantes insertadas.")

            # Insertar eventos
            insert_eventos(conn, event_df)
            print("Eventos insertados.")

            print(f"Datos del partido {metadata.get('id_partido')} insertados exitosamente en la base de datos.")

    except Exception as e:
        print(f"Error durante la inserción de datos: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == '__main__':
    main()