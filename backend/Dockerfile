FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del backend
COPY . .

# Crear carpeta de datos y dar permisos
RUN mkdir -p /app/instance && chmod 777 /app/instance

# Exponer el puerto
EXPOSE 5000

# Seed/migrate: si volumen vacio o con schema viejo (sin admins.role), restaura DB del image
ENTRYPOINT ["sh", "-c", "mkdir -p /app/instance && chmod 777 /app/instance && if [ ! -s /app/instance/portal.db ] && [ -f /app/backend_seed.db ]; then cp /app/backend_seed.db /app/instance/portal.db && echo '[DB] Seeded portal.db from image (empty volume)'; else if [ -f /app/instance/portal.db ] && [ -f /app/backend_seed.db ] && ! sqlite3 /app/instance/portal.db 'SELECT role FROM admins LIMIT 1' >/dev/null 2>&1; then echo '[DB] Old schema detected (no admins.role) — backing up and restoring seed'; cp /app/instance/portal.db /app/instance/portal.db.bak.old_schema.$(date +%Y%m%d%H%M%S) 2>/dev/null || true; cp /app/backend_seed.db /app/instance/portal.db && echo '[DB] Restored portal.db from image (migrated)'; fi; fi && gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app"]
