-- Script para la corrección y carga final de datos.

-- Paso 1: Vaciar las tablas de jugadores e incidentes.
-- TRUNCATE es rápido y CASCADE se asegura de que la tabla incidentes (que depende de jugadores) también se vacíe.
TRUNCATE TABLE jugadores, incidentes RESTART IDENTITY CASCADE;

-- Paso 2: Cargar la lista de jugadores completa y consolidada.
\copy jugadores FROM 'C:\Users\ASUS\Music\ConectPremier\jugadores.csv' DELIMITER ',' CSV HEADER;

-- Paso 3: Cargar TODOS los incidentes de nuevo.
-- (Los partidos de enero y febrero ya están en la base de datos, así que no los tocamos).
\copy incidentes FROM 'C:\Users\ASUS\Music\ConectPremier\incidentes.csv' DELIMITER ',' CSV HEADER;
\copy incidentes FROM 'C:\Users\ASUS\Music\ConectPremier\nuevos_incidentes.csv' DELIMITER ',' CSV HEADER;


