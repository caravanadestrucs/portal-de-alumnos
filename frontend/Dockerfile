# TODO Sprint 3: multi-stage build with nginx for prod
FROM node:18-alpine

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Build-time env for Vite (baked into JS)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
ARG VITE_ALUMNO_INVITE_TOKEN
ENV VITE_ALUMNO_INVITE_TOKEN=$VITE_ALUMNO_INVITE_TOKEN
ARG VITE_PROFESOR_INVITE_TOKEN
ENV VITE_PROFESOR_INVITE_TOKEN=$VITE_PROFESOR_INVITE_TOKEN

# Copiar el resto del código
COPY . .

# Dar permisos de ejecución a vite
RUN chmod +x node_modules/.bin/vite || true

# Exponer el puerto de desarrollo
EXPOSE 3000

# Comando para desarrollo
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
