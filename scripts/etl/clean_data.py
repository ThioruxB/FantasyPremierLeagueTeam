import csv
import os

print("Iniciando la limpieza de los archivos CSV...")

# --- Configuración ---
FILES_TO_CLEAN = {
    'competiciones': 'competiciones.csv',
    'equipos': 'equipos.csv',
    'jugadores': 'jugadores.csv',
    'partidos': 'partidos.csv',
    'incidentes': 'incidentes.csv'
}

CLEAN_SUFFIX = '_clean.csv'

# --- Funciones de Limpieza ---

def clean_competiciones(reader, writer):
    """Limpia y escribe filas de competiciones."""
    writer.writerow(next(reader)) # Escribir cabecera
    for row in reader:
        if not row or not row[0]:
            continue
        writer.writerow(row)
    return {row[0] for row in reader} # Devuelve los IDs válidos

def clean_equipos(reader, writer):
    """Limpia y escribe filas de equipos."""
    writer.writerow(next(reader))
    for row in reader:
        if not row or not row[0]:
            continue
        writer.writerow(row)

def clean_jugadores(reader, writer):
    """Limpia y escribe filas de jugadores."""
    writer.writerow(next(reader))
    for row in reader:
        if not row or not row[0]:
            continue
        writer.writerow(row)

def clean_partidos(reader, writer, valid_competicion_ids):
    """Limpia y escribe filas de partidos, validando contra IDs de competición."""
    header = next(reader)
    writer.writerow(header)
    valid_partido_ids = set()

    for row in reader:
        if not row or not row[0]:
            continue

        # Validar que la competición exista
        competicion_id = row[1]
        if competicion_id not in valid_competicion_ids:
            print(f"  - [Partidos] Omitiendo partido ID {row[0]}: competición ID '{competicion_id}' no es válida.")
            continue

        # Validar que los equipos existan
        equipo_local_id = row[4]
        equipo_visitante_id = row[5]
        if not equipo_local_id or not equipo_visitante_id:
            print(f"  - [Partidos] Omitiendo partido ID {row[0]}: falta ID de equipo local o visitante.")
            continue
        
        # Limpiar tiempo_transcurrido (columna 12)
        if len(row) > 12 and not row[12].isdigit():
            row[12] = '' # Ponerlo vacío para que COPY lo interprete como NULL

        writer.writerow(row)
        valid_partido_ids.add(row[0])
        
    return valid_partido_ids

def clean_incidentes(reader, writer, valid_partido_ids):
    """Limpia y escribe filas de incidentes, validando contra IDs de partido."""
    header = next(reader)
    writer.writerow(header)
    periodo_map = {'FirstHalf': '1', 'SecondHalf': '2', 'PostGame': '3', 'PreMatch': '0', 'PenaltyShootout': '4'}

    for row in reader:
        if not row or not row[0]:
            continue
        
        # Validar que el partido exista
        partido_id = row[1]
        if partido_id not in valid_partido_ids:
            print(f"  - [Incidentes] Omitiendo incidente ID {row[0]}: partido ID '{partido_id}' no es válido o fue omitido.")
            continue

        # Mapear periodo (columna 8)
        if len(row) > 8 and row[8] in periodo_map:
            row[8] = periodo_map[row[8]]
        
        writer.writerow(row)

# --- Lógica Principal ---

try:
    # 1. Leer todos los IDs válidos de competiciones primero
    valid_competicion_ids = set()
    comp_file = FILES_TO_CLEAN['competiciones']
    if os.path.exists(comp_file):
        with open(comp_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # saltar cabecera
            for row in reader:
                if row and row[0]:
                    valid_competicion_ids.add(row[0])
        print(f"Encontrados {len(valid_competicion_ids)} IDs de competiciones para validar.")
    else:
        print(f"ADVERTENCIA: No se encontró '{comp_file}'. La validación de partidos puede fallar.")

    # 2. Limpiar archivos básicos y partidos
    valid_partido_ids = set()
    for name, filename in FILES_TO_CLEAN.items():
        if name == 'incidentes': continue # Los incidentes se limpian al final
        
        if not os.path.exists(filename):
            print(f"ADVERTENCIA: Archivo '{filename}' no encontrado. Omitiendo.")
            continue

        clean_filename = filename.replace('.csv', CLEAN_SUFFIX)
        print(f"Procesando '{filename}' -> '{clean_filename}'")
        
        with open(filename, 'r', encoding='utf-8') as infile, \
             open(clean_filename, 'w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            if name == 'competiciones':
                clean_competiciones(reader, writer)
            elif name == 'equipos':
                clean_equipos(reader, writer)
            elif name == 'jugadores':
                clean_jugadores(reader, writer)
            elif name == 'partidos':
                valid_partido_ids = clean_partidos(reader, writer, valid_competicion_ids)
                print(f"Se generaron {len(valid_partido_ids)} IDs de partidos válidos para la siguiente fase.")

    # 3. Limpiar incidentes usando los IDs de partidos válidos
    inc_file = FILES_TO_CLEAN['incidentes']
    if os.path.exists(inc_file):
        clean_inc_filename = inc_file.replace('.csv', CLEAN_SUFFIX)
        print(f"Procesando '{inc_file}' -> '{clean_inc_filename}'")
        with open(inc_file, 'r', encoding='utf-8') as infile, \
             open(clean_inc_filename, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            clean_incidentes(reader, writer, valid_partido_ids)
    else:
        print(f"ADVERTENCIA: Archivo '{inc_file}' no encontrado. Omitiendo.")

    print("\nLimpieza de archivos CSV completada.")

except Exception as e:
    print(f"\nOcurrió un error durante el proceso de limpieza: {e}")
