# Infrastructure origin

The integrated deployment layer adopts the modular organization and operational goals of
Lars O. Finke's `PI-Server-Infrastructure` repository:

- https://github.com/LarsOFinke/PI-Server-Infrastructure

It is intentionally adapted rather than used as a Git submodule. This keeps application,
migrations and infrastructure in one atomic release while preserving recognizable divisions
for host setup, services, backups, checks and reusable shell helpers.
