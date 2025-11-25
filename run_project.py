import subprocess
import sys
import pandas as pd
import os

# --- Configuración de las Fases del Proyecto ---
# Lista de tuplas, donde cada tupla contiene el nombre del script y un mensaje para el usuario.
PHASES = [
    ('src/data_pipeline.py', 'Fase 1: Extrayendo y actualizando datos de la FPL...'),
    ('src/enrich_with_csv_data.py', 'Fase 2: Enriqueciendo datos con CSVs de partidos...'),
    ('src/feature_engineering.py', 'Fase 3: Calculando métricas avanzadas (volatilidad, etc.)...'),
    ('src/model_training.py', 'Fase 4: Entrenando modelo y prediciendo puntos (xP)...'),
    ('src/team_selection.py', 'Fase 5: Seleccionando equipo ideal y generando explicaciones...')
]

FINAL_TEAM_FILE = 'data/processed/equipo_ideal.csv'

def run_phase(script_name, description):
    """Ejecuta un script de Python como una fase del pipeline y maneja los errores."""
    print("-" * 60)
    print(description)
    print("-" * 60)
    
    try:
        # Se usa sys.executable para asegurar que se corre con el mismo intérprete de Python
        process = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=True,  # Lanza una excepción si el script devuelve un código de error
            encoding='utf-8'
        )
        print(process.stdout)
        print(f"\n[ÉXITO] La fase '{script_name}' se completó correctamente.")
        return True
    except FileNotFoundError:
        print(f"[ERROR] El archivo '{script_name}' no se encontró. Asegúrate de que está en el directorio correcto.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Hubo un error al ejecutar '{script_name}'.")
        print("--- Salida de Error ---")
        print(e.stderr)
        print("------------------------")
        return False
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado durante la ejecución de '{script_name}': {e}")
        return False

def determine_lineup():
    """Lee el equipo ideal y determina la alineación, capitán y suplentes."""
    print("=" * 60)
    print("PROCESO FINALIZADO - ARMANDO LA ALINEACIÓN FINAL")
    print("=" * 60)

    if not os.path.exists(FINAL_TEAM_FILE):
        print(f"[ERROR] No se encontró el archivo final '{FINAL_TEAM_FILE}'. No se puede determinar la alineación.")
        return

    # Cargar el equipo de 15 jugadores
    squad_df = pd.read_csv(FINAL_TEAM_FILE)
    squad_df = squad_df.sort_values(by='xP', ascending=False).reset_index(drop=True)

    # --- Capitán y Vicecapitán ---
    captain = squad_df.iloc[0]
    vice_captain = squad_df.iloc[1]

    # --- Separar Porteros y Jugadores de Campo ---
    goalkeepers = squad_df[squad_df['Posicion'] == 'Goalkeeper']
    outfield_players = squad_df[squad_df['Posicion'] != 'Goalkeeper']

    # --- Determinar Alineación Titular (11 jugadores) ---
    starting_11 = []
    substitutes = []

    # 1. Seleccionar portero titular (el de mayor xP)
    starting_goalkeeper = goalkeepers.iloc[0]
    bench_goalkeeper = goalkeepers.iloc[1]
    starting_11.append(starting_goalkeeper)
    
    # 2. Lógica para seleccionar 10 jugadores de campo que formen una alineación válida
    # Empezamos con los 10 con mayor xP y ajustamos si la formación no es válida.
    tentative_starters = outfield_players.head(10)
    tentative_subs = outfield_players.tail(3)

    # Contar posiciones en el 11 titular tentativo
    formation = tentative_starters['Posicion'].value_counts() 
    
    # Requisitos mínimos de formación
    min_def = 3
    min_mid = 2
    min_fwd = 1

    # Ajustar si faltan defensas
    while formation.get('Defender', 0) < min_def:
        # Sacar al jugador con menos xP que no sea defensa
        player_to_drop = tentative_starters[tentative_starters['Posicion'] != 'Defender'].iloc[-1]
        # Meter al defensa con más xP del banquillo
        player_to_add = tentative_subs[tentative_subs['Posicion'] == 'Defender'].iloc[0]
        
        tentative_starters = pd.concat([tentative_starters.drop(player_to_drop.name), player_to_add.to_frame().T])
        tentative_subs = pd.concat([tentative_subs.drop(player_to_add.name), player_to_drop.to_frame().T])
        formation = tentative_starters['Posicion'].value_counts()

    # Ajustar si faltan delanteros
    while formation.get('Forward', 0) < min_fwd:
        player_to_drop = tentative_starters[tentative_starters['Posicion'] != 'Forward'].iloc[-1]
        player_to_add = tentative_subs[tentative_subs['Posicion'] == 'Forward'].iloc[0]

        tentative_starters = pd.concat([tentative_starters.drop(player_to_drop.name), player_to_add.to_frame().T])
        tentative_subs = pd.concat([tentative_subs.drop(player_to_add.name), player_to_drop.to_frame().T])
        formation = tentative_starters['Posicion'].value_counts()

    # Ajustar si faltan mediocampistas
    while formation.get('Midfielder', 0) < min_mid:
        player_to_drop = tentative_starters[tentative_starters['Posicion'] != 'Midfielder'].iloc[-1]
        player_to_add = tentative_subs[tentative_subs['Posicion'] == 'Midfielder'].iloc[0]

        tentative_starters = pd.concat([tentative_starters.drop(player_to_drop.name), player_to_add.to_frame().T])
        tentative_subs = pd.concat([tentative_subs.drop(player_to_add.name), player_to_drop.to_frame().T])
        formation = tentative_starters['Posicion'].value_counts()

    # Añadir los 10 jugadores de campo definitivos a la alineación
    starting_11.extend([row for index, row in tentative_starters.iterrows()])
    
    # --- Ordenar Suplentes ---
    # Primero los de campo por xP descendente, y al final el portero
    substitutes.extend([row for index, row in tentative_subs.sort_values('xP', ascending=False).iterrows()])
    substitutes.append(bench_goalkeeper)

    # --- Imprimir Resultados Finales ---
    print_final_lineup(starting_11, substitutes, captain, vice_captain)


def print_final_lineup(starting_11, substitutes, captain, vice_captain):
    """Imprime la alineación final en un formato claro y profesional."""
    
    print("\n--- 👑 Capitán y Vicecapitán ---")
    print(f"Capitán (C):       {captain['Nombre']} {captain['Apellido']} (xP: {captain['xP']:.2f})")
    print(f"Vicecapitán (VC):  {vice_captain['Nombre']} {vice_captain['Apellido']} (xP: {vice_captain['xP']:.2f})")

    print("\n--- ⚽ Once Inicial Titular ---")
    for player in sorted(starting_11, key=lambda p: {'Goalkeeper': 0, 'Defender': 1, 'Midfielder': 2, 'Forward': 3}[p['Posicion']]):
        is_captain = '(C)' if player.equals(captain) else ''
        is_vice_captain = '(VC)' if player.equals(vice_captain) else ''
        print(f"- {player['Posicion']:<12} | {player['Nombre']} {player['Apellido']:<30} (xP: {player['xP']:.2f}) {is_captain}{is_vice_captain}")

    print("\n--- 🔄 Suplentes (Banquillo) ---")
    for i, player in enumerate(substitutes):
        print(f"{i+1}. {player['Posicion']:<12} | {player['Nombre']} {player['Apellido']:<30} (xP: {player['xP']:.2f})")

if __name__ == '__main__':
    # Ejecutar todas las fases del proyecto en orden
    for script, message in PHASES:
        success = run_phase(script, message)
        if not success:
            print("\nEl pipeline se ha detenido debido a un error en una de las fases.")
            sys.exit(1) # Termina el script con un código de error

    # Si todas las fases fueron exitosas, determinar y mostrar la alineación final
    determine_lineup()