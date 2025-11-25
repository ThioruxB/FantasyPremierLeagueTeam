
-- Tabla: competiciones
CREATE TABLE IF NOT EXISTS competiciones (
    competicion_id INT PRIMARY KEY,
    nombre_competicion VARCHAR(255) NOT NULL
);

-- Tabla: equipos
CREATE TABLE IF NOT EXISTS equipos (
    equipo_id INT PRIMARY KEY,
    nombre_equipo VARCHAR(255) NOT NULL
);

-- Tabla: jugadores
CREATE TABLE IF NOT EXISTS jugadores (
    jugador_id INT PRIMARY KEY,
    nombre_jugador VARCHAR(255) NOT NULL
);

-- Tabla: partidos
CREATE TABLE IF NOT EXISTS partidos (
    partido_id INT PRIMARY KEY,
    competicion_id INT NOT NULL REFERENCES competiciones(competicion_id),
    fecha_inicio TIMESTAMP NOT NULL,
    estado INT NOT NULL,
    equipo_local_id INT NOT NULL REFERENCES equipos(equipo_id),
    equipo_visitante_id INT NOT NULL REFERENCES equipos(equipo_id),
    goles_local INT NOT NULL,
    goles_visitante INT NOT NULL,
    tiempo_transcurrido VARCHAR(50) NOT NULL
);

-- Tabla: incidentes
CREATE TABLE IF NOT EXISTS incidentes (
    incidente_id INT PRIMARY KEY,
    partido_id INT NOT NULL REFERENCES partidos(partido_id),
    minuto INT NOT NULL,
    tipo VARCHAR(255) NOT NULL,
    subtipo VARCHAR(255),
    jugador_id INT REFERENCES jugadores(jugador_id),
    jugador_participante_id INT REFERENCES jugadores(jugador_id),
    periodo VARCHAR(50)
);

