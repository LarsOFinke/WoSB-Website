# Production Checklist

## Already improved in this pass

- Central app settings.
- Central logging configuration.
- Request logging middleware with request IDs.
- Split frontend app shell components.
- Central sidebar navigation model.
- DB check constraints for important enum/range fields on fresh schemas.
- Updated documentation and architecture inventory.

## Required before live users

- [ ] Add Alembic migrations and migration review process.
- [ ] Use PostgreSQL in staging/production.
- [ ] Add CI pipeline for backend tests, frontend build, locale checks, audits and linting.
- [ ] Add backend tests for auth, fleet membership, uploads, guide embeds and staff permissions.
- [ ] Add rate limiting for login/register/upload endpoints.
- [ ] Move uploads to object storage or durable shared storage.
- [ ] Add backup/restore procedure.
- [ ] Configure production CORS origins explicitly.
- [ ] Set `SESSION_COOKIE_SECURE=true` behind HTTPS.
- [ ] Replace demo admin password before deployment.
- [ ] Add monitoring for error rates, request latency and storage growth.

## Nice-to-have hardening

- [ ] Full audit trail for staff actions.
- [ ] Soft-delete model for user-generated content.
- [ ] Rich-text editor that serializes to the current embed token model.
- [ ] Pagination on large lists.
- [ ] Background cleanup task for orphaned uploads and expired sessions.
