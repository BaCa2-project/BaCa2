FROM postgres:16.2

COPY initdb.sql /docker-entrypoint-initdb.d/
