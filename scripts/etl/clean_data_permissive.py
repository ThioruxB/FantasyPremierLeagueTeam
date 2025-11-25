import csv
import os

print("Iniciando la limpieza de formato de los archivos CSV (modo permisivo y robusto)...")

# --- Configuración ---
FILES_TO_CLEAN = {
    'competiciones': 'competiciones.csv',
    'equipos': 'equipos.csv',
    'jugadores': 'jugadores.csv',
    'partidos': 'partidos.csv',
    'incidentes': 'incidentes.csv'
}

CLEAN_SUFFIX = '_clean_permissive.csv'

# --- Lógica Principal ---

try:
    for name, filename in FILES_TO_CLEAN.items():
        if not os.path.exists(filename):
            print(f"ADVERTENCIA: Archivo '{filename}' no encontrado. Omitiendo.")
            continue

        clean_filename = filename.replace('.csv', CLEAN_SUFFIX)
        print(f"Procesando '{filename}' -> '{clean_filename}'")
        
        with open(filename, 'r', encoding='utf-8') as infile, \
             open(clean_filename, 'w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            header = next(reader)
            writer.writerow(header)

            for row in reader:
                if not row: continue

                if name == 'partidos':
                    # Limpiar tiempo_transcurrido (columna 12)
                    if len(row) > 12 and not row[12].strip().isdigit():
                        row[12] = '' # Ponerlo vacío para que COPY lo interprete como NULL
                
                elif name == 'incidentes':
                    # Mapear periodo (columna 8) de forma robusta
                    periodo_map = {'FirstHalf': '1', 'SecondHalf': '2', 'PostGame': '3', 'PreMatch': '0', 'PenaltyShootout': '4', 'Start': '1'}
                    if len(row) > 8:
                        periodo_val = row[8].strip() # Limpiar espacios en blanco
                        if periodo_val in periodo_map:
                            row[8] = periodo_map[periodo_val]
                
                writer.writerow(row)

    print("\nLimpieza de formato (permisiva y robusta) completada.")

except Exception as e:
    print(f"\nOcurrió un error durante el proceso de limpieza: {e}")