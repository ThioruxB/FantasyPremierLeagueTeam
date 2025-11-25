\copy competiciones FROM 'competiciones.csv' WITH (FORMAT CSV, HEADER TRUE);
\copy equipos FROM 'equipos.csv' WITH (FORMAT CSV, HEADER TRUE);
\copy jugadores FROM 'jugadores.csv' WITH (FORMAT CSV, HEADER TRUE);
\copy partidos FROM 'partidos.csv' WITH (FORMAT CSV, HEADER TRUE);
\copy incidentes FROM 'incidentes.csv' WITH (FORMAT CSV, HEADER TRUE, NULL '');