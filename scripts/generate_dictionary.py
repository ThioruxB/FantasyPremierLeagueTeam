import pandas as pd

def generate_data_dictionary(event_data_path, player_data_path, output_path):
    # Load data
    event_df = pd.read_csv(event_data_path)
    player_df = pd.read_csv(player_data_path)

    # Prepare data dictionary for EventData.csv
    event_dict_data = []
    for col in event_df.columns:
        event_dict_data.append({
            'Tabla': 'EventData',
            'Nombre del Campo': col,
            'Tipo de Dato': str(event_df[col].dtype),
            'Descripción': '' # Placeholder for description
        })
    event_dict_df = pd.DataFrame(event_dict_data)

    # Prepare data dictionary for PlayerData.csv
    player_dict_data = []
    for col in player_df.columns:
        player_dict_data.append({
            'Tabla': 'PlayerData',
            'Nombre del Campo': col,
            'Tipo de Dato': str(player_df[col].dtype),
            'Descripción': '' # Placeholder for description
        })
    player_dict_df = pd.DataFrame(player_dict_data)

    # Concatenate and save to Excel
    full_dict_df = pd.concat([event_dict_df, player_dict_df], ignore_index=True)
    full_dict_df.to_excel(output_path, index=False)

    print(f"Diccionario de datos generado exitosamente en {output_path}")

if __name__ == '__main__':
    generate_data_dictionary('EventData.csv', 'PlayerData.csv', 'diccionarioscrapping.xlsx')