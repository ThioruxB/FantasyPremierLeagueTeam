
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba
import seaborn as sns
from pprint import pprint
import matplotlib.image as mpimg
import matplotlib.patches as patches
from PIL import Image
from io import BytesIO
import matplotlib as mpl
from matplotlib.gridspec import GridSpec
from matplotlib.markers import MarkerStyle
from mplsoccer import Pitch, VerticalPitch
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams
from matplotlib.patheffects import withStroke, Normal
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer.utils import FontManager
import matplotlib.patheffects as path_effects
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.cbook import get_sample_data
from sklearn.cluster import KMeans
import warnings
from highlight_text import ax_text
from datetime import datetime
import ast
from bs4 import BeautifulSoup

pd.set_option('display.max_columns', None)

green = '#69f900'
red = '#ffffff'
blue = '#999999'
violet = '#a369ff'
bg_color= '#999999'
line_color= '#000000'
col1 = '#ffffff'
col2 = '#e41a1c'

def extract_json_from_html(html, save_output=False):
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    data_txt = None
    for script in scripts:
        if script.string and 'require.config.params["args"]' in script.string:
            data_txt = script.string
            break

    if not data_txt:
        print("Error: Could not find the required data in the HTML file.")
        return None

    # A more robust way to find the data
    try:
        start_index = data_txt.index('require.config.params["args"] = {')
        # Find the closing }; for the args object
        end_index = data_txt.rfind('}') + 1
        data_txt = data_txt[start_index:end_index]
        data_txt = data_txt.split('=', 1)[1].strip()

    except ValueError:
        print("Error: Could not find the required data in the HTML file.")
        return None

    # It's not a valid JSON, it's a Javascript object. 
    # We need to make it a valid python dictionary.
    data_txt = re.sub(r'([{\s,])(\w+)(\s*:)', r'\1"\2"\3', data_txt)
    data_txt = data_txt.replace('true', 'True').replace('false', 'False')
    # fix the timestamp
    data_txt = data_txt.replace('"timeStamp":"2025-10-04 "17":13:13"', '"timeStamp":"2025-10-04T17:13:13"')
    data_txt = data_txt.replace('"timeStamp":"2025-10-06 "00":11:07"', '"timeStamp":"2025-10-06T00:11:07"')

    if save_output:
        # save json data to txt
        with open("extracted_data.txt", "w") as output_file:
            output_file.write(data_txt)

    return data_txt

def extract_data_from_dict(data):
    # load data from json
    event_types_json = data["matchCentreEventTypeJson"]
    formation_mappings = data["formationIdNameMappings"]
    events_dict = data["matchCentreData"]["events"]
    teams_dict = {data["matchCentreData"]['home']['teamId']: data["matchCentreData"]['home']['name'],
                  data["matchCentreData"]['away']['teamId']: data["matchCentreData"]['away']['name']}
    players_dict = data["matchCentreData"]["playerIdNameDictionary"]
    # create players dataframe
    players_home_df = pd.DataFrame(data["matchCentreData"]['home']['players'])
    players_home_df["teamId"] = data["matchCentreData"]['home']['teamId']
    players_away_df = pd.DataFrame(data["matchCentreData"]['away']['players'])
    players_away_df["teamId"] = data["matchCentreData"]['away']['teamId']
    players_df = pd.concat([players_home_df, players_away_df])
    players_ids = data["matchCentreData"]["playerIdNameDictionary"]
    return events_dict, players_df, teams_dict

def get_short_name(full_name):
    if pd.isna(full_name):
        return full_name
    parts = full_name.split()
    if len(parts) == 1:
        return full_name
    elif len(parts) == 2:
        return parts[0][0] + ". " + parts[1]
    else:
        return parts[0][0] + ". " + parts[1][0] + ". " + " ".join(parts[2:])

def parse_display_name(x):
    if isinstance(x, dict) and 'displayName' in x:
        return x['displayName']
    return x

def find_script_content_recursive(node):
    """Recursively searches for the script content in the JSON DOM."""
    if isinstance(node, dict):
        if node.get('tag') == 'script' and node.get('children'):
            for child in node['children']:
                if isinstance(child, dict) and 'text' in child:
                    if 'require.config.params["args"]' in child['text']:
                        return child['text']
        if node.get('children'):
            for child in node['children']:
                result = find_script_content_recursive(child)
                if result:
                    return result
    elif isinstance(node, list):
        for item in node:
            result = find_script_content_recursive(item)
            if result:
                return result
    return None

def extract_data_from_json_dom(json_dom_path):
    """Reads a JSON DOM representation and extracts the JavaScript object string."""
    try:
        with open(json_dom_path, 'r', encoding='utf-8') as f:
            dom_data = json.load(f)
        print(f"DOM JSON cargado exitosamente desde {json_dom_path}")
    except FileNotFoundError:
        print(f"Error: El archivo {json_dom_path} no fue encontrado.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON DOM desde {json_dom_path}: {e}")
        return None
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo JSON DOM: {e}")
        return None

    script_tag_content = find_script_content_recursive(dom_data)

    if not script_tag_content:
        print("Error: No se encontró el contenido del script con 'require.config.params[\"args\"]' en el JSON DOM.")
        return None

    # Apply the same cleaning and parsing logic as before
    try:
        start_index = script_tag_content.index('require.config.params["args"] = {')
        end_index = script_tag_content.rfind('}') + 1
        data_txt = script_tag_content[start_index:end_index]
        data_txt = data_txt.split('=', 1)[1].strip()

        data_txt = re.sub(r'([{\s,])(\w+)(\s*:)', r'\1"\2"\3', data_txt)
        data_txt = data_txt.replace('true', 'True').replace('false', 'False')
        data_txt = data_txt.replace('"timeStamp":"2025-10-04 "17":13:13"', '"timeStamp":"2025-10-04T17:13:13"')
        data_txt = data_txt.replace('"timeStamp":"2025-10-06 "00":11:07"', '"timeStamp":"2025-10-06T00:11:07"')
        
        data = ast.literal_eval(data_txt)
        return data
    except (ValueError, SyntaxError) as e:
        print(f"Error al procesar el contenido del script extraído del JSON DOM: {e}")
        return None

def main():
    json_dom_file_path = 'D:\\ConectPremier\\pag3.json'
    
    data = extract_data_from_json_dom(json_dom_file_path)
    
    if data is None:
        return

    events_dict, players_df, teams_dict = extract_data_from_dict(data)

    df = pd.DataFrame(events_dict)
    dfp = pd.DataFrame(players_df)

    df.to_csv('EventData.csv', index=False)
    dfp.to_csv('PlayerData.csv', index=False)

    print("Data extracted and saved to EventData.csv and PlayerData.csv")

if __name__ == '__main__':
    main()
