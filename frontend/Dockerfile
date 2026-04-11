# frontend/Dockerfile
# Imagen para desarrollo con hot-reload (Vite HMR)
# En producción usar multi-stage build con nginx

FROM node:20-alpine

WORKDIR /app

# Instalar dependencias primero (aprovecha caché de Docker)
COPY package*.json ./
RUN npm install

# Copiar código fuente
COPY . .

EXPOSE 5173

# Vite necesita --host para ser accesible desde fuera del contenedor
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
