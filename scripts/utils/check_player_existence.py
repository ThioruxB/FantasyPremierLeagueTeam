import pandas as pd
import numpy as np
import os

def check_player_existence():
    print("--- Verificando existencia de jugadores entre incidentes.csv y jugadores.csv ---")

    # Load jugadores.csv
    jugadores_df = None
    try:
        jugadores_df = pd.read_csv('jugadores.csv', dtype={'jugador_id': 'Int64'})
        print(f"Cargados {len(jugadores_df)} jugadores de jugadores.csv.")
    except FileNotFoundError:
        print("Error: 'jugadores.csv' no encontrado.")
        return
    except Exception as e:
        print(f"Ocurrió un error al cargar 'jugadores.csv': {e}")
        return

    existing_jugador_ids = set(jugadores_df['jugador_id'].dropna().tolist())

    # Check for specific missing player (380706)
    missing_player_id = 380706
    if missing_player_id not in existing_jugador_ids:
        print(f"\n¡Confirmado! El jugador_id {missing_player_id} NO está presente en jugadores.csv.")
    else:
        print(f"\nEl jugador_id {missing_player_id} SÍ está presente en jugadores.csv.")


    # Load incidentes.csv
    incidentes_df = None
    try:
        # Use dtype='Int64' to allow NaN in integer columns
        incidentes_df = pd.read_csv('incidentes.csv', dtype={'jugador_id': 'Int64', 'jugador_participante_id': 'Int64'})
        print(f"Cargados {len(incidentes_df)} incidentes de incidentes.csv.")
    except FileNotFoundError:
        print("Error: 'incidentes.csv' no encontrado.")
        return
    except Exception as e:
        print(f"Ocurrió un error al cargar 'incidentes.csv': {e}")
        return

    # Find unique player IDs referenced in incidentes.csv
    incidentes_player_ids = set(incidentes_df['jugador_id'].dropna().tolist())
    incidentes_participant_ids = set(incidentes_df['jugador_participante_id'].dropna().tolist())
    all_referenced_player_ids = incidentes_player_ids.union(incidentes_participant_ids)

    # Find referenced player IDs that are missing from jugadores.csv
    missing_from_jugadores = all_referenced_player_ids - existing_jugador_ids

    if missing_from_jugadores:
        print(f"\nSe encontraron {len(missing_from_jugadores)} jugadores referenciados en incidentes.csv que NO están en jugadores.csv:")
        # Print up to 10 missing IDs
        for i, player_id in enumerate(list(missing_from_jugadores)[:10]):
            print(f"- Jugador ID: {player_id}")
        if len(missing_from_jugadores) > 10:
            print("  ...")
    else:
        print("\nTodos los jugadores referenciados en incidentes.csv están presentes en jugadores.csv.")

if __name__ == "__main__":
    check_player_existence()
