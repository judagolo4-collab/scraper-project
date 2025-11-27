#!/bin/bash
set -e

echo "🔧 Inicializando base de datos..."

# Crear tabla proyectos_ley en la BD airflow
echo "📊 Creando tablas de proyectos en airflow..."

if [ -f /docker-entrypoint-initdb.d/02-init-tables.sql ]; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "airflow" -f /docker-entrypoint-initdb.d/02-init-tables.sql
    echo "✅ Tablas de proyectos creadas"
else
    echo "⚠️ Archivo init_tables.sql no encontrado"
fi

echo "🎉 Inicialización completada"
