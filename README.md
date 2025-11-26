# ⚽ ConectPremier: Fantasy Premier League AI Assistant

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**ConectPremier** es un sistema avanzado de análisis de datos y machine learning diseñado para revolucionar la toma de decisiones en la Fantasy Premier League (FPL). Utilizando algoritmos de optimización matemática y modelos predictivos de última generación, este proyecto ofrece a los managers una ventaja competitiva basada en datos.

<table>
  <tr>
    <td align="center"><b>Detalle de Jugadores</b></td>
  </tr>
  <tr>
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

### Scraping de Datos de Partidos

El proyecto también incluye un script para realizar web scraping de datos detallados de un partido desde WhoScored.com y cargarlos en la base de datos.

-   **Fuente de Datos**: `pag3.json`, que contiene los datos de un partido.
-   **Script**: `scripts/insert_data_to_db.py`

Para ejecutar este proceso, utiliza el siguiente comando:

```bash
python scripts/insert_data_to_db.py
```

## Base de Datos

El sistema utiliza una base de datos PostgreSQL, alojada en [Neon](https://neon.tech/), para almacenar los datos históricos de jugadores y equipos. La configuración de la conexión está definida directamente en los scripts de la carpeta `src`. Si deseas utilizar tu propia base de datos, deberás actualizar la cadena de conexión en dichos archivos.

### Scripts de Datos Históricos

Adicionalmente, se han añadido scripts para trabajar con datos históricos de los jugadores:

-   `scripts/get_all_players_history_resumable.py`: Extrae de la API de FPL las estadísticas agregadas de las últimas dos temporadas de la carrera de cada jugador y las guarda en `all_players_history_resumable.csv`. El script es reanudable.
-   `scripts/upload_season_history.py`: Sube los datos del CSV anterior a una tabla `player_season_history` en la base de datos, diseñada para almacenar este historial.

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

El sistema utiliza una arquitectura de datos híbrida en PostgreSQL, dividida en dos esquemas lógicos principales: **Datos FPL (Fantasy Premier League)** y **Datos Detallados de Partidos (WhoScored)**.

### 1. Esquema FPL (Fantasy Premier League)
Este esquema almacena la información oficial de la API de la FPL, utilizada para el entrenamiento del modelo predictivo y la optimización de equipos.

#### Diagrama Relacional Simplificado
```mermaid
erDiagram
    TEAMS ||--o{ PLAYERS : "tiene"
    TEAMS ||--o{ FIXTURES : "juega como local"
    TEAMS ||--o{ FIXTURES : "juega como visitante"
    PLAYERS ||--o{ PLAYER_HISTORY : "tiene historial"
    GAMEWEEKS ||--o{ FIXTURES : "contiene"
    PLAYER_TYPES ||--o{ PLAYERS : "define posición"
```

#### Diccionario de Datos

**Tabla: `players`**
Almacena la información actual de cada jugador de la FPL.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | INT (PK) | Identificador único del jugador en la FPL. |
| `Nombre` | VARCHAR | Primer nombre del jugador. |
| `Apellido` | VARCHAR | Apellido del jugador. |
| `team_id` | INT (FK) | ID del equipo al que pertenece (Ref: `teams.id`). |
| `Posicion` | VARCHAR | Posición del jugador (GKP, DEF, MID, FWD). |
| `Precio` | FLOAT | Costo actual del jugador en la FPL. |
| `Puntos Totales` | INT | Puntos acumulados en la temporada actual. |
| `status` | VARCHAR | Estado de disponibilidad (a=available, d=doubtful, i=injured, etc.). |
| `chance_of_playing_next_round` | INT | Probabilidad (%) de jugar la próxima jornada. |

**Tabla: `teams`**
Información de los clubes de la Premier League.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | INT (PK) | Identificador único del equipo. |
| `name` | VARCHAR | Nombre completo del equipo (ej. Arsenal). |
| `short_name` | VARCHAR | Abreviatura del equipo (ej. ARS). |
| `strength` | INT | Fuerza general del equipo (1-5). |

**Tabla: `player_history`**
Historial de rendimiento partido a partido para cada jugador.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `element` | INT (FK) | ID del jugador (Ref: `players.id`). |
| `fixture` | INT (FK) | ID del partido (Ref: `fixtures.id`). |
| `total_points` | INT | Puntos obtenidos en ese partido. |
| `minutes` | INT | Minutos jugados. |
| `goals_scored` | INT | Goles marcados. |
| `assists` | INT | Asistencias realizadas. |
| `clean_sheets` | INT | Porterías a cero. |
| `bps` | INT | Bonus Points System. |

**Tabla: `fixtures`**
Calendario de partidos.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | INT (PK) | Identificador único del partido. |
| `event` | INT (FK) | ID de la jornada (Ref: `gameweeks.id`). |
| `team_h` | INT (FK) | ID del equipo local (Ref: `teams.id`). |
| `team_a` | INT (FK) | ID del equipo visitante (Ref: `teams.id`). |
| `kickoff_time` | TIMESTAMP | Fecha y hora del partido. |

---

### 2. Esquema de Datos Detallados (Match Events)
Este esquema almacena datos granulares de eventos de partidos (pases, disparos, entradas) obtenidos mediante web scraping, permitiendo un análisis táctico profundo.

#### Diagrama Relacional Simplificado
```mermaid
erDiagram
    EQUIPOS ||--o{ JUGADORES : "tiene"
    EQUIPOS ||--o{ PARTIDOS : "local"
    EQUIPOS ||--o{ PARTIDOS : "visitante"
    PARTIDOS ||--o{ EVENTOS : "genera"
    PARTIDOS ||--o{ FORMACIONES : "tiene"
    JUGADORES ||--o{ EVENTOS : "realiza"
```

#### Diccionario de Datos

**Tabla: `partidos`**
Metadatos de cada encuentro procesado.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id_partido` | BIGINT (PK) | ID único del partido (origen externo). |
| `fecha_inicio` | DATE | Fecha del partido. |
| `marcador` | VARCHAR | Resultado final (ej. "2 : 1"). |
| `nombre_estadio` | VARCHAR | Estadio donde se jugó. |
| `nombre_arbitro` | VARCHAR | Nombre del árbitro principal. |

**Tabla: `eventos`**
Registro de cada acción que ocurre en el campo (aprox. 1500-2000 por partido).

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id_evento` | BIGINT (PK) | ID único del evento. |
| `id_partido` | BIGINT (FK) | Partido al que pertenece. |
| `minuto` | INT | Minuto del evento (0-90+). |
| `tipo` | VARCHAR | Tipo de evento (Pass, Shot, Tackle, Save, etc.). |
| `x`, `y` | NUMERIC | Coordenadas (0-100) de la posición del evento en el campo. |
| `es_gol` | BOOLEAN | Indica si el evento resultó en gol. |
| `es_disparo` | BOOLEAN | Indica si el evento fue un disparo. |

**Tabla: `jugadores` (Schema Detallado)**
Mapeo de jugadores específico para los datos de eventos.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id_jugador` | BIGINT (PK) | ID único del jugador. |
| `nombre` | VARCHAR | Nombre del jugador. |
| `posicion` | VARCHAR | Posición táctica (ej. DC, MC, DFC). |
| `altura` | INT | Altura en cm. |
| `peso` | INT | Peso en kg. |

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
