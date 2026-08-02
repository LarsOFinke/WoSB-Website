FROM maven:3.9.11-eclipse-temurin-21-alpine AS build
WORKDIR /workspace
COPY pom.xml ./
RUN mvn --batch-mode --no-transfer-progress dependency:go-offline
COPY src ./src
RUN mvn --batch-mode --no-transfer-progress clean package -DskipTests

FROM eclipse-temurin:21.0.8_9-jre-alpine
RUN addgroup -S rbf && adduser -S -G rbf -u 10001 rbf
WORKDIR /app
COPY --from=build --chown=rbf:rbf /workspace/target/rbf-secure-api-*.jar /app/application.jar
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-XX:+ExitOnOutOfMemoryError", "-jar", "/app/application.jar"]
