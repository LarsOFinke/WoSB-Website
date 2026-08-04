package eu.royalblackwater.api.config;

import eu.royalblackwater.api.security.CsrfCookieFilter;
import eu.royalblackwater.api.security.RequestBoundaryFilter;
import eu.royalblackwater.api.security.SessionAuthenticationFilter;
import java.util.List;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;
import org.springframework.security.web.csrf.XorCsrfTokenRequestAttributeHandler;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
@EnableMethodSecurity
@EnableConfigurationProperties({SessionProperties.class, SecurityProperties.class, StorageProperties.class,
        OperationsProperties.class, SecretEncryptionProperties.class, LegalNoticeProperties.class,
        BootstrapAdminProperties.class})
public class SecurityConfiguration {
    private static final Logger LOG = LoggerFactory.getLogger(SecurityConfiguration.class);
    private static final String[] PUBLIC_ENDPOINTS = {
            "/api/health", "/api/health/ready", "/actuator/health/**",
            "/api/auth/login", "/api/auth/logout", "/api/auth/me", "/api/auth/register",
            "/api/legal-notice", "/api/privacy/cookie-consent", "/api/privacy/cookie-policy",
            "/api/privacy/contact", "/api/fleets/public/official", "/api/files/*/content"
    };

    @Bean
    SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            RequestBoundaryFilter boundary,
            SessionAuthenticationFilter sessionAuthentication,
            CsrfCookieFilter csrfCookieFilter,
            CorsConfigurationSource corsConfigurationSource,
            SessionProperties sessionProperties) throws Exception {
        return http
                .csrf(csrf -> {
                    CookieCsrfTokenRepository repository = CookieCsrfTokenRepository.withHttpOnlyFalse();
                    repository.setCookiePath("/");
                    repository.setCookieCustomizer(cookie -> cookie.secure(sessionProperties.secure()).sameSite(sessionProperties.sameSite()));
                    XorCsrfTokenRequestAttributeHandler handler = new XorCsrfTokenRequestAttributeHandler();
                    handler.setCsrfRequestAttributeName("_csrf");
                    csrf.csrfTokenRepository(repository).csrfTokenRequestHandler(handler);
                })
                .cors(cors -> cors.configurationSource(corsConfigurationSource))
                .httpBasic(basic -> basic.disable())
                .formLogin(form -> form.disable())
                .logout(logout -> logout.disable())
                .requestCache(cache -> cache.disable())
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .headers(Customizer.withDefaults())
                .addFilterBefore(boundary, UsernamePasswordAuthenticationFilter.class)
                .addFilterAfter(sessionAuthentication, RequestBoundaryFilter.class)
                .addFilterAfter(csrfCookieFilter, SessionAuthenticationFilter.class)
                .authorizeHttpRequests(auth -> auth
                        // Keep method/path matching explicit: this avoids a
                        // servlet-path matcher treating generated public
                        // routes as protected after the Spring Boot 4 move.
                        .requestMatchers(HttpMethod.GET,
                                "/api/health", "/api/health/ready", "/actuator/health/**",
                                "/api/auth/me", "/api/legal-notice", "/api/privacy/cookie-consent",
                                "/api/privacy/cookie-policy", "/api/fleets/public/official",
                                "/api/files/*/content").permitAll()
                        .requestMatchers(HttpMethod.POST,
                                "/api/auth/login", "/api/auth/logout", "/api/auth/register",
                                "/api/privacy/cookie-consent", "/api/privacy/contact").permitAll()
                        .requestMatchers(PUBLIC_ENDPOINTS).permitAll()
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                        .requestMatchers("/api/admin/**").hasAuthority("ROLE_ADMIN")
                        .requestMatchers("/api/**").authenticated()
                        .anyRequest().denyAll())
                .exceptionHandling(errors -> errors
                        .authenticationEntryPoint((request, response, exception) -> {
                            LOG.warn("security_401 method={} path={} originPresent={} sessionCookiePresent={} csrfHeaderPresent={} cause={}",
                                    request.getMethod(), request.getRequestURI(),
                                    hasHeader(request, "Origin"), hasCookie(request, "rbf_hub_session"),
                                    hasHeader(request, "X-XSRF-TOKEN"), exception.getClass().getSimpleName());
                            response.sendError(401);
                        })
                        .accessDeniedHandler((request, response, exception) -> {
                            LOG.warn("security_403 method={} path={} originPresent={} sessionCookiePresent={} csrfHeaderPresent={} cause={}",
                                    request.getMethod(), request.getRequestURI(),
                                    hasHeader(request, "Origin"), hasCookie(request, "rbf_hub_session"),
                                    hasHeader(request, "X-XSRF-TOKEN"), exception.getClass().getSimpleName());
                            response.sendError(403);
                        }))
                .build();
    }

    private static boolean hasHeader(jakarta.servlet.http.HttpServletRequest request, String name) {
        String value = request.getHeader(name);
        return value != null && !value.isBlank();
    }

    private static boolean hasCookie(jakarta.servlet.http.HttpServletRequest request, String name) {
        if (request.getCookies() == null) return false;
        for (jakarta.servlet.http.Cookie cookie : request.getCookies()) {
            if (name.equals(cookie.getName())) return true;
        }
        return false;
    }

    @Bean
    CorsConfigurationSource corsConfigurationSource(SecurityProperties securityProperties) {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(securityProperties.normalizeOrigins());
        configuration.setAllowedMethods(List.of("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("Content-Type", "Accept", "X-Requested-With", "X-XSRF-TOKEN"));
        configuration.setExposedHeaders(List.of("Location", "Retry-After"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
