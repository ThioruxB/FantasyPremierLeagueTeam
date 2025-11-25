DROP TABLE IF EXISTS incidentes CASCADE;
DROP TABLE IF EXISTS partidos CASCADE;
DROP TABLE IF EXISTS jugadores CASCADE;
DROP TABLE IF EXISTS equipos CASCADE;
DROP TABLE IF EXISTS competiciones CASCADE;

-- Tabla para almacenar las competiciones (Ligas, Copas, etc.)
CREATE TABLE IF NOT EXISTS competiciones (
    competicion_id INTEGER PRIMARY KEY,
    nombre_competicion VARCHAR(255) NOT NULL
);

-- Tabla para almacenar los equipos
CREATE TABLE IF NOT EXISTS equipos (
    equipo_id INTEGER PRIMARY KEY,
    nombre_equipo VARCHAR(255) NOT NULL,
    codigo_pais VARCHAR(10),
    nombre_pais VARCHAR(100)
);

-- Tabla para almacenar todos los jugadores
CREATE TABLE IF NOT EXISTS jugadores (
    jugador_id INTEGER PRIMARY KEY,
    nombre_jugador VARCHAR(255) NOT NULL
);

-- Tabla central para almacenar la información de cada partido
CREATE TABLE IF NOT EXISTS partidos (
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
    tiempo_transcurrido INTEGER,
    CONSTRAINT fk_competicion FOREIGN KEY(competicion_id) REFERENCES competiciones(competicion_id) ON DELETE SET NULL,
    CONSTRAINT fk_equipo_local FOREIGN KEY(equipo_local_id) REFERENCES equipos(equipo_id) ON DELETE SET NULL,
    CONSTRAINT fk_equipo_visitante FOREIGN KEY(equipo_visitante_id) REFERENCES equipos(equipo_id) ON DELETE SET NULL
);

-- Tabla para registrar los incidentes de cada partido (goles, tarjetas, etc.)
CREATE TABLE IF NOT EXISTS incidentes (
    incidente_id INTEGER PRIMARY KEY,
    partido_id INTEGER,
    minuto INTEGER,
    periodo INTEGER,
    tipo VARCHAR(100),
    subtipo VARCHAR(100),
    jugador_id INTEGER,
    jugador_participante_id INTEGER,
    campo VARCHAR(100),
    CONSTRAINT fk_partido FOREIGN KEY(partido_id) REFERENCES partidos(partido_id) ON DELETE CASCADE,
    CONSTRAINT fk_jugador FOREIGN KEY(jugador_id) REFERENCES jugadores(jugador_id) ON DELETE SET NULL,
    CONSTRAINT fk_jugador_participante FOREIGN KEY(jugador_participante_id) REFERENCES jugadores(jugador_id) ON DELETE SET NULL
);

-- Creación de índices para mejorar el rendimiento de las búsquedas más comunes
CREATE INDEX IF NOT EXISTS idx_partidos_fecha ON partidos(fecha_inicio);
CREATE INDEX IF NOT EXISTS idx_incidentes_partido_id ON incidentes(partido_id);
