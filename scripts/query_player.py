
import pandas as pd
from sqlalchemy import create_engine, text

# Database connection
db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
engine = create_engine(
    db_url,
    connect_args={'sslmode': 'require'}
)

# SQL query to get stats for players with last name Haaland (case-insensitive)
query = """
SELECT "Nombre", "Apellido", "Puntos Totales", "Goles", "Asistencias", "Precio"
FROM players
WHERE "Apellido" ILIKE 'Haaland';
"""

# Execute the query and print the result
try:
    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)
        if not df.empty:
            print(f"Se encontraron los siguientes jugadores con el apellido 'Haaland':")
            for index, player in df.iterrows():
                print(f"- {player['Nombre']} {player['Apellido']}:")
                print(f"  - Puntos Totales: {player['Puntos Totales']}")
                print(f"  - Goles: {player['Goles']}")
                print(f"  - Asistencias: {player['Asistencias']}")
                print(f"  - Precio: {player['Precio'] / 10.0}M") # Price is in tenths of millions
        else:
            print("No se encontró ningún jugador con el apellido 'Haaland' en la base de datos.")
except Exception as e:
    print(f"Ocurrió un error al consultar la base de datos: {e}")
