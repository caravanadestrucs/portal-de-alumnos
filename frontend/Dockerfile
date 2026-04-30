FROM node:18-bullseye/

WORKDIR /app/

# ARG for Vite (needs to be available at build time)
ARG VITE_API_URL=http://localhost:5000/api/

# Copy dependency files FIRST (to leverage cache)
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps/

# Install vite GLOBALLY (avoids permission issues)
RUN npm install -g vite/

# Copy the rest of the code
COPY . ./

# Build for production using the GLOBAL vite path
RUN /usr/local/bin/vite build/

# Install serve to serve static files
RUN npm install -g serve/

# Expose the port
EXPOSE 3000/

# Serve with serve
CMD ["serve", "-l", "3000", "-s", "dist"]
