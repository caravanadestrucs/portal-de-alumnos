#!/bin/sh
# Entrypoint script para el backend

# Crear directorio de datos si no existe
mkdir -p /app/data
chmod 777 /app/data

# Ejecutar gunicorn
exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app
