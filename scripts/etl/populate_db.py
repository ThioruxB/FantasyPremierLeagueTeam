import psycopg2
import csv
from urllib.parse import urlparse
from datetime import datetime

# --- Configuración de la Base de Datos ---
DATABASE_URL = "postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# --- Esquema SQL para crear las tablas ---
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS competiciones (
    competicion_id INTEGER PRIMARY KEY,
    nombre_competicion VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS equipos (
    equipo_id INTEGER PRIMARY KEY,
    nombre_equipo VARCHAR(255) NOT NULL,
    codigo_pais VARCHAR(10),
    nombre_pais VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS jugadores (
    jugador_id INTEGER PRIMARY KEY,
    nombre_jugador VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS partidos (
    partido_id INTEGER PRIMARY KEY,
    competicion_id INTEGER,
    fecha_inicio TIMESTAMPTZ,
    estado VARCHAR(50),
    equipo_local_id INTEGER,
    equipo_visitante_id INTEGER,
    goles_local INTEGER DEFAULT 0,
    goles_visitante INTEGER DEFAULT 0,
    tarjetas_amarillas_local INTEGER DEFAULT 0,
    tarjetas_rojas_local INTEGER DEFAULT 0,
    tarjetas_amarillas_visitante INTEGER DEFAULT 0,
    tarjetas_rojas_visitante INTEGER DEFAULT 0,
    tiempo_transcurrido INTEGER,
    CONSTRAINT fk_competicion FOREIGN KEY(competicion_id) REFERENCES competiciones(competicion_id) ON DELETE SET NULL,
    CONSTRAINT fk_equipo_local FOREIGN KEY(equipo_local_id) REFERENCES equipos(equipo_id) ON DELETE SET NULL,
    CONSTRAINT fk_equipo_visitante FOREIGN KEY(equipo_visitante_id) REFERENCES equipos(equipo_id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS incidentes (
    incidente_id INTEGER PRIMARY KEY,
    partido_id INTEGER,
    minuto INTEGER,
    periodo INTEGER,
    tipo VARCHAR(100),
    subtipo VARCHAR(100),
    jugador_id INTEGER,
    jugador_participante_id INTEGER,
    campo VARCHAR(100),
    CONSTRAINT fk_partido FOREIGN KEY(partido_id) REFERENCES partidos(partido_id) ON DELETE CASCADE,
    CONSTRAINT fk_jugador FOREIGN KEY(jugador_id) REFERENCES jugadores(jugador_id) ON DELETE SET NULL,
    CONSTRAINT fk_jugador_participante FOREIGN KEY(jugador_participante_id) REFERENCES jugadores(jugador_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_partidos_fecha ON partidos(fecha_inicio);
CREATE INDEX IF NOT EXISTS idx_incidentes_partido_id ON incidentes(partido_id);
"""

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def create_tables(conn):
    """Ejecuta el esquema SQL para crear las tablas."""
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
        print("Tablas creadas o ya existentes.")
    except Exception as e:
        print(f"Error al crear tablas: {e}")
        conn.rollback()

def process_file(conn, file_name, table_name, insert_sql, row_processor):
    """Función genérica para procesar un archivo CSV e insertar en la BD fila por fila."""
    print(f"Procesando archivo '{file_name}' para la tabla '{table_name}'...")
    processed_count = 0
    error_count = 0
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Saltar la cabecera
            with conn.cursor() as cur:
                for row in reader:
                    if not row: continue
                    try:
                        data = row_processor(row)
                        if data is None: # El procesador puede decidir omitir la fila
                            continue
                        cur.execute(insert_sql, data)
                        conn.commit()
                        processed_count += 1
                    except (ValueError, IndexError) as e:
                        print(f"  - Error de formato en fila: {row} -> {e}")
                        error_count += 1
                        conn.rollback()
                    except psycopg2.Error as e:
                        # Errores de BD (ej. clave foránea)
                        print(f"  - Error de BD en fila: {row} -> {e.pgerror}")
                        error_count += 1
                        conn.rollback()
        print(f"Finalizado '{file_name}'. Filas procesadas: {processed_count}, Errores: {error_count}\n")
    except FileNotFoundError:
        print(f"Archivo {file_name} no encontrado.")
    except Exception as e:
        print(f"Error mayor al procesar el archivo {file_name}: {e}")
        conn.rollback()

# --- Procesadores de Fila ---

def process_competicion_row(row):
    return (int(row[0]), row[1])

def process_equipo_row(row):
    return (int(row[0]), row[1], row[2], row[3])

def process_jugador_row(row):
    return (int(row[0]), row[1])

def process_partido_row(row):
    if not (len(row) > 5 and row[4] and row[5]):
        print(f"  - AVISO: Omitiendo partido {row[0]} por falta de ID de equipo.")
        return None
    
    partido_id = int(row[0])
    competicion_id = int(row[1])
    fecha_inicio = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S') if row[2] else None
    estado = row[3] or None
    equipo_local_id = int(row[4])
    equipo_visitante_id = int(row[5])
    goles_local = int(row[6]) if row[6] else 0
    goles_visitante = int(row[7]) if row[7] else 0
    tarjetas_amarillas_local = int(row[8]) if row[8] else 0
    tarjetas_rojas_local = int(row[9]) if row[9] else 0
    tarjetas_amarillas_visitante = int(row[10]) if row[10] else 0
    tarjetas_rojas_visitante = int(row[11]) if row[11] else 0
    tiempo_str = row[12] if len(row) > 12 else None
    tiempo_transcurrido = int(tiempo_str) if tiempo_str and tiempo_str.isdigit() else None
    
    return (partido_id, competicion_id, fecha_inicio, estado, equipo_local_id, equipo_visitante_id,
            goles_local, goles_visitante, tarjetas_amarillas_local, tarjetas_rojas_local,
            tarjetas_amarillas_visitante, tarjetas_rojas_visitante, tiempo_transcurrido)

def process_incidente_row(row):
    periodo_map = {'FirstHalf': 1, 'SecondHalf': 2, 'PostGame': 3, 'PreMatch': 0, 'PenaltyShootout': 4}
    periodo_str = row[8] if len(row) > 8 else None
    periodo = periodo_map.get(periodo_str)

    return (
        int(row[0]), int(row[1]), int(row[2]) if row[2] else None, periodo,
        row[3] or None, row[4] or None, int(row[5]) if row[5] else None,
        int(row[6]) if len(row) > 6 and row[6] else None,
        row[7] if len(row) > 7 else None
    )

def main():
    conn = get_db_connection()
    if conn:
        try:
            create_tables(conn)
            
            # Definir SQLs de inserción
            sql_competiciones = "INSERT INTO competiciones (competicion_id, nombre_competicion) VALUES (%s, %s) ON CONFLICT (competicion_id) DO NOTHING"
            sql_equipos = "INSERT INTO equipos (equipo_id, nombre_equipo, codigo_pais, nombre_pais) VALUES (%s, %s, %s, %s) ON CONFLICT (equipo_id) DO NOTHING"
            sql_jugadores = "INSERT INTO jugadores (jugador_id, nombre_jugador) VALUES (%s, %s) ON CONFLICT (jugador_id) DO NOTHING"
            sql_partidos = """INSERT INTO partidos (partido_id, competicion_id, fecha_inicio, estado, equipo_local_id, equipo_visitante_id, goles_local, goles_visitante, tarjetas_amarillas_local, tarjetas_rojas_local, tarjetas_amarillas_visitante, tarjetas_rojas_visitante, tiempo_transcurrido) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (partido_id) DO NOTHING"""
            sql_incidentes = """INSERT INTO incidentes (incidente_id, partido_id, minuto, periodo, tipo, subtipo, jugador_id, jugador_participante_id, campo) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (incidente_id) DO NOTHING"""

            # Procesar archivos en orden
            process_file(conn, 'competiciones.csv', 'competiciones', sql_competiciones, process_competicion_row)
            process_file(conn, 'equipos.csv', 'equipos', sql_equipos, process_equipo_row)
            process_file(conn, 'jugadores.csv', 'jugadores', sql_jugadores, process_jugador_row)
            process_file(conn, 'partidos.csv', 'partidos', sql_partidos, process_partido_row)
            process_file(conn, 'incidentes.csv', 'incidentes', sql_incidentes, process_incidente_row)

        finally:
            conn.close()
            print("Proceso completado. Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    main()