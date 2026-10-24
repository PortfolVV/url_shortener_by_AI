FROM node:22-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install --no-audit --no-fund

COPY . .
RUN npm run build

# The Compose `frontend_build` service copies /app/dist into a shared volume
# that the Nginx load balancer serves as static files.
CMD ["sh", "-c", "echo 'frontend build complete'"]
