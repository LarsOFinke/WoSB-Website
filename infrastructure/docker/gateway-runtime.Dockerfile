FROM nginx:1.29.4-alpine3.23
ARG GATEWAY_MAX_BODY_MB=90
RUN apk upgrade --no-cache \
    && addgroup -S rbf && adduser -S -G rbf -u 10001 rbf \
    && mkdir -p /var/cache/nginx /var/run /var/log/nginx /var/www/certbot \
    && chown -R rbf:rbf /var/cache/nginx /var/run /var/log/nginx /var/www/certbot /etc/nginx/conf.d
COPY infrastructure/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY infrastructure/nginx/security-headers.conf /etc/nginx/snippets/rbf-security-headers.conf
COPY infrastructure/nginx/upload-security-headers.conf /etc/nginx/snippets/rbf-upload-security-headers.conf
RUN sed -i "s/__RBF_GATEWAY_MAX_BODY_MB__/${GATEWAY_MAX_BODY_MB}/g" /etc/nginx/conf.d/default.conf
RUN sed -i 's|error_log /var/log/nginx/error.log notice;|error_log /dev/stderr notice;|' /etc/nginx/nginx.conf
COPY artifacts/frontend/ /usr/share/nginx/html/
USER 101
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
EXPOSE 8080 8443
