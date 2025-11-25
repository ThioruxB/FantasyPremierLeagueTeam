import subprocess
import json
import os

def run_script_and_capture_output(script_path):
    # Ensure the script path is absolute
    full_script_path = os.path.join(os.getcwd(), script_path)
    result = subprocess.run(['python', full_script_path], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def generate_html_report():
    # 1. Run scrape_pag1.py and capture its output
    general_scrape_output = run_script_and_capture_output("scrape_pag1.py")

    # 2. Run scrape_json_from_html.py and capture its output (also generates CSVs)
    json_scrape_output = run_script_and_capture_output("scrape_json_from_html.py")

    # Extract data for HTML report
    metadata = general_scrape_output.get("metadata", {})
    text_content = general_scrape_output.get("text_content", "")
    links = general_scrape_output.get("links", [])
    images = general_scrape_output.get("images", [])
    
    # Format metadata for HTML
    meta_html = f"<h3>Título: {metadata.get('title', 'N/A')}</h3>\n"
    meta_html += "<h4>Meta Tags:</h4>\n<ul>\n"
    for meta_tag in metadata.get("meta_tags", []):
        attrs = ", ".join([f"<b>{k}</b>: {v}" for k, v in meta_tag.items()])
        meta_html += f"<li>{attrs}</li>\n"
    meta_html += "</ul>\n"

    # Format links for HTML
    links_html = "<h4>Enlaces:</h4>\n<ul>\n"
    for link in links:
        links_html += f"<li><a href=\"{link.get('href', '#')}\" target=\"_blank\">{link.get('text', 'N/A')}</a></li>\n"
    links_html += "</ul>\n"

    # Format images for HTML
    images_html = "<h4>Imágenes:</h4>\n<div class=\"image-grid\">\n"
    for image in images:
        images_html += f"<div class=\"image-item\"><img src=\"{image.get('src', '#')}\" alt=\"{image.get('alt', '')}\"><span>{image.get('alt', 'N/A')}</span></div>\n"
    images_html += "</div>\n"

    # Convert JSON data to a pretty-printed string for HTML
    json_data_pretty = json.dumps(json_scrape_output, indent=2, ensure_ascii=False)

    # Build HTML content using a list of strings and join them
    html_parts = []
    html_parts.append("<!DOCTYPE html>")
    html_parts.append("<html lang=\"es\">")
    html_parts.append("<head>")
    html_parts.append("    <meta charset=\"UTF-8\">")
    html_parts.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
    html_parts.append("    <title>Reporte de Web Scraping de pag1.html</title>")
    html_parts.append("    <style>")
    html_parts.append("        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: #f4f7f6; color: #333; }")
    html_parts.append("        .container { max-width: 1200px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }")
    html_parts.append("        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }")
    html_parts.append("        h2 { color: #34495e; margin-top: 25px; border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; }")
    html_parts.append("        h3, h4 { color: #34495e; }")
    html_parts.append("        pre { background-color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word; }")
    html_parts.append("        ul { list-style-type: disc; margin-left: 20px; padding: 0; }")
    html_parts.append("        li { margin-bottom: 8px; }")
    html_parts.append("        a { color: #3498db; text-decoration: none; }")
    html_parts.append("        a:hover { text-decoration: underline; }")
    html_parts.append("        .section { margin-bottom: 30px; padding: 15px; background-color: #fdfdfd; border-left: 5px solid #3498db; border-radius: 5px; }")
    html_parts.append("        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 15px; margin-top: 20px; }")
    html_parts.append("        .image-item { text-align: center; border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: #fff; }")
    html_parts.append("        .image-item img { max-width: 100px; height: auto; display: block; margin: 0 auto 10px auto; border-radius: 3px; }")
    html_parts.append("        .image-item span { font-size: 0.8em; color: #555; word-break: break-all; }")
    html_parts.append("        .collapsible { background-color: #3498db; color: white; cursor: pointer; padding: 12px; width: 100%; border: none; text-align: left; outline: none; font-size: 1.1em; margin-top: 10px; border-radius: 5px; transition: background-color 0.3s ease; }")
    html_parts.append("        .collapsible:hover { background-color: #2980b9; }")
    html_parts.append("        .collapsible:after { content: '\002B'; color: white; font-weight: bold; float: right; margin-left: 5px; }")
    html_parts.append("        .active-collapsible:after { content: '\2212'; }")
    html_parts.append("        .collapsible-content { padding: 0 18px; background-color: white; max-height: 0; overflow: hidden; transition: max-height 0.2s ease-out; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }")
    html_parts.append("    </style>")
    html_parts.append("</head>")
    html_parts.append("<body>")
    html_parts.append("    <div class=\"container\">")
    html_parts.append("        <h1>Reporte de Web Scraping de pag1.html</h1>")

    html_parts.append("        <div class=\"section\">")
    html_parts.append("            <h2>Metadatos HTML</h2>")
    html_parts.append(meta_html)
    html_parts.append("        </div>")

    html_parts.append("        <div class=\"section\">")
    html_parts.append("            <h2>Contenido de Texto General (sin dashboards ni publicidad)</h2>")
    html_parts.append("            <button type=\"button\" class=\"collapsible\">Ver/Ocultar Contenido</button>")
    html_parts.append("            <div class=\"collapsible-content\">")
    html_parts.append(f"                <pre>{text_content}</pre>") # f-string for text_content
    html_parts.append("            </div>")
    html_parts.append("        </div>")

    html_parts.append("        <div class=\"section\">")
    html_parts.append("            <h2>Enlaces Extraídos</h2>")
    html_parts.append(links_html)
    html_parts.append("        </div>")

    html_parts.append("        <div class=\"section\">")
    html_parts.append("            <h2>Imágenes Extraídas</h2>")
    html_parts.append(images_html)
    html_parts.append("        </div>")

    html_parts.append("        <div class=\"section\">")
    html_parts.append("            <h2>Datos JSON Detallados (según scr.ipynb)</h2>")
    html_parts.append("            <p>Este es el objeto JSON completo extraído que alimenta los dashboards de la página original.</p>")
    html_parts.append("            <button type=\"button\" class=\"collapsible\">Ver/Ocultar JSON</button>")
    html_parts.append("            <div class=\"collapsible-content\">")
    html_parts.append(f"                <pre>{json_data_pretty}</pre>") # f-string for json_data_pretty
    html_parts.append("            </div>")
    html_parts.append("        </div>")

    html_parts.append("        <div class=\"section\">")
    html_parts.append("            <h2>Archivos CSV Generados</h2>")
    html_parts.append("            <p>Se han creado los archivos <code>EventData.csv</code> y <code>PlayerData.csv</code> en el directorio del proyecto, conteniendo los datos procesados del JSON.</p>")
    html_parts.append("        </div>")

    html_parts.append("    </div>") # Close container

    html_parts.append("    <script>")
    html_parts.append("        var coll = document.getElementsByClassName(\"collapsible\");")
    html_parts.append("        var i;")
    html_parts.append("        for (i = 0; i < coll.length; i++) {")
    html_parts.append("            coll[i].addEventListener(\"click\", function() {")
    html_parts.append("                this.classList.toggle(\"active-collapsible\");")
    html_parts.append("                var content = this.nextElementSibling;")
    html_parts.append("                if (content.style.maxHeight){")
    html_parts.append("                    content.style.maxHeight = null;")
    html_parts.append("                } else {")
    html_parts.append("                    content.style.maxHeight = content.scrollHeight + \"px\";")
    html_parts.append("                }")
    html_parts.append("            });")
    html_parts.append("        }")
    html_parts.append("    </script>")
    html_parts.append("</body>")
    html_parts.append("</html>")

    html_content = "\n".join(html_parts)

    with open("scraped_output.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Reporte HTML generado en scraped_output.html")

if __name__ == "__main__":
    generate_html_report()