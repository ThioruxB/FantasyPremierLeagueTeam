DROP TABLE IF EXISTS incidentes CASCADE;
DROP TABLE IF EXISTS partidos CASCADE;
DROP TABLE IF EXISTS jugadores CASCADE;
DROP TABLE IF EXISTS equipos CASCADE;
DROP TABLE IF EXISTS competiciones CASCADE;

-- Tablas permisivas sin claves foráneas (FOREIGN KEY)

CREATE TABLE competiciones (
    competicion_id INTEGER PRIMARY KEY,
    nombre_competicion VARCHAR(255) NOT NULL
);

CREATE TABLE equipos (
    equipo_id INTEGER PRIMARY KEY,
    nombre_equipo VARCHAR(255) NOT NULL,
    codigo_pais VARCHAR(10),
    nombre_pais VARCHAR(100)
);

CREATE TABLE jugadores (
    jugador_id INTEGER PRIMARY KEY,
    nombre_jugador VARCHAR(255) NOT NULL
);

CREATE TABLE partidos (
    partido_id INTEGER PRIMARY KEY,
    competicion_id INTEGER,
    fecha_inicio TIMESTAMPTZ,
    estado VARCHAR(50),
    equipo_local_id INTEGER,
    equipo_visitante_id INTEGER,
    goles_local INTEGER DEFAULT 0,
    goles_visitante INTEGER DEFAULT 0,
    tarjetas_amarillas_local INTEGER DEFAULT 0,
    tarjetas_rojas_local INTEGER DEFAULT 0,
    tarjetas_amarillas_visitante INTEGER DEFAULT 0,
    tarjetas_rojas_visitante INTEGER DEFAULT 0,
    tiempo_transcurrido INTEGER
);

CREATE TABLE incidentes (
    incidente_id INTEGER PRIMARY KEY,
    partido_id INTEGER,
    minuto INTEGER,
    periodo INTEGER,
    tipo VARCHAR(100),
    subtipo VARCHAR(100),
    jugador_id INTEGER,
    jugador_participante_id INTEGER,
    campo VARCHAR(100)
);
