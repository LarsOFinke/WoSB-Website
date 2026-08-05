FROM eclipse-temurin:21-jre-alpine
RUN apk upgrade --no-cache \
    && addgroup -S rbf && adduser -S -G rbf -u 10001 rbf \
    && mkdir -p /app /var/lib/rbf/uploads /var/lib/rbf/control \
    && chown -R rbf:rbf /app /var/lib/rbf
WORKDIR /app
COPY --chown=rbf:rbf artifacts/rbf-api.jar /app/rbf-api.jar
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-XX:+ExitOnOutOfMemoryError", "-jar", "/app/rbf-api.jar"]
