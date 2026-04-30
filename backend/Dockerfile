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

# Copiar entrypoint y dar permisos
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Crear carpeta de datos
RUN mkdir -p /app/data

# Exponer el puerto
EXPOSE 5000

# Usar entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
