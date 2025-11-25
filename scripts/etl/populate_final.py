import psycopg2
import csv
from urllib.parse import urlparse
from datetime import datetime
import os

print("--- INICIANDO PROCESO DE CARGA DEFINITIVO ---")

# --- Configuración ---
DATABASE_URL = "postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

SCHEMA_SQL = """
DROP TABLE IF EXISTS incidentes CASCADE;
DROP TABLE IF EXISTS partidos CASCADE;
DROP TABLE IF EXISTS jugadores CASCADE;
DROP TABLE IF EXISTS equipos CASCADE;
DROP TABLE IF EXISTS competiciones CASCADE;

CREATE TABLE competiciones (
    competicion_id INTEGER PRIMARY KEY,
    nombre_competicion VARCHAR(255)
);
CREATE TABLE equipos (
    equipo_id INTEGER PRIMARY KEY,
    nombre_equipo VARCHAR(255)
);
CREATE TABLE jugadores (
    jugador_id INTEGER PRIMARY KEY,
    nombre_jugador VARCHAR(255)
);
CREATE TABLE partidos (
    partido_id INTEGER PRIMARY KEY,
    competicion_id INTEGER,
    fecha_inicio TIMESTAMPTZ,
    estado VARCHAR(50),
    equipo_local_id INTEGER,
    equipo_visitante_id INTEGER,
    goles_local INTEGER,
    goles_visitante INTEGER,
    tarjetas_amarillas_local INTEGER,
    tarjetas_rojas_local INTEGER,
    tarjetas_amarillas_visitante INTEGER,
    tarjetas_rojas_visitante INTEGER,
    tiempo_transcurrido INTEGER
);
CREATE TABLE incidentes (
    incidente_id INTEGER PRIMARY KEY,
    partido_id INTEGER,
    minuto INTEGER,
    periodo INTEGER,
    tipo VARCHAR(100),
    subtipo VARCHAR(100),
    jugador_id INTEGER,
    jugador_participante_id INTEGER,
    campo VARCHAR(100)
);
"""

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"FATAL: No se pudo conectar a la base de datos: {e}")
        return None

def recreate_tables(conn):
    print("Paso 1: Eliminando y recreando tablas (modo permisivo)...")
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
        print("Tablas recreadas con éxito.")
        return True
    except Exception as e:
        print(f"FATAL: No se pudieron recrear las tablas: {e}")
        conn.rollback()
        return False

def process_and_load(conn, filename, table_name, insert_sql, row_processor):
    print(f"Paso {process_and_load.step}: Cargando datos de '{filename}' en tabla '{table_name}'...")
    process_and_load.step += 1
    
    if not os.path.exists(filename):
        print(f"  - ADVERTENCIA: Archivo '{filename}' no encontrado. Omitiendo.")
        return

    processed_count = 0
    error_count = 0
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        with conn.cursor() as cur:
            for i, row in enumerate(reader, 2): # i starts at 2 for line number
                if not row: continue
                try:
                    data = row_processor(row)
                    if data is None:
                        continue
                    cur.execute(insert_sql, data)
                    conn.commit()
                    processed_count += 1
                except Exception as e:
                    print(f"  - Error en línea {i} del archivo {filename}: {row} -> {e}")
                    error_count += 1
                    conn.rollback()
    print(f"  - Finalizado. Filas cargadas: {processed_count}, Errores: {error_count}")

process_and_load.step = 2 # Initialize step counter

# --- Procesadores de Fila ---
def process_competicion_row(row):
    return (int(row[0]), row[1])

def process_equipo_row(row):
    # Assuming a different structure for equipos.csv based on earlier errors
    # equipo_id,nombre_equipo,codigo_pais,nombre_pais
    # Let's just take the first two columns to be safe
    return (int(row[0]), row[1])

def process_jugador_row(row):
    return (int(row[0]), row[1])

def process_partido_row(row):
    tiempo_str = row[12] if len(row) > 12 else None
    return (
        int(row[0]), int(row[1]) if row[1] else None,
        datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S') if row[2] else None,
        row[3] or None, int(row[4]) if row[4] else None, int(row[5]) if row[5] else None,
        int(row[6]) if row[6] else None, int(row[7]) if row[7] else None,
        int(row[8]) if row[8] else None, int(row[9]) if row[9] else None,
        int(row[10]) if row[10] else None, int(row[11]) if row[11] else None,
        int(tiempo_str) if tiempo_str and tiempo_str.strip().isdigit() else None
    )

def process_incidente_row(row):
    periodo_map = {'FirstHalf': 1, 'SecondHalf': 2, 'PostGame': 3, 'PreMatch': 0, 'PenaltyShootout': 4, 'Start': 1}
    periodo_val = None
    if len(row) > 8 and row[8]:
        cleaned_val = row[8].strip()
        if cleaned_val in periodo_map:
            periodo_val = periodo_map[cleaned_val]
        else:
            # If it's a digit string, convert it. Otherwise, None.
            periodo_val = int(cleaned_val) if cleaned_val.isdigit() else None
            if cleaned_val not in periodo_map and not cleaned_val.isdigit():
                 print(f"  - AVISO: Valor de periodo no mapeado '{row[8]}' en fila, se insertará como NULL.")

    return (
        int(row[0]), int(row[1]) if row[1] else None, int(row[2]) if row[2] else None,
        periodo_val, row[3] or None, row[4] or None,
        int(row[5]) if row[5] else None,
        int(row[6]) if len(row) > 6 and row[6] else None,
        row[7] if len(row) > 7 else None
    )

def main():
    conn = get_db_connection()
    if conn:
        try:
            if not recreate_tables(conn):
                return # Stop if tables can't be created

            # Definir SQLs de inserción
            sql_competiciones = "INSERT INTO competiciones (competicion_id, nombre_competicion) VALUES (%s, %s) ON CONFLICT (competicion_id) DO NOTHING"
            sql_equipos = "INSERT INTO equipos (equipo_id, nombre_equipo) VALUES (%s, %s) ON CONFLICT (equipo_id) DO NOTHING"
            sql_jugadores = "INSERT INTO jugadores (jugador_id, nombre_jugador) VALUES (%s, %s) ON CONFLICT (jugador_id) DO NOTHING"
            sql_partidos = """INSERT INTO partidos (partido_id, competicion_id, fecha_inicio, estado, equipo_local_id, equipo_visitante_id, goles_local, goles_visitante, tarjetas_amarillas_local, tarjetas_rojas_local, tarjetas_amarillas_visitante, tarjetas_rojas_visitante, tiempo_transcurrido) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (partido_id) DO NOTHING"""
            sql_incidentes = """INSERT INTO incidentes (incidente_id, partido_id, minuto, periodo, tipo, subtipo, jugador_id, jugador_participante_id, campo) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (incidente_id) DO NOTHING"""

            # Procesar archivos
            process_and_load(conn, 'competiciones.csv', 'competiciones', sql_competiciones, process_competicion_row)
            process_and_load(conn, 'equipos.csv', 'equipos', sql_equipos, process_equipo_row)
            process_and_load(conn, 'jugadores.csv', 'jugadores', sql_jugadores, process_jugador_row)
            process_and_load(conn, 'partidos.csv', 'partidos', sql_partidos, process_partido_row)
            process_and_load(conn, 'incidentes.csv', 'incidentes', sql_incidentes, process_incidente_row)

        finally:
            conn.close()
            print("\n--- PROCESO FINALIZADO ---")

if __name__ == "__main__":
    main()
