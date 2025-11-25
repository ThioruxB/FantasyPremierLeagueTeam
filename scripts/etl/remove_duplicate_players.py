import pandas as pd

def remove_duplicate_players():
    try:
        df = pd.read_csv('jugadores.csv')
    except FileNotFoundError:
        print("jugadores.csv not found.")
        return

    # Remove duplicate jugador_id, keeping the first occurrence
    df.drop_duplicates(subset=['jugador_id'], keep='first', inplace=True)

    # Overwrite the CSV with the cleaned data
    df.to_csv('jugadores.csv', index=False)
    print("Duplicate players have been removed from jugadores.csv.")

if __name__ == "__main__":
    remove_duplicate_players()
