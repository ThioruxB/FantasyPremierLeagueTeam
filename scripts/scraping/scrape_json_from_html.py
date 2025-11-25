import re
import json
import pandas as pd

def extract_json_from_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # The regex pattern from scr.ipynb, adjusted for direct Python execution
    regex_pattern = r"require\.config\.params\[\"args\"\]\s*=\s*({[\s\S]*?});"
    
    data_txt_matches = re.findall(regex_pattern, html)
    
    if not data_txt_matches:
        return {"error": "No JSON data found matching the pattern from scr.ipynb"}

    # The regex now captures the entire JSON object, so we take the first group
    data_txt = data_txt_matches[0]

    # Apply the string replacements from scr.ipynb to make it valid JSON
    data_txt = data_txt.replace('matchId', '"matchId"')
    data_txt = data_txt.replace('matchCentreData', '"matchCentreData"')
    data_txt = data_txt.replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"')
    data_txt = data_txt.replace('formationIdNameMappings', '"formationIdNameMappings"')
    # The original scr.ipynb had '};' replacement, but our regex captures up to '};' so it's not needed for the captured group.
    # However, if the captured group itself contains '};' it might be an issue. Let's keep it for robustness.
    data_txt = data_txt.replace('};', '}')

    try:
        json_data = json.loads(data_txt)

        # Process data and save to CSVs as in scr.ipynb
        events_dict = json_data["matchCentreData"]["events"]
        players_home_df = pd.DataFrame(json_data["matchCentreData"]['home']['players'])
        players_home_df["teamId"] = json_data["matchCentreData"]['home']['teamId']
        players_away_df = pd.DataFrame(json_data["matchCentreData"]['away']['players'])
        players_away_df["teamId"] = json_data["matchCentreData"]['away']['teamId']
        players_df = pd.concat([players_home_df, players_away_df])

        df_events = pd.DataFrame(events_dict)
        df_players = pd.DataFrame(players_df)

        df_events.to_csv('EventData.csv', index=False)
        df_players.to_csv('PlayerData.csv', index=False)

        return json_data
    except json.JSONDecodeError as e:
        return {"error": f"JSON decoding failed: {e}", "raw_extracted_text": data_txt}
    except KeyError as e:
        return {"error": f"Missing key in JSON data for CSV generation: {e}", "json_data": json_data}

if __name__ == "__main__":
    file_path = "pag1.html"
    extracted_data = extract_json_from_html(file_path)
    print(json.dumps(extracted_data, indent=2, ensure_ascii=False))

