import pandas as pd

def analyze_csv_file(file_path, df_name):
    print(f"\n--- Analizando {df_name} ({file_path}) ---")
    try:
        df = pd.read_csv(file_path)
        print("\nPrimeras 5 filas:")
        print(df.head().to_string())
        print("\nInformación del DataFrame:")
        df.info()
        return df
    except FileNotFoundError:
        print(f"Error: '{file_path}' no encontrado.")
        return None
    except Exception as e:
        print(f"Ocurrió un error al analizar '{file_path}': {e}")
        return None

def main():
    # Analyze incidentes.csv
    incidentes_df = analyze_csv_file('incidentes.csv', 'incidentes_df')
    if incidentes_df is not None:
        print("\nValores únicos y sus conteos en la columna 'tipo' (incidentes):")
        if 'tipo' in incidentes_df.columns:
            print(incidentes_df['tipo'].value_counts().to_string())
        else:
            print("Columna 'tipo' no encontrada.")

        print("\nValores nulos en columnas críticas (incidentes):")
        critical_inc_cols = ['incidente_id', 'partido_id', 'minuto', 'tipo', 'jugador_id']
        for col in critical_inc_cols:
            if col in incidentes_df.columns:
                if incidentes_df[col].isnull().any():
                    print(f"- '{col}': {incidentes_df[col].isnull().sum()} valores nulos")
                else:
                    print(f"- '{col}': No hay valores nulos")
            else:
                print(f"- '{col}': Columna no encontrada")

    # Analyze jugadores.csv
    jugadores_df = analyze_csv_file('jugadores.csv', 'jugadores_df')
    if jugadores_df is not None:
        print("\nValores nulos en columnas críticas (jugadores):")
        critical_jug_cols = ['jugador_id', 'nombre_jugador']
        for col in critical_jug_cols:
            if col in jugadores_df.columns:
                if jugadores_df[col].isnull().any():
                    print(f"- '{col}': {jugadores_df[col].isnull().sum()} valores nulos")
                else:
                    print(f"- '{col}': No hay valores nulos")
            else:
                print(f"- '{col}': Columna no encontrada")

    # Analyze equipos.csv
    equipos_df = analyze_csv_file('equipos.csv', 'equipos_df')
    if equipos_df is not None:
        print("\nValores nulos en columnas críticas (equipos):")
        critical_eq_cols = ['equipo_id', 'nombre_equipo']
        for col in critical_eq_cols:
            if col in equipos_df.columns:
                if equipos_df[col].isnull().any():
                    print(f"- '{col}': {equipos_df[col].isnull().sum()} valores nulos")
                else:
                    print(f"- '{col}': No hay valores nulos")
            else:
                print(f"- '{col}': Columna no encontrada")

    # Analyze competiciones.csv
    competiciones_df = analyze_csv_file('competiciones.csv', 'competiciones_df')
    if competiciones_df is not None:
        print("\nValores únicos y sus conteos en la columna 'competicion_id' (competiciones):")
        if 'competicion_id' in competiciones_df.columns:
            print(competiciones_df['competicion_id'].value_counts().to_string())
        else:
            print("Columna 'competicion_id' no encontrada.")
            
        print("\nValores nulos en columnas críticas (competiciones):")
        critical_comp_cols = ['competicion_id', 'nombre_competicion']
        for col in critical_comp_cols:
            if col in competiciones_df.columns:
                if competiciones_df[col].isnull().any():
                    print(f"- '{col}': {competiciones_df[col].isnull().sum()} valores nulos")
                else:
                    print(f"- '{col}': No hay valores nulos")
            else:
                print(f"- '{col}': Columna no encontrada")

if __name__ == "__main__":
    main()
