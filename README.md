# ⚽ ConectPremier: Fantasy Premier League AI Assistant

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**ConectPremier** es un sistema avanzado de análisis de datos y machine learning diseñado para revolucionar la toma de decisiones en la Fantasy Premier League (FPL). Utilizando algoritmos de optimización matemática y modelos predictivos de última generación, este proyecto ofrece a los managers una ventaja competitiva basada en datos.

<table>
  <tr>
    <td align="center"><b>Dashboard de Análisis</b></td>
    <td align="center"><b>Detalle de Jugadores</b></td>
  </tr>
  <tr>
    <td><img src="data/output/eda.html" alt="Dashboard Demo" width="420"></td>
    <td><img src="img/demos2.png" alt="Player Detail Demo" width="420"></td>
  </tr>
</table>

---

## 🚀 Características Principales

*   **🔮 Predicción de Puntos Esperados (xP)**: Modelo de Gradient Boosting entrenado con datos históricos para predecir el rendimiento futuro de cada jugador.
*   **🧠 Optimización de Plantilla (ILP)**: Algoritmos de Programación Lineal Entera (PuLP) para seleccionar el equipo matemáticamente óptimo bajo las restricciones de presupuesto y reglas de la FPL.
*   **🎲 Simulación de Monte Carlo**: Análisis de robustez que simula miles de escenarios para recomendar equipos que no solo son buenos en promedio, sino consistentes y de bajo riesgo.
*   **🔄 Pipeline ETL Automatizado**: Extracción, transformación y carga de datos desde la API oficial de la FPL y fuentes externas (WhoScored) de forma totalmente automatizada.
*   **📊 Análisis de Volatilidad**: Métricas avanzadas para evaluar la consistencia de los jugadores y evitar "trampas" de puntos.

---

## 📂 Estructura del Proyecto

El proyecto ha sido reorganizado para seguir las mejores prácticas de ingeniería de software:

```text
ConectPremier/
├── 📁 data/                  # Almacenamiento de datos
│   ├── 📁 raw/               # Datos crudos (CSVs, JSONs de la API)
│   ├── 📁 processed/         # Datos limpios y enriquecidos para el modelo
│   └── 📁 output/            # Reportes generados, gráficos y logs
├── 📁 scripts/               # Scripts utilitarios y de ejecución
│   ├── 📁 etl/               # Scripts de limpieza y carga de datos
│   ├── 📁 scraping/          # Scrapers para obtener datos externos
│   ├── 📁 analysis/          # Scripts de análisis exploratorio (EDA)
│   └── 📁 web/               # Scripts para la interfaz web
├── 📁 src/                   # Código fuente principal (Core Logic)
│   ├── data_pipeline.py      # Orquestador del flujo de datos
│   ├── feature_engineering.py# Ingeniería de características
│   ├── model_training.py     # Entrenamiento del modelo predictivo
│   └── team_selection.py     # Lógica de optimización de equipos
├── 📁 sql/                   # Scripts SQL para gestión de base de datos
├── 📁 web/                   # Interfaz web (HTML/JS)
├── 📁 notebooks/             # Jupyter Notebooks para experimentación
└── 📄 run_project.py         # Punto de entrada principal
```

---

## 🛠️ Instalación y Configuración

### Prerrequisitos

*   Python 3.8 o superior
*   PostgreSQL (Base de datos)
*   Cuenta de Neon Tech (Opcional, si se usa la configuración por defecto)

### Pasos de Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/ConectPremier.git
    cd ConectPremier
    ```

2.  **Crear un entorno virtual (Recomendado):**
    ```bash
    python -m venv venv
    # En Windows:
    .\venv\Scripts\activate
    # En macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno:**
    Crea un archivo `.env` o configura tus variables de entorno para la conexión a la base de datos:
    ```env
    DB_CONNECTION_STRING=postgresql://usuario:password@host/dbname
    ```

<<<<<<< HEAD
### Scraping de Datos de Partidos

El proyecto también incluye un script para realizar web scraping de datos detallados de un partido desde WhoScored.com y cargarlos en la base de datos.

-   **Fuente de Datos**: `pag3.json`, que contiene los datos de un partido.
-   **Script**: `insert_data_to_db.py`

Para ejecutar este proceso, utiliza el siguiente comando:

```bash
python insert_data_to_db.py
```

## Base de Datos

El sistema utiliza una base de datos PostgreSQL, alojada en [Neon](https://neon.tech/), para almacenar los datos históricos de jugadores y equipos. La configuración de la conexión está definida directamente en los scripts de la carpeta `src`. Si deseas utilizar tu propia base de datos, deberás actualizar la cadena de conexión en dichos archivos.

### Scripts de Datos Históricos

Adicionalmente, se han añadido scripts para trabajar con datos históricos de los jugadores:

-   `scripts/get_all_players_history_resumable.py`: Extrae de la API de FPL las estadísticas agregadas de las últimas dos temporadas de la carrera de cada jugador y las guarda en `all_players_history_resumable.csv`. El script es reanudable.
-   `scripts/upload_season_history.py`: Sube los datos del CSV anterior a una tabla `player_season_history` en la base de datos, diseñada para almacenar este historial.

=======
>>>>>>> 28b92f7 (Actualización del proyecto)
---

## 💻 Guía de Uso

### 1. Ejecución Completa (Recomendado)
Para correr todo el pipeline (descarga de datos, procesamiento, entrenamiento y recomendación):

```bash
python run_project.py
```

### 2. Recomendación Rápida
Si ya tienes los datos procesados y solo quieres generar una nueva recomendación de equipo:

```bash
python recommend_team.py
```

### 3. Actualización de Datos Externos
Para actualizar la base de datos con los últimos partidos y estadísticas de WhoScored:

```bash
python run_update.py
```

---

## 📊 Flujo de Datos y Metodología

1.  **Ingesta**: `scripts/scraping/scrape_soccerdata.py` y `src/data_pipeline.py` obtienen datos crudos.
2.  **Procesamiento**: `scripts/etl/clean_data.py` limpia y normaliza los datos.
3.  **Ingeniería de Características**: `src/feature_engineering.py` calcula métricas clave como *Forma*, *Dificultad de Calendario* y *Volatilidad*.
4.  **Modelado**: `src/model_training.py` entrena un modelo Gradient Boosting para predecir puntos.
5.  **Optimización**: `src/team_selection.py` utiliza PuLP para resolver el problema de la mochila (Knapsack Problem) aplicado a la FPL.

---

## 🗄️ Esquema de Base de Datos

El sistema utiliza un esquema relacional robusto en PostgreSQL:

*   **`players`**: Información estática de los jugadores.
*   **`teams`**: Datos de los equipos de la Premier League.
*   **`fixtures`**: Calendario de partidos y resultados.
*   **`player_history`**: Rendimiento histórico partido a partido.
*   **`gameweeks`**: Información sobre las jornadas de la FPL.

---

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar el modelo o nuevas características:

1.  Haz un Fork del proyecto.
2.  Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`).
3.  Haz Commit de tus cambios (`git commit -m 'Add some AmazingFeature'`).
4.  Haz Push a la rama (`git push origin feature/AmazingFeature`).
5.  Abre un Pull Request.

---

## 📄 Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para más información.

---

<div align="center">
  <sub>Construido con ❤️ por el equipo de ConectPremier</sub>
</div>