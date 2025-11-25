
import pandas as pd
import json
from fase2_modelado import get_data as get_data_f2, calculate_volatility, run_monte_carlo_simulation
from fase3_recomendacion import train_and_predict_xp
from fase4_explicacion import select_ideal_team

# Copiamos la función mejorada de la Fase 4
def generate_explanation(player, all_players):
    position = player['Posicion']
    position_players = all_players[all_players['Posicion'] == position]

    explanation = f"{player['Nombre']} {player['Apellido']} ({player['Posicion']}) - xP: {player['xP']:.2f}, Precio: {player['Precio']:.1f}. "
    
    reasons = []

    if player['xP'] >= position_players['xP'].quantile(0.90):
        reasons.append(f"su predicción de puntos es excepcional (top 10% de los {position}s)")
    elif player['xP'] >= position_players['xP'].quantile(0.75):
        reasons.append(f"se proyecta como uno de los mejores puntuadores en su posición (top 25%)")

    if player['form'] >= position_players['form'].quantile(0.80):
        reasons.append(f"llega en un gran estado de forma ({player['form']:.1f} pts/partido)")

    if player['difficulty'] <= all_players['difficulty'].quantile(0.20):
        reasons.append("su próximo partido tiene una dificultad muy baja")

    if player['valor'] >= position_players['valor'].quantile(0.80):
        reasons.append("ofrece una excelente relación calidad-precio")

    if player['is_home']:
        reasons.append("además cuenta con la ventaja de jugar en casa")

    if not reasons:
        explanation += "Es una elección equilibrada y consistente para completar el equipo."
    else:
        explanation += "Se recomienda porque " + ", ".join(reasons[:-1]) + (f" y {reasons[-1]}" if len(reasons) > 1 else reasons[0]) + "."

    return explanation

def consolidate_data_for_web():
    print("--- Iniciando consolidación de datos para la web ---")

    # --- Cargar datos base ---
    try:
        fase1_df = pd.read_csv('resultados.csv')
        fase3_df = pd.read_csv('resultados_fase3.csv')
        print("Archivos CSV de las fases cargados.")
    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo {e.filename}. Asegúrate de haber ejecutado todas las fases.")
        return

    # --- Preparar datos para cada fase ---
    
    # Fase 1: Top 15 jugadores por valor
    fase1_top_valor = fase1_df.sort_values('valor', ascending=False).head(15).to_dict('records')

    # Fase 2: Equipo robusto (Ejecución completa de Monte Carlo)
    print("Ejecutando Fase 2 para obtener el equipo robusto. Esto puede tardar...")
    main_df_f2, history_df_f2 = get_data_f2()
    if main_df_f2 is not None:
        final_df_f2 = calculate_volatility(main_df_f2, history_df_f2)
        robust_df = run_monte_carlo_simulation(final_df_f2, n_simulations=100)
        fase2_robust_team = robust_df.to_dict('records')
    else:
        fase2_robust_team = []

    # Fase 3: Top 15 jugadores por xP
    fase3_top_xp = fase3_df.sort_values('xP', ascending=False).head(15).to_dict('records')

    # Fase 4: Equipo ideal con explicaciones
    print("\nGenerando equipo ideal y explicaciones de la Fase 4.")
    ideal_team_list = select_ideal_team(fase3_df, objective_col='xP')
    fase4_ideal_team = []
    if ideal_team_list:
        ideal_team_df = pd.DataFrame(ideal_team_list)
        for _, player in ideal_team_df.iterrows():
            explanation = generate_explanation(player, fase3_df)
            fase4_ideal_team.append({
                'player_info': player.to_dict(),
                'explanation': explanation
            })

    # --- Consolidar en un solo JSON ---
    final_json = {
        'fase1_top_valor': fase1_top_valor,
        'fase2_robust_team': fase2_robust_team,
        'fase3_top_xp': fase3_top_xp,
        'fase4_ideal_team': fase4_ideal_team
    }

    # Guardar el archivo JSON
    with open('fpl_data.json', 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=4)
    
    print("\nArchivo 'fpl_data.json' creado exitosamente con los datos de todas las fases.")

if __name__ == '__main__':
    consolidate_data_for_web()
