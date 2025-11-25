import csv
import sys

def check_csv_structure(file_path):
    """
    Checks the structure of a CSV file, reporting the number of columns in each row.
    """
    print(f"Revisando la estructura del archivo '{file_path}'...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            num_header_cols = len(header)
            print(f"El encabezado tiene {num_header_cols} columnas.")
            
            inconsistent_rows = []
            for i, row in enumerate(reader, 1):
                num_row_cols = len(row)
                if num_row_cols != num_header_cols:
                    inconsistent_rows.append((i, num_row_cols, row))
            
            if inconsistent_rows:
                print(f"Se encontraron {len(inconsistent_rows)} filas con un número de columnas inconsistente.")
                # Print details for the first 5 inconsistent rows
                for i, num_cols, row_data in inconsistent_rows[:5]:
                    print(f"  - Fila {i}: tiene {num_cols} columnas (se esperaban {num_header_cols}). Contenido: {row_data}")
                if len(inconsistent_rows) > 5:
                    print("  ...")

            else:
                print("Todas las filas tienen un número de columnas consistente.")


    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en {file_path}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_csv_structure(sys.argv[1])
    else:
        print("Por favor, proporciona la ruta de un archivo.")
