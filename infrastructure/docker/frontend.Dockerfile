FROM node:22-alpine AS build
WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=/api
ARG VITE_MONITORING_HTTPS_PORT=8443
RUN printf 'VITE_API_BASE_URL=%s\nVITE_MONITORING_HTTPS_PORT=%s\n' "$VITE_API_BASE_URL" "$VITE_MONITORING_HTTPS_PORT" > .env \
    && npm run check:locales \
    && npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY infrastructure/nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80 443
