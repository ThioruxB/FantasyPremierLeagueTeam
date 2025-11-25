import pandas as pd
import os

def clean_csv(file_path, columns_to_drop):
    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no existe. Saltando limpieza.")
        return

    try:
        df = pd.read_csv(file_path)
        
        # Identify columns that actually exist in the DataFrame
        existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]

        if existing_columns_to_drop:
            print(f"Limpiando '{file_path}': Eliminando columnas {existing_columns_to_drop}")
            df = df.drop(columns=existing_columns_to_drop)
            df.to_csv(file_path, index=False)
            print(f"'{file_path}' limpiado y guardado.")
        else:
            print(f"'{file_path}': No se encontraron columnas para eliminar o ya estaban eliminadas.")

    except Exception as e:
        print(f"Error al limpiar '{file_path}': {e}")

def main():
    # Columns to drop from partidos.csv
    partidos_cols_to_drop = [
        'tarjetas_amarillas_local',
        'tarjetas_rojas_local',
        'tarjetas_amarillas_visitante',
        'tarjetas_rojas_visitante'
    ]
    clean_csv('partidos.csv', partidos_cols_to_drop)

    # Columns to drop from equipos.csv
    equipos_cols_to_drop = [
        'codigo_pais',
        'nombre_pais'
    ]
    clean_csv('equipos.csv', equipos_cols_to_drop)

    # Columns to drop from incidentes.csv
    incidentes_cols_to_drop = [
        'campo'
    ]
    clean_csv('incidentes.csv', incidentes_cols_to_drop)

if __name__ == "__main__":
    main()
