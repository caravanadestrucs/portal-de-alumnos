#!/bin/sh
# Entrypoint script para el backend

# Crear directorio instance si no existe
mkdir -p /app/instance
chmod 777 /app/instance

# Crear archivo DB si no existe
if [ ! -f /app/instance/portal.db ]; then
    touch /app/instance/portal.db
    chmod 666 /app/instance/portal.db
fi

# Ejecutar gunicorn
exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app
