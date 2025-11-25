import os
import subprocess
import sys

def run_step(command_list, description):
    """Ejecuta un paso del proceso y termina si hay un error."""
    print(f"--- {description}... ---")
    try:
        # Usar una lista de argumentos y shell=False es más seguro y robusto.
        # text=True (o universal_newlines=True) usará la codificación por defecto del sistema.
        process = subprocess.run(command_list, check=True, capture_output=True, text=True, errors='replace')
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            # soccerdata a menudo imprime logs de información en stderr, así que los imprimimos en stdout
            print(process.stderr)
        print(f"--- ¡Éxito! ---")
        return True
    except subprocess.CalledProcessError as e:
        print(f"¡Error en el paso: {description}!", file=sys.stderr)
        print(f"Comando: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"Código de retorno: {e.returncode}", file=sys.stderr)
        print(f"Salida de stdout:\n{e.stdout}", file=sys.stderr)
        print(f"Salida de stderr:\n{e.stderr}", file=sys.stderr)
        sys.exit(1) # Termina el script si un paso falla
    except FileNotFoundError as e:
        print(f"¡Error! Comando no encontrado: {command_list[0]}", file=sys.stderr)
        print(f"Asegúrate de que Python y psql estén en el PATH del sistema.", file=sys.stderr)
        sys.exit(1)

def main():
    """Función principal que orquesta todo el proceso de actualización."""
    print("--- Iniciando el proceso de actualización de datos de la Premier League ---")

    # Obtenemos el ejecutable de Python para asegurar que usamos el mismo en los subprocesos
    python_executable = sys.executable

    # 1. Scrape soccer data
    run_step([python_executable, "scripts/scraping/scrape_soccerdata.py"], "Paso 1: Scrapeando nuevos partidos")

    # 2. Append new data
    run_step([python_executable, "scripts/etl/append_data.py"], "Paso 2: Añadiendo nuevos datos a los CSVs")

    # 3. Preprocess incidents
    run_step([python_executable, "scripts/etl/preprocess_incidentes.py"], "Paso 3: Preprocesando archivo de incidentes")

    # 4. Truncate tables in DB
    db_connection_string = os.getenv("DB_CONNECTION_STRING")
    if not db_connection_string:
        print("¡Error! La variable de entorno DB_CONNECTION_STRING no está configurada.", file=sys.stderr)
        print("Por favor, configúrala con tu cadena de conexión a PostgreSQL.", file=sys.stderr)
        sys.exit(1)
    
    psql_truncate_command = ["psql", db_connection_string, "-f", "sql/truncate_tables.sql"]
    run_step(psql_truncate_command, "Paso 4: Truncando tablas en la base de datos")

    # 5. Load all data into DB
    psql_load_command = ["psql", db_connection_string, "-f", "sql/load_data.sql"]
    run_step(psql_load_command, "Paso 5: Cargando datos en la base de datos")

    print("\n--- ¡Proceso de actualización completado con éxito! ---")

if __name__ == "__main__":
    main()