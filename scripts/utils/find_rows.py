import pandas as pd
import argparse

def find_rows_with_value(file_path, column_name, value):
    """
    Finds and prints rows where a specific column has a given value.

    Args:
        file_path (str): The path to the CSV file.
        column_name (str): The name of the column to check.
        value (str): The value to look for.
    """
    print(f"Buscando filas donde '{column_name}' es '{value}' en '{file_path}'...")
    try:
        df = pd.read_csv(file_path, dtype=str)
        
        if column_name not in df.columns:
            print(f"Error: Columna '{column_name}' no encontrada en {file_path}.")
            return

        matching_rows = df[df[column_name] == value]
        
        if not matching_rows.empty:
            print(f"Se encontraron {len(matching_rows)} filas coincidentes. Mostrando las primeras 5:")
            print(matching_rows.head().to_string())
        else:
            print("No se encontraron filas coincidentes.")

    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en {file_path}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Find rows with a specific value in a column.")
    parser.add_argument('file', help="CSV file to investigate.")
    parser.add_argument('column', help="Name of the column to check.")
    parser.add_argument('value', help="Value to look for.")
    args = parser.parse_args()

    find_rows_with_value(args.file, args.column, args.value)

if __name__ == "__main__":
    main()
