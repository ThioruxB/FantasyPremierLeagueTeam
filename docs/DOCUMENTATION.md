# Documentación Técnica del Proyecto FPL

## 1. Introducción

Este documento proporciona una descripción técnica completa del sistema de recomendación para Fantasy Premier League (FPL). El objetivo es detallar la arquitectura, el flujo de datos, la configuración y el propósito de cada componente del proyecto.

---

## 2. Arquitectura y Estructura del Proyecto

El proyecto adopta una estructura de directorios estándar que separa las responsabilidades, facilitando el mantenimiento y la claridad.

```
. 
├── data/                 # Almacena datos generados por el pipeline (ej. resultados_fase2.csv).
├── docs/                 # Contiene esta documentación.
├── outputs/              # Destino para salidas no-tabulares como imágenes o reportes.
├── scripts/              # Scripts auxiliares, de análisis exploratorio (EDA) o pruebas.
├── src/                  # El código fuente principal de la aplicación.
│   ├── __init__.py       # Convierte a src en un paquete de Python.
│   ├── data_pipeline.py  # Fase 1: Extrae y carga datos de la API de FPL a la BD.
│   ├── feature_engineering.py # Fase 2: Calcula métricas como forma y dificultad.
│   ├── model_training.py # Fase 3: Entrena el modelo y predice puntos esperados (xP).
│   └── team_selection.py # Fase 4: Selecciona el equipo óptimo y genera explicaciones.
├── .gitignore            # Especifica los archivos que Git debe ignorar.
├── README.md             # Guía de inicio rápido.
├── requirements.txt      # Lista de dependencias de Python para el proyecto.
└── run_project.py        # Script maestro que orquesta todo el pipeline.
```

---

## 3. Configuración y Puesta en Marcha

Sigue estos pasos para configurar y ejecutar el proyecto en un nuevo entorno.

### 3.1. Requisitos Previos

- Python 3.8 o superior.
- Git para clonar el repositorio.

### 3.2. Instalación

1.  **Clonar el Repositorio:**
    ```bash
    git clone <URL-DEL-REPOSITORIO>
    cd <NOMBRE-DEL-DIRECTORIO>
    ```

2.  **Crear un Entorno Virtual (Recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar Dependencias:**
    El archivo `requirements.txt` contiene todas las bibliotecas necesarias.
    ```bash
    pip install -r requirements.txt
    ```

### 3.3. Configuración de la Base de Datos (NeonDB)

El proyecto está pre-configurado para usar una base de datos PostgreSQL gratuita alojada en **Neon**.

- **Cadena de Conexión:** La conexión a la base de datos está codificada en los scripts dentro de `src/`. La URL utilizada es:
  ```
  postgresql://neondb_owner:npg_siXJHlLYwC10@ep-muddy-mode-ad05g277-pooler.c-2.us-east-1.aws.neon.tech/neondb
  ```
- **Uso Propio:** Si deseas utilizar tu propia instancia de PostgreSQL, deberás reemplazar esta cadena de conexión en todos los scripts que la contengan dentro de la carpeta `src/`.

---

## 4. Cómo Usar el Proyecto

La ejecución del proyecto se ha simplificado a un único comando gracias al script maestro `run_project.py`.

```bash
python run_project.py
```

Este comando ejecutará secuencialmente todas las fases del pipeline:
1.  Actualizará los datos desde la API de FPL.
2.  Calculará las nuevas métricas.
3.  Re-entrenará el modelo y predecirá los puntos.
4.  Seleccionará el equipo óptimo.
5.  Finalmente, imprimirá en la consola la alineación recomendada, el capitán, el vicecapitán y los suplentes.

---

## 5. El Pipeline Explicado a Fondo

Cada fase del pipeline es un script independiente dentro de la carpeta `src/`, diseñado para una tarea específica.

### Fase 1: `src/data_pipeline.py`
- **Propósito:** Extraer los datos más recientes de la API de FPL y cargarlos en la base de datos Neon.
- **Proceso:** 
    1. Se conecta a la API de FPL.
    2. Descarga datos de jugadores, equipos e historial de partidos.
    3. Limpia y formatea los datos.
    4. Sube los datos limpios a las tablas correspondientes en la base de datos PostgreSQL, sobrescribiendo la información anterior para mantenerla actualizada.

### Fase 2: `src/feature_engineering.py`
- **Propósito:** Tomar los datos básicos y enriquecerlos con métricas de rendimiento (ingeniería de características).
- **Proceso:**
    1. Carga los datos de la base de datos.
    2. Calcula el **estado de forma (`form`)** de cada jugador (promedio de puntos en los últimos 5 partidos).
    3. Calcula la **dificultad del próximo partido (`difficulty`)** basándose en la fortaleza del oponente.
    4. Genera un archivo `data/resultados_fase2.csv` con los datos enriquecidos.

### Fase 3: `src/model_training.py`
- **Propósito:** Predecir el rendimiento futuro de los jugadores.
- **Proceso:**
    1. Carga los datos de la fase anterior y el historial completo de la base de datos.
    2. **Entrena un modelo de Machine Learning** (Gradient Boosting Regressor) para aprender la relación entre la forma, la dificultad y los puntos obtenidos.
    3. Usa el modelo para predecir los **Puntos Esperados (xP)** para la siguiente jornada.
    4. Guarda los resultados, incluyendo los xP, en `data/resultados_fase3.csv`.

### Fase 4: `src/team_selection.py`
- **Propósito:** Construir el equipo óptimo y presentar los resultados.
- **Proceso:**
    1. Carga los datos con las predicciones de xP.
    2. Resuelve un **problema de optimización matemática** para encontrar la combinación de 15 jugadores que maximiza el `xP` total, sujeto a las restricciones de presupuesto y formación de FPL.
    3. Genera una explicación basada en reglas para cada jugador seleccionado.
    4. Guarda el equipo final en `data/equipo_ideal.csv` y lo muestra en consola.

---

## 6. Extracción de Datos de Partidos y Carga a la Base de Datos (Scraping)

Además del pipeline de FPL, el proyecto incluye un sistema para extraer datos detallados de partidos de WhoScored.com, procesarlos y cargarlos en la base de datos PostgreSQL. Este proceso es fundamental para análisis más profundos a nivel de evento.

### 6.1. Proceso de Web Scraping

El web scraping se centra en la extracción de datos de un partido específico desde WhoScored.

-   **Fuente de Datos**: El archivo `pag3.json` contiene una representación DOM del HTML de la página de un partido de WhoScored. Dentro de este JSON se encuentra un bloque de script con todos los datos del partido (eventos, jugadores, formaciones, etc.).
-   **Extracción**: El script `insert_data_to_db.py` lee `pag3.json`, localiza y extrae el objeto JavaScript que contiene los datos del partido.
-   **Procesamiento**: Los datos extraídos se limpian, procesan y estructuran en DataFrames de pandas para su posterior inserción en la base de datos.

### 6.2. Script de Inserción de Datos (`insert_data_to_db.py`)

Este script es el responsable de orquestar todo el proceso de scraping y carga de datos a la base de datos.

-   **Propósito**: Extraer los datos del archivo `pag3.json`, crear el esquema de tablas necesario en la base de datos y cargar los datos del partido.
-   **Proceso**:
    1.  **Conexión a la BD**: Se conecta a la base de datos PostgreSQL definida en `DATABASE_URL`.
    2.  **Creación de Tablas**: Ejecuta sentencias `CREATE TABLE IF NOT EXISTS` para asegurar que las tablas `equipos`, `jugadores`, `partidos`, `eventos` y `formaciones` existan.
    3.  **Extracción de Datos**: Lee y procesa el archivo `pag3.json` para obtener los datos del partido.
    4.  **Inserción de Datos**: Inserta los datos en las tablas en el orden correcto para respetar las restricciones de llaves foráneas:
        -   `equipos`
        -   `jugadores`
        -   `partidos`
        -   `formaciones`
        -   `eventos`
-   **Uso**:
    ```bash
    python insert_data_to_db.py
    ```

### 6.3. Esquema de la Base de Datos de Scraping

A continuación se detalla el esquema de las tablas creadas por el script `insert_data_to_db.py`.

#### Tabla: `equipos`
```sql
CREATE TABLE IF NOT EXISTS equipos (
    id_equipo BIGINT PRIMARY KEY,
    nombre_equipo VARCHAR(255) NOT NULL
);
```

#### Tabla: `jugadores`
```sql
CREATE TABLE IF NOT EXISTS jugadores (
    id_jugador BIGINT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    numero_camiseta INTEGER,
    posicion VARCHAR(50),
    altura INTEGER,
    peso INTEGER,
    edad INTEGER,
    es_titular BOOLEAN,
    es_hombre_del_partido BOOLEAN,
    campo VARCHAR(50),
    id_equipo BIGINT NOT NULL,
    FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo)
);
```

#### Tabla: `partidos`
```sql
CREATE TABLE IF NOT EXISTS partidos (
    id_partido BIGINT PRIMARY KEY,
    id_equipo_local BIGINT NOT NULL,
    id_equipo_visitante BIGINT NOT NULL,
    marcador VARCHAR(10),
    marcador_medio_tiempo VARCHAR(10),
    marcador_tiempo_completo VARCHAR(10),
    tiempo_transcurrido VARCHAR(50),
    hora_inicio TIMESTAMP,
    fecha_inicio DATE,
    asistencia INTEGER,
    nombre_estadio VARCHAR(255),
    nombre_arbitro VARCHAR(255),
    apellido_arbitro VARCHAR(255),
    codigo_clima VARCHAR(50),
    FOREIGN KEY (id_equipo_local) REFERENCES equipos(id_equipo),
    FOREIGN KEY (id_equipo_visitante) REFERENCES equipos(id_equipo)
);
```

#### Tabla: `eventos`
```sql
CREATE TABLE IF NOT EXISTS eventos (
    id_evento BIGINT PRIMARY KEY,
    id_partido BIGINT NOT NULL,
    minuto INTEGER,
    segundo INTEGER,
    id_equipo BIGINT NOT NULL,
    id_jugador BIGINT,
    x NUMERIC(5,2),
    y NUMERIC(5,2),
    minuto_expandido INTEGER,
    periodo VARCHAR(50),
    tipo VARCHAR(50),
    tipo_resultado VARCHAR(50),
    calificadores TEXT,
    tipos_eventos_satisfechos TEXT,
    es_toque BOOLEAN,
    fin_x NUMERIC(5,2),
    fin_y NUMERIC(5,2),
    id_evento_relacionado BIGINT,
    id_jugador_relacionado BIGINT,
    x_bloqueado NUMERIC(5,2),
    y_bloqueado NUMERIC(5,2),
    z_boca_porteria NUMERIC(5,2),
    y_boca_porteria NUMERIC(5,2),
    es_disparo BOOLEAN,
    es_gol BOOLEAN,
    tipo_tarjeta VARCHAR(50),
    FOREIGN KEY (id_partido) REFERENCES partidos(id_partido),
    FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo),
    FOREIGN KEY (id_jugador) REFERENCES jugadores(id_jugador),
    FOREIGN KEY (id_evento_relacionado) REFERENCES eventos(id_evento),
    FOREIGN KEY (id_jugador_relacionado) REFERENCES jugadores(id_jugador)
);
```

#### Tabla: `formaciones`
```sql
CREATE TABLE IF NOT EXISTS formaciones (
    id_formacion BIGSERIAL PRIMARY KEY,
    id_partido BIGINT NOT NULL,
    id_equipo BIGINT NOT NULL,
    nombre_formacion VARCHAR(50),
    id_jugador_capitan BIGINT,
    periodo VARCHAR(50),
    minuto_inicio_expandido INTEGER,
    minuto_fin_expandido INTEGER,
    numeros_camiseta TEXT,
    slots_formacion TEXT,
    ids_jugadores TEXT,
    posiciones_formacion TEXT,
    FOREIGN KEY (id_partido) REFERENCES partidos(id_partido),
    FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo),
    FOREIGN KEY (id_jugador_capitan) REFERENCES jugadores(id_jugador)
);
```

## 7. Scripts de Datos Históricos

Se han desarrollado scripts adicionales, ubicados en la carpeta `scripts/`, para la extracción y gestión de datos históricos de rendimiento de los jugadores a lo largo de diferentes temporadas.

### 6.1. Extracción de Historial por Temporada (`scripts/get_all_players_history_resumable.py`)

-   **Propósito:** Este script extrae de la API de FPL las estadísticas agregadas por temporada para todos los jugadores. Específicamente, guarda las últimas dos temporadas registradas en la carrera de cada jugador.
-   **Salida:** Genera un archivo `all_players_history_resumable.csv` en el directorio raíz del proyecto.
-   **Características:**
    -   **Reanudable:** Si el script es interrumpido, al volver a ejecutarlo, continuará desde donde se quedó, sin perder el progreso.
    -   **Respetuoso con la API:** Incluye una pausa de 1 segundo entre solicitudes para evitar el bloqueo de la API.
-   **Uso:**
    ```bash
    python scripts/get_all_players_history_resumable.py
    ```

### 6.2. Carga de Historial a la Base de Datos (`scripts/upload_season_history.py`)

-   **Propósito:** Sube los datos del archivo CSV generado por el script anterior a una tabla permanente en la base de datos Neon.
-   **Proceso:**
    1.  Se conecta a la base de datos usando la configuración del proyecto.
    2.  Asegura que la tabla `player_season_history` exista. Si no, la crea con la estructura adecuada.
    3.  Utiliza una estrategia de "upsert" (actualizar o insertar) para cargar los datos. Esto evita la creación de registros duplicados si el script se ejecuta varias veces.
    4.  Este proceso es seguro y no afecta a ninguna otra tabla de la base de datos.
-   **Uso:**
    ```bash
    python scripts/upload_season_history.py
    ```

### 6.3. Esquema de la Tabla `player_season_history`

Esta es la estructura de la tabla creada para almacenar los datos históricos por temporada.

```sql
CREATE TABLE IF NOT EXISTS player_season_history (
    player_id INT,
    player_name VARCHAR(255),
    season_name VARCHAR(50),
    total_points INT,
    minutes INT,
    goals_scored INT,
    assists INT,
    clean_sheets INT,
    goals_conceded INT,
    bonus INT,
    yellow_cards INT,
    red_cards INT,
    PRIMARY KEY (player_id, season_name)
);
```

---

## 7. Flujo de Trabajo de Scraping Mensual (WhoScored)

Se ha añadido un sistema robusto para la ingesta de datos históricos de partidos, mes a mes, utilizando `soccerdata` como motor de scraping para el sitio WhoScored.

### 7.1. Propósito

El objetivo es construir una base de datos histórica y detallada con información de partidos, incluyendo eventos específicos como goles, tarjetas, etc. Este flujo de trabajo está diseñado para ser ejecutado periódicamente (ej. cada mes) para añadir nuevos datos a los ya existentes.

### 7.2. Scripts Involucrados

1.  **`scrape_soccerdata.py`**
    -   **Función:** Script principal de scraping. Se debe modificar manualmente cada mes para apuntar al mes correcto (ej. `schedule['date'].dt.month == 10`) y al archivo de salida correspondiente (ej. `whoscored_data_october.json`).
    -   **Ejecución:** `python scrape_soccerdata.py`

2.  **`consolidate_all.py`**
    -   **Función:** Script de consolidación. Lee todos los archivos JSON mensuales generados hasta la fecha y crea un único conjunto de 5 archivos CSV maestros (`competiciones.csv`, `equipos.csv`, `jugadores.csv`, `partidos.csv`, `incidentes.csv`). Este proceso unifica todos los datos y resuelve duplicados.
    -   **Ejecución:** `python consolidate_all.py`

3.  **`load_all_data.sql`**
    -   **Función:** Script SQL para la carga final. Realiza un reseteo completo de las tablas en la base de datos y carga los datos desde los 5 CSVs maestros generados en el paso anterior.
    -   **Ejecución:** `psql "YOUR_CONNECTION_STRING" -f load_all_data.sql`

### 7.3. Esquema de Base de Datos (WhoScored)

Las siguientes tablas fueron diseñadas para almacenar los datos extraídos de WhoScored.

#### Tabla: `competiciones`
Almacena las competiciones o ligas.

| Columna              | Tipo de Dato | Descripción                        |
| -------------------- | ------------ | ---------------------------------- |
| `competicion_id`     | `INT`        | ID único de la competición.        |
| `nombre_competicion` | `VARCHAR`    | Nombre de la competición.          |

#### Tabla: `equipos`
Almacena la información de cada equipo.

| Columna         | Tipo de Dato | Descripción                        |
| --------------- | ------------ | ---------------------------------- |
| `equipo_id`     | `INT`        | ID único del equipo.               |
| `nombre_equipo` | `VARCHAR`    | Nombre del equipo.                 |
| `codigo_pais`   | `VARCHAR`    | Código de país del equipo (ej. "gb-eng"). |
| `nombre_pais`   | `VARCHAR`    | Nombre del país del equipo.        |

#### Tabla: `jugadores`
Almacena la información de cada jugador.

| Columna          | Tipo de Dato | Descripción                        |
| ---------------- | ------------ | ---------------------------------- |
| `jugador_id`     | `INT`        | ID único del jugador.              |
| `nombre_jugador` | `VARCHAR`    | Nombre del jugador.                |

#### Tabla: `partidos`
Contiene la información general de cada partido.

| Columna                        | Tipo de Dato | Descripción                               |
| ------------------------------ | ------------ | ----------------------------------------- |
| `partido_id`                   | `INT`        | ID único del partido.                     |
| `competicion_id`               | `INT`        | FK a `competiciones.competicion_id`.      |
| `fecha_inicio`                 | `DATETIME`   | Fecha y hora de inicio del partido.       |
| `equipo_local_id`              | `INT`        | FK a `equipos.equipo_id`.                 |
| `equipo_visitante_id`          | `INT`        | FK a `equipos.equipo_id`.                 |
| `goles_local`                  | `INT`        | Goles anotados por el equipo local.       |
| `goles_visitante`              | `INT`        | Goles anotados por el equipo visitante.   |
| ...                            | ...          | Otros campos de resumen del partido.      |

#### Tabla: `incidentes`
El registro detallado de cada evento dentro de un partido.

| Columna                   | Tipo de Dato | Descripción                                       |
| ------------------------- | ------------ | ------------------------------------------------- |
| `incidente_id`            | `INT`        | ID único del incidente (auto-incremental).        |
| `partido_id`              | `INT`        | FK a `partidos.partido_id`.                       |
| `minuto`                  | `INT`        | Minuto en que ocurrió el incidente.               |
| `tipo`                    | `INT`        | Tipo de evento (ej. 1 para Gol).                  |
| `subtipo`                 | `INT`        | Subtipo de evento (ej. 1 para Gol normal, 2 para Penalti). |
| `jugador_id`              | `INT`        | FK a `jugadores.jugador_id` del jugador principal. |
| `jugador_participante_id` | `INT`        | FK a `jugadores.jugador_id` del segundo jugador (ej. asistente). |
