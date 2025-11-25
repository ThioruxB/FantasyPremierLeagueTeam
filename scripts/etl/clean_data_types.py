import pandas as pd

def clean_data_types():
    # Clean partidos.csv
    try:
        partidos_df = pd.read_csv('partidos.csv')
        
        # Columns that should be integers
        int_cols_partidos = [
            'partido_id', 'competicion_id', 'equipo_local_id', 
            'equipo_visitante_id', 'goles_local', 'goles_visitante',
            'tarjetas_amarillas_local', 'tarjetas_rojas_local',
            'tarjetas_amarillas_visitante', 'tarjetas_rojas_visitante'
        ]
        
        for col in int_cols_partidos:
            # Convert to numeric, coercing errors, then to Int64 (which can handle NaNs)
            partidos_df[col] = pd.to_numeric(partidos_df[col], errors='coerce').astype('Int64')
            
        partidos_df.to_csv('partidos.csv', index=False)
        print("partidos.csv has been cleaned.")
        
    except FileNotFoundError:
        print("partidos.csv not found.")

    # Clean incidentes.csv
    try:
        incidentes_df = pd.read_csv('incidentes.csv')
        
        # Columns that should be integers
        int_cols_incidentes = [
            'incidente_id', 'partido_id', 'minuto', 
            'jugador_id', 'jugador_participante_id'
        ]
        
        for col in int_cols_incidentes:
            # Convert to numeric, coercing errors, then to Int64 (which can handle NaNs)
            incidentes_df[col] = pd.to_numeric(incidentes_df[col], errors='coerce').astype('Int64')

        incidentes_df.to_csv('incidentes.csv', index=False)
        print("incidentes.csv has been cleaned.")
        
    except FileNotFoundError:
        print("incidentes.csv not found.")

if __name__ == "__main__":
    clean_data_types()
