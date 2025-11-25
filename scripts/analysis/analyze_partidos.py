import pandas as pd

def analyze_partidos_csv():
    try:
        print("--- Analizando partidos.csv ---")
        partidos_df = pd.read_csv('partidos.csv')

        print("\nPrimeras 5 filas:")
        print(partidos_df.head().to_string())

        print("\nInformación del DataFrame:")
        partidos_df.info()

        print("\nConteo de valores de la columna 'estado':")
        print(partidos_df['estado'].value_counts().to_string())

        # Check for missing values in critical columns
        print("\nValores nulos en columnas críticas:")
        critical_columns = ['partido_id', 'competicion_id', 'fecha_inicio', 'estado', 'equipo_local_id', 'equipo_visitante_id', 'goles_local', 'goles_visitante']
        for col in critical_columns:
            if partidos_df[col].isnull().any():
                print(f"- '{col}': {partidos_df[col].isnull().sum()} valores nulos")
            else:
                print(f"- '{col}': No hay valores nulos")

    except FileNotFoundError:
        print("Error: 'partidos.csv' no encontrado.")
    except Exception as e:
        print(f"Ocurrió un error al analizar 'partidos.csv': {e}")

if __name__ == "__main__":
    analyze_partidos_csv()
