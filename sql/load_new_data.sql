-- Script para cargar nuevos datos a la base de datos.
-- Ejecutar en orden para mantener la integridad de las claves foráneas.

\copy partidos FROM 'C:\Users\ASUS\Music\ConectPremier\nuevos_partidos.csv' DELIMITER ',' CSV HEADER;
\copy incidentes FROM 'C:\Users\ASUS\Music\ConectPremier\nuevos_incidentes.csv' DELIMITER ',' CSV HEADER;
