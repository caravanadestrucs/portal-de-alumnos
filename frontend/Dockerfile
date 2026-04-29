FROM node:18-alpine

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar resto del frontend
COPY . .

# Exponer el puerto
EXPOSE 3000

# Iniciar en modo desarrollo con Vite
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
