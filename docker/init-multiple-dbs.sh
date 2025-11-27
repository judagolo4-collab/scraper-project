#!/bin/bash

# Script para crear múltiples bases de datos en PostgreSQL
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Base de datos para proyectos de ley
    CREATE DATABASE proyectos_ley;
    GRANT ALL PRIVILEGES ON DATABASE proyectos_ley TO $POSTGRES_USER;

    -- Base de datos para metadata del scraper
    CREATE DATABASE scraper_metadata;
    GRANT ALL PRIVILEGES ON DATABASE scraper_metadata TO $POSTGRES_USER;
EOSQL

echo "✅ Bases de datos adicionales creadas: proyectos_ley, scraper_metadata"
