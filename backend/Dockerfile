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
# 🔥 AGREGA ESTO
RUN mkdir -p /app/data && chmod -R 777 /app
# Exponer el puerto
EXPOSE 5000

# Comando para iniciar
CMD ["python", "app.py"]
