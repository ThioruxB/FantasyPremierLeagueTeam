import pandas as pd
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpBinary, PULP_CBC_CMD
import sys
import codecs

# --- 1. Cargar Datos ---
def load_data():
    print("--- Cargando datos de la Fase 3 ---")
    try:
        df = pd.read_csv('data/processed/resultados_fase3.csv')
        print("Archivo 'data/processed/resultados_fase3.csv' cargado exitosamente.")
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'data/processed/resultados_fase3.csv'. Ejecuta las fases anteriores primero.")
        return None

# --- 2. Generar Explicación Mejorada ---
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

# --- 3. Selección de Equipo Ideal con ILP ---
def select_ideal_team(df, budget=1000, objective_col='xP', formation={'Goalkeeper': 2, 'Defender': 5, 'Midfielder': 5, 'Forward': 3}):
    print(f"\n--- Iniciando Selección de Equipo Ideal maximizando '{objective_col}' ---")
    
    # Filter out unavailable players (This is now handled by the adjusted xP)
    # df = df[df['status'] == 'a']

    players = df.to_dict('records')
    prob = LpProblem("IdealTeamSelection", LpMaximize)
    player_vars = LpVariable.dicts("Player", [(p['Nombre'], p['Apellido']) for p in players], cat=LpBinary)
    
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] * p[objective_col] for p in players]), f"Total_{objective_col}"
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] * p['Precio'] for p in players]) <= budget, "TotalCost"
    prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players]) == sum(formation.values()), "TotalPlayers"
    
    for pos, count in formation.items():
        prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players if p['Posicion'] == pos]) == count, f"Num{pos}"
        
    team_names = df['team_name'].unique()
    for team in team_names:
        prob += lpSum([player_vars[(p['Nombre'], p['Apellido'])] for p in players if p['team_name'] == team]) <= 3, f"Max3PerTeam_{team.replace(' ','_')}"
        
    prob.solve(PULP_CBC_CMD(msg=0))
    
    selected_players = []
    for p in players:
        if player_vars[(p['Nombre'], p['Apellido'])].varValue == 1:
            selected_players.append(p)
            
    return selected_players

if __name__ == '__main__':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    player_data = load_data()

    if player_data is not None:
        ideal_team_list = select_ideal_team(player_data, objective_col='xP')

        if ideal_team_list:
            ideal_team_df = pd.DataFrame(ideal_team_list).sort_values(by=['Posicion', 'xP'], ascending=[True, False])
            
            # Debugging: Print the ideal_team_df before saving
            print("\n--- Contenido de ideal_team_df antes de guardar ---")
            print(ideal_team_df[['Nombre', 'Apellido', 'status', 'xP']].to_string())
            print("---------------------------------------------------")
            
            # Debugging: Print the ideal_team_df before saving
            print("\n--- Contenido de ideal_team_df antes de guardar ---")
            print(ideal_team_df[['Nombre', 'Apellido', 'status', 'xP']].to_string())
            print("---------------------------------------------------")
            
            print("\n--- Equipo Ideal Recomendado y Justificación ---")
            for index, player in ideal_team_df.iterrows():
                explanation = generate_explanation(player, player_data)
                print(f"- {explanation}")
            
            total_cost = ideal_team_df['Precio'].sum()
            total_xp = ideal_team_df['xP'].sum()
            print("\n--- Estadísticas del Equipo Ideal ---")
            print(f"Costo Total: {total_cost:.1f} / 1000")
            print(f"xP Total: {total_xp:.2f}")
            
            # Guardar el equipo ideal en un archivo CSV para ser usado por otros scripts
            ideal_team_df.to_csv('data/processed/equipo_ideal.csv', index=False, encoding='utf-8-sig')
            print("\nEl equipo ideal ha sido guardado en 'data/processed/equipo_ideal.csv'")
        else:
            print("No se pudo generar un equipo ideal con los datos proporcionados.")