import pandas as pd
import numpy as np
import os

def preprocess_incidentes_csv(file_path='incidentes.csv'):
    print(f"Preprocesando '{file_path}' para manejar valores nulos en IDs de jugador...")
    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no existe.")
        return

    try:
        # Read the CSV, making sure to interpret empty strings as NaN
        df = pd.read_csv(file_path, keep_default_na=True, na_values=[''])

        # Explicitly convert problematic columns to numeric, coercing errors to NaN
        # This will turn any non-numeric (including empty strings) into NaN
        df['jugador_id'] = pd.to_numeric(df['jugador_id'], errors='coerce')
        df['jugador_participante_id'] = pd.to_numeric(df['jugador_participante_id'], errors='coerce')

        # Convert back to Int64 (nullable integer type) to store NaNs without converting entire column to float
        # If a column should be integer but contains NaNs, standard pandas int dtype will fail.
        # Int64 allows NaNs in integer columns.
        df['jugador_id'] = df['jugador_id'].astype('Int64')
        df['jugador_participante_id'] = df['jugador_participante_id'].astype('Int64')
        
        # Save the modified DataFrame back to CSV
        # Pandas will write Int64 NaNs as empty strings in CSV, which psql's \copy NULL '' can handle
        df.to_csv(file_path, index=False)
        print(f"'{file_path}' preprocesado y guardado correctamente.")

    except Exception as e:
        print(f"Ocurrió un error al preprocesar '{file_path}': {e}")

if __name__ == "__main__":
    preprocess_incidentes_csv()
