FROM node:18-alpine as builder

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Exponer el puerto
EXPOSE 3000

# Build de producción
RUN npm run build

# Servir con un servidor estático ligero (serve)
RUN npm install -g serve

# Comando para producción
CMD ["serve", "-l", "3000", "-s", "dist"]
