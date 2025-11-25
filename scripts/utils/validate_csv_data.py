import pandas as pd
import numpy as np
import argparse

def validate_csv(file_path):
    """
    Validates the data consistency of a CSV file.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        dict: A dictionary containing information about inconsistent columns.
    """
    print(f"Validando archivo: {file_path}")
    inconsistencies = {}
    try:
        # Read CSV with all columns as strings to avoid type inference issues
        df = pd.read_csv(file_path, dtype=str, keep_default_na=False, na_values=[''])

        for column in df.columns:
            # Attempt to convert to numeric, coercing errors to NaN
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            
            # Identify non-numeric values that aren't just empty strings
            non_numeric_mask = numeric_col.isna() & (df[column].str.strip() != '') & df[column].notna()

            if non_numeric_mask.any():
                num_numeric = numeric_col.notna().sum()
                num_non_numeric = non_numeric_mask.sum()

                # Report if there is a mix of numeric and non-numeric values
                if num_numeric > 0 and num_non_numeric > 0:
                    inconsistent_rows = df[non_numeric_mask]
                    inconsistencies[column] = {
                        'num_numeric': num_numeric,
                        'num_non_numeric': num_non_numeric,
                        'inconsistent_values': inconsistent_rows[[column]].head().to_dict('records')
                    }
                    print(f"  - Columna '{column}' tiene tipos de datos mixtos.")

    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en {file_path}")
        return None
    except Exception as e:
        print(f"Ocurrió un error al procesar {file_path}: {e}")
        return None

    if not inconsistencies:
        print("  - No se encontraron inconsistencias mayores en los tipos de datos.")
    
    return inconsistencies

def main():
    parser = argparse.ArgumentParser(description="Valida la consistencia de datos en archivos CSV.")
    parser.add_argument('files', nargs='+', help="Lista de archivos CSV a validar.")
    args = parser.parse_args()

    all_results = {}
    for file in args.files:
        result = validate_csv(file)
        if result:
            all_results[file] = result

    print("\n--- Resumen de Validación ---")
    if not all_results:
        print("Todos los archivos se procesaron sin detectar inconsistencias mayores.")
    else:
        for file, inconsistencies in all_results.items():
            print(f"\nInconsistencias en {file}:")
            for col, info in inconsistencies.items():
                print(f"  Columna '{col}':")
                print(f"    - {info['num_numeric']} valores numéricos.")
                print(f"    - {info['num_non_numeric']} valores no numéricos.")
                print(f"    - Ejemplos de valores no numéricos:")
                for val in info['inconsistent_values']:
                    print(f"        - '{val[col]}'")

if __name__ == "__main__":
    main()
