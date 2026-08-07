# Spring AOP / Repository Proxy Fix — 2026-08-07

A real `mvn verify` with Spring Boot 4.1, Spring Framework 7 and PostgreSQL Testcontainers exposed a runtime-only problem that static compilation could not detect.

## Root cause

Module JDBC repositories annotated with `@Repository` were declared `final`. Spring's persistence exception translation creates CGLIB class proxies for these beans. CGLIB cannot subclass a final class, so application-context startup failed first at `SecurityOperationsRepository` and would have failed subsequently at the other final repository beans.

`JdbcRepositorySupport` also exposed its shared JDBC operations as `public final` methods. Those methods could not be advised on a class proxy and generated proxy warnings.

## Fix

- all concrete classes annotated with `@Repository` are now non-final;
- proxy-visible methods inherited from `JdbcRepositorySupport` are non-final;
- HTTP 422 usages use Spring 7's `UNPROCESSABLE_CONTENT` constant instead of deprecated `UNPROCESSABLE_ENTITY`;
- MapStruct compiler options are applied only to main compilation, so test compilation no longer warns that no processor recognized those options.

## Architectural rule

Spring-managed classes that may be advised through class-based proxies must remain proxyable. In particular, concrete `@Repository` classes and methods intended for Spring advice must not be `final` when `spring.aop.proxy-target-class=true` is in effect.

The authoritative regression check remains `mvn verify`, because proxyability is a runtime application-context concern rather than a Java type-system error.
