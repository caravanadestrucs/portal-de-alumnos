FROM node:18-alpine

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Dar permisos de ejecución a vite
RUN chmod +x node_modules/.bin/vite || true

# Exponer el puerto de desarrollo
EXPOSE 3000

# Comando para desarrollo
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
