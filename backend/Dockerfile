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

# Comando directo (sin script externo para evitar problemas de permisos)
ENTRYPOINT ["sh", "-c", "mkdir -p /app/instance && chmod 777 /app/instance && gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app"]
