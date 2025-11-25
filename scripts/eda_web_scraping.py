
import pandas as pd
from bs4 import BeautifulSoup
import re
import ast

def extract_metadata_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    metadata = {}

    # Extract data from the script tag containing require.config.params["args"]
    script_tag_content = None
    for script in soup.find_all('script'):
        if script.string and 'require.config.params["args"]' in script.string:
            script_tag_content = script.string
            break

    if script_tag_content:
        try:
            # Extract the JSON-like string
            start_index = script_tag_content.index('require.config.params["args"] = {')
            end_index = script_tag_content.rfind('}') + 1
            json_like_str = script_tag_content[start_index:end_index]
            json_like_str = json_like_str.split('=', 1)[1].strip()
            
            # Clean and parse the string
            json_like_str = re.sub(r'([{\s,])(\w+)(\s*:)', r'\1"\2"\3', json_like_str)
            json_like_str = json_like_str.replace('true', 'True').replace('false', 'False')
            json_like_str = json_like_str.replace('"timeStamp":"2025-10-04 "17":13:13"', '"timeStamp":"2025-10-04T17:13:13"')
            json_like_str = json_like_str.replace('"timeStamp":"2025-10-06 "00":11:07"', '"timeStamp":"2025-10-06T00:11:07"')
            
            data = ast.literal_eval(json_like_str)

            # Populate metadata dictionary
            metadata['Match ID'] = data.get('matchId')
            
            match_centre_data = data.get('matchCentreData', {})
            home_team = match_centre_data.get('home', {})
            away_team = match_centre_data.get('away', {})
            referee_data = match_centre_data.get('referee', {})

            metadata['Home Team'] = home_team.get('name')
            metadata['Away Team'] = away_team.get('name')
            metadata['Score'] = match_centre_data.get('score')
            metadata['Half-time Score'] = match_centre_data.get('htScore')
            metadata['Full-time Score'] = match_centre_data.get('ftScore')
            metadata['Elapsed Time'] = match_centre_data.get('elapsed')
            metadata['Start Time'] = match_centre_data.get('startTime')
            metadata['Start Date'] = match_centre_data.get('startDate')
            metadata['Attendance'] = match_centre_data.get('attendance')
            metadata['Venue Name'] = match_centre_data.get('venueName')
            metadata['Referee'] = f"{referee_data.get('firstName')} {referee_data.get('lastName')}" if referee_data.get('firstName') else None
            metadata['Weather Code'] = match_centre_data.get('weatherCode')

        except (ValueError, SyntaxError) as e:
            print(f"Error parsing script tag content for metadata: {e}")
            # Fallback to simpler extraction if parsing fails
            # This part remains for robustness, though the above should be more comprehensive
            pass

    # Fallback/additional extraction from HTML structure if not found in script or for other elements
    if not metadata.get('Home Team') or not metadata.get('Away Team') or not metadata.get('Score'):
        match_header = soup.find(id='match-header')
        if match_header:
            teams = match_header.find_all('a', class_='team-link')
            if len(teams) == 2:
                metadata['Home Team'] = metadata.get('Home Team', teams[0].get_text(strip=True))
                metadata['Away Team'] = metadata.get('Away Team', teams[1].get_text(strip=True))
            score = match_header.find('td', class_='result')
            if score:
                metadata['Score'] = metadata.get('Score', score.get_text(strip=True))

    if not metadata.get('Date') or not metadata.get('Venue Name'):
        info_blocks = soup.find_all('div', class_='info-block')
        for block in info_blocks:
            dt_tags = block.find_all('dt')
            dd_tags = block.find_all('dd')
            for i in range(len(dt_tags)):
                if dt_tags[i].get_text(strip=True) == 'Date:':
                    metadata['Date'] = metadata.get('Date', dd_tags[i].get_text(strip=True))
                elif dt_tags[i].get_text(strip=True) == 'Venue:':
                    metadata['Venue Name'] = metadata.get('Venue Name', dd_tags[i].get_text(strip=True))

    return metadata

def generate_html_report(metadata, event_data_df, player_data_df):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Web Scraping Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: #eef2f7; color: #333; line-height: 1.6; }}
            .container {{ max-width: 1200px; margin: 20px auto; background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            h1 {{ color: #004085; text-align: center; margin-bottom: 30px; border-bottom: 2px solid #004085; padding-bottom: 10px; }}
            h2 {{ color: #0056b3; margin-top: 30px; border-bottom: 1px solid #e0e0e0; padding-bottom: 5px; }}
            section {{ margin-bottom: 25px; }}

            .metadata-table table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; background-color: #f8f9fa; border-radius: 8px; overflow: hidden; }}
            .metadata-table th, .metadata-table td {{ border: 1px solid #dee2e6; padding: 12px 15px; text-align: left; }}
            .metadata-table th {{ background-color: #e9ecef; font-weight: bold; width: 30%; color: #495057; }}
            .metadata-table td {{ background-color: #fff; }}

            .data-section {{ overflow-x: auto; }} /* Make section horizontally scrollable */
            .data-section table {{ width: 100%; min-width: 800px; border-collapse: collapse; margin-bottom: 20px; font-size: 0.85em; background-color: #f8f9fa; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .data-section th, .data-section td {{ border: 1px solid #dee2e6; padding: 8px 10px; text-align: left; white-space: nowrap; }}
            .data-section th {{ background-color: #007bff; color: #fff; font-weight: bold; position: sticky; top: 0; z-index: 1; }}
            .data-section tbody tr:nth-child(even) {{ background-color: #e9f2fa; }}
            .data-section tbody tr:hover {{ background-color: #cce5ff; transition: background-color 0.3s ease; cursor: pointer; }}
            .data-section td {{ background-color: #fff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Web Scraping Report</h1>
            
            <section class="metadata-section">
                <h2>Metadata</h2>
                <div class="metadata-table">
                    <table>
                        <tbody>
    """;

    for key, value in metadata.items():
        html_content += f"""
                            <tr>
                                <th>{key}</th>
                                <td>{value if value is not None else 'N/A'}</td>
                            </tr>
        """
    
    html_content += f"""
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="data-section">
                <h2>Event Data (First 10 Rows)</h2>
                {event_data_df.head(10).to_html(classes='data-table', index=False)}
            </section>

            <section class="data-section">
                <h2>Player Data (First 10 Rows)</h2>
                {player_data_df.head(10).to_html(classes='data-table', index=False)}
            </section>
        </div>
    </body>
    </html>
    """;
    return html_content

def main():
    # Read HTML content from pag3.html
    html_file_path = 'D:\\ConectPremier\\pag3.html'
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract metadata
    metadata = extract_metadata_from_html(html_content)

    # Read CSV data
    event_data_df = pd.read_csv('EventData.csv')
    player_data_df = pd.read_csv('PlayerData.csv')

    # Generate HTML report
    html_report = generate_html_report(metadata, event_data_df, player_data_df)

    # Write HTML report to index.html
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_report)

    print("Web scraping report generated successfully in index.html")

if __name__ == '__main__':
    main()
