FROM node:22.23.1-alpine3.24 AS build
WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=/api
ARG GATEWAY_MAX_BODY_MB=90
RUN printf 'VITE_API_BASE_URL=%s\n' "$VITE_API_BASE_URL" > .env \
    && npm run check:locales \
    && npm run build

FROM nginx:1.29.4-alpine3.23 AS runtime
ARG GATEWAY_MAX_BODY_MB=90
COPY --from=build /app/dist /usr/share/nginx/html
RUN find /usr/share/nginx/html -type d -exec chmod 0755 {} + \
    && find /usr/share/nginx/html -type f -exec chmod 0644 {} +
COPY infrastructure/nginx/default.conf /etc/nginx/conf.d/default.conf
RUN case "$GATEWAY_MAX_BODY_MB" in \
      ''|*[!0-9]*) GATEWAY_MAX_BODY_MB=90 ;; \
    esac \
    && sed -i "s/__RBF_GATEWAY_MAX_BODY_MB__/${GATEWAY_MAX_BODY_MB}/g" /etc/nginx/conf.d/default.conf
COPY infrastructure/nginx/security-headers.conf /etc/nginx/snippets/rbf-security-headers.conf
COPY infrastructure/nginx/upload-security-headers.conf /etc/nginx/snippets/rbf-upload-security-headers.conf
RUN apk upgrade --no-cache \
    && addgroup -S rbf && adduser -S -G rbf -u 10001 rbf \
    && mkdir -p /var/cache/nginx /var/run /var/log/nginx /var/www/certbot \
    && chown -R rbf:rbf /var/cache/nginx /var/run /var/log/nginx /var/www/certbot /etc/nginx/conf.d
RUN sed -i 's|error_log /var/log/nginx/error.log notice;|error_log /dev/stderr notice;|' /etc/nginx/nginx.conf
USER 101
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
EXPOSE 8080 8443
