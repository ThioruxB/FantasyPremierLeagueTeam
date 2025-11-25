
import pandas as pd
from sqlalchemy import create_engine, text

# Database connection
db_url = 'postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb'
engine = create_engine(
    db_url,
    connect_args={'sslmode': 'require'}
)

# SQL query to get all name variations for player types
query = """
SELECT singular_name, singular_name_short, plural_name, plural_name_short
FROM player_types
ORDER BY id;
"""

# Execute the query and print the result
try:
    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)
        if not df.empty:
            print("Todas las variaciones de nombres para los tipos de jugador:")
            for index, row in df.iterrows():
                print(f"- Posición: {row['singular_name']}")
                print(f"  - Nombre corto (singular): {row['singular_name_short']}")
                print(f"  - Nombre (plural): {row['plural_name']}")
                print(f"  - Nombre corto (plural): {row['plural_name_short']}")
                print("---")
        else:
            print("No se encontró información sobre los tipos de jugador.")
except Exception as e:
    print(f"Ocurrió un error al consultar la base de datos: {e}")
