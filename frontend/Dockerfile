# Frontend: build Vite -> statyczne pliki serwowane przez Caddy (HTTPS + proxy do API)
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM caddy:2-alpine

# Konfiguracja Caddy jest montowana z katalogu deploy/ (docker-compose.yml),
# dzięki czemu zmiana domeny nie wymaga przebudowy obrazu.
COPY --from=build /app/dist /srv
