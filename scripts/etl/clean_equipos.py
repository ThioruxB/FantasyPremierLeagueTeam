import pandas as pd

def clean_equipos_csv():
    try:
        df = pd.read_csv('equipos.csv')
    except FileNotFoundError:
        print("equipos.csv not found.")
        return

    # Remove rows with missing equipo_id
    df.dropna(subset=['equipo_id'], inplace=True)

    # Convert equipo_id to integer
    df['equipo_id'] = pd.to_numeric(df['equipo_id'], errors='coerce').astype('Int64')

    # Set default values for codigo_pais and nombre_pais
    df['codigo_pais'] = 'ENG'
    df['nombre_pais'] = 'England'

    # Overwrite the CSV with the cleaned data
    df.to_csv('equipos.csv', index=False)
    print("equipos.csv has been cleaned.")

if __name__ == "__main__":
    clean_equipos_csv()
