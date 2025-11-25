# Documentación del Proyecto de Web Scraping

## 1. Resumen del Proyecto

Este proyecto implica el web scraping de datos de partidos de WhoScored.com, la realización de un análisis exploratorio de datos (EDA) y la presentación de los resultados en un informe web fácil de usar.

## 2. Fuentes de Datos

-   **`pag3.html`**: El archivo HTML principal extraído de WhoScored.com, que contiene eventos detallados del partido, estadísticas de jugadores y metadatos del partido.
-   **`EventData.csv`**: Contiene datos detallados a nivel de evento para el partido, extraídos de `pag3.html`.
-   **`PlayerData.csv`**: Contiene datos detallados a nivel de jugador para el partido, extraídos de `pag3.html`.

## 3. Proceso de Web Scraping

El script `scraping_script.py` es responsable de:
1.  Leer el archivo `pag3.html`.
2.  Extraer un objeto JavaScript incrustado dentro de una etiqueta `<script>`, que contiene los datos principales del partido.
3.  Limpiar y analizar este objeto JavaScript (que no es JSON estricto) en un diccionario de Python utilizando `ast.literal_eval`.
4.  Transformar los datos extraídos en dos DataFrames de pandas: uno para los datos de eventos y otro para los datos de jugadores.
5.  Guardar estos DataFrames como `EventData.csv` y `PlayerData.csv`.

## 4. Informe Web (`index.html`)

El script `eda_web.py` genera un archivo `index.html` que sirve como un informe web completo. Este informe incluye:
-   **Sección de Metadatos**: Muestra información clave del partido, como el ID del partido, nombres de los equipos, resultados, fecha, lugar, árbitro y asistencia.
-   **Sección de Datos de Eventos**: Muestra las primeras 10 filas de `EventData.csv` en una tabla formateada.
-   **Sección de Datos de Jugadores**: Muestra las primeras 10 filas de `PlayerData.csv` en una tabla formateada.

El informe web está diseñado para ser visualmente atractivo, organizado y profesional, con tablas responsivas para una mejor legibilidad.

## 5. Análisis Exploratorio de Datos (EDA)

El script `eda.py` realiza un análisis exploratorio inicial de los datos en los archivos `EventData.csv` y `PlayerData.csv`. El EDA incluye:
-   Mostrar información básica del DataFrame (`.info()`, `.describe()`).
-   Identificar valores faltantes en cada columna.
-   Generar visualizaciones:
    -   `event_type_distribution.png`: Un gráfico de recuento que muestra la distribución de los diferentes tipos de eventos.
    -   `player_position_distribution.png`: Un gráfico de recuento que muestra la distribución de las posiciones de los jugadores.

## 6. Cómo Ejecutar el Proyecto

1.  **Asegurar Dependencias**: Asegúrese de que todas las bibliotecas de Python requeridas (pandas, beautifulsoup4, matplotlib, seaborn) estén instaladas. Puede instalarlas usando `pip install -r requirements.txt`.
2.  **Ejecutar Web Scraping**: Ejecute `python scraping_script.py` para extraer datos de `pag3.html` y generar `EventData.csv` y `PlayerData.csv`.
3.  **Realizar EDA**: Ejecute `python eda.py` para realizar el análisis exploratorio de datos y generar gráficos.
4.  **Generar Informe Web**: Ejecute `python eda_web.py` para crear el informe web `index.html`.
5.  **Ver Informe**: Abra `index.html` en su navegador web para ver el informe.