-- Script para el reseteo completo y la carga de datos consolidados.

-- Paso 1: Vaciar TODAS las tablas para asegurar un estado limpio.
-- RESTART IDENTITY reinicia los contadores de IDs (ej. para incidentes).
-- CASCADE se encarga de las dependencias entre tablas.
TRUNCATE TABLE competiciones, equipos, jugadores, partidos, incidentes RESTART IDENTITY CASCADE;

-- Paso 2: Cargar los archivos CSV maestros con los datos de Enero y Febrero.
\copy competiciones FROM 'C:\Users\ASUS\Music\ConectPremier\competiciones.csv' DELIMITER ',' CSV HEADER;
\copy equipos FROM 'C:\Users\ASUS\Music\ConectPremier\equipos.csv' DELIMITER ',' CSV HEADER;
\copy jugadores FROM 'C:\Users\ASUS\Music\ConectPremier\jugadores.csv' DELIMITER ',' CSV HEADER;
\copy partidos FROM 'C:\Users\ASUS\Music\ConectPremier\partidos.csv' DELIMITER ',' CSV HEADER;
\copy incidentes FROM 'C:\Users\ASUS\Music\ConectPremier\incidentes.csv' DELIMITER ',' CSV HEADER;
