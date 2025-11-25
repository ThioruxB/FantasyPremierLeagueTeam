import pandas as pd
import argparse

def investigate_column(file_path, column_name):
    """
    Investigates a specific column in a CSV file, showing unique values and their counts.

    Args:
        file_path (str): The path to the CSV file.
        column_name (str): The name of the column to investigate.
    """
    print(f"Investigando la columna '{column_name}' en el archivo '{file_path}'...")
    try:
        df = pd.read_csv(file_path, dtype={column_name: str})
        
        if column_name not in df.columns:
            print(f"Error: Columna '{column_name}' no encontrada en {file_path}.")
            return

        value_counts = df[column_name].value_counts(dropna=False)
        
        print(f"\nValores únicos y sus frecuencias en la columna '{column_name}':")
        print(value_counts.to_string())

    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en {file_path}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Investigate a column in a CSV file.")
    parser.add_argument('file', help="CSV file to investigate.")
    parser.add_argument('column', help="Name of the column to investigate.")
    args = parser.parse_args()

    investigate_column(args.file, args.column)

if __name__ == "__main__":
    main()

