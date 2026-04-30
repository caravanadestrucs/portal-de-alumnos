FROM node:18 as builder

WORKDIR /app

# ARG para Vite (necesita estar disponible en build time)
ARG VITE_API_URL=http://localhost:5000/api

# Copiar archivos de dependencias PRIMERO (para aprovechar cache)
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Build de producción (usar npx para evitar problemas de permisos)
RUN npx vite build

# --- Imagen final ligera ---
FROM node:18

WORKDIR /app

# Instalar serve para servir archivos estáticos
RUN npm install -g serve

# Copiar solo el build de la etapa anterior
COPY --from=builder /app/dist ./dist

# Exponer el puerto
EXPOSE 3000

# Servir con serve
CMD ["serve", "-l", "3000", "-s", "dist"]
