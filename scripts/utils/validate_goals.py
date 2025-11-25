import json

def validate_goals(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        game_id = None
        team = None
        player = None
        
        for line in f:
            line = line.strip()
            
            if '"game_id":' in line:
                game_id = line.split(':')[1].strip().replace(',', '')
            
            if '"team":' in line:
                team = line.split(':')[1].strip().replace('"', '').replace(',', '')

            if '"player":' in line:
                player = line.split(':')[1].strip().replace('"', '').replace(',', '')

            if '"is_goal": true' in line:
                print(f"Goal in game {game_id}, by {player} for {team}")

if __name__ == "__main__":
    validate_goals('nuevos_datos.json')
