# Docker and Container Security Standard

Status: August 2, 2026

Containers are an additional isolation layer, not a security boundary equivalent to a
separate VM. Docker Engine, containerd, and runc share the host kernel; runtime, kernel,
images, and container configuration must therefore be hardened together.

## Current risk landscape

For the production Linux server, these upstream fixes are particularly relevant:

- Docker Engine 29.5.1 fixed several ways to influence host-root code or files via
  `docker cp` with CVE-2026-41567, CVE-2026-41568, and CVE-2026-42306. Until the
  update is installed, do not use `docker cp` with untrusted or compromised containers.
- Docker Engine 29.5.0 limited memory exhaustion through crafted image archives with
  CVE-2026-32288. Unknown images and `docker load` from third-party sources remain prohibited.
- Current runc releases contain follow-up fixes for the container escapes
  CVE-2025-31133, CVE-2025-52565, and CVE-2025-52881 as well as CVE-2026-41579.
- containerd published, among other issues, a critical image-unpack vulnerability
  (GHSA-cm76-qm8v-3j95) and a UID-check bypass in 2026. The security-maintained packages
  of the deployed Linux distribution are authoritative, not a bare comparison of upstream
  version numbers, because distributions backport fixes.
- Docker Desktop CVEs do not affect the production server: the project uses Docker Engine
  on Linux there, not Docker Desktop or Model Runner.

Primary sources: [Docker security announcements](https://docs.docker.com/security/security-announcements/),
[Docker Engine 29 release notes](https://docs.docker.com/engine/release-notes/29/),
[runc releases](https://github.com/opencontainers/runc/releases), and
[containerd advisories](https://github.com/containerd/containerd/security/advisories).

## Mandatory protection layers

### Host and runtime

1. Obtain the kernel, `docker.io`/Docker CE, containerd, and runc from a supported
   distribution and install security updates daily. After runtime or kernel updates,
   restart the host or daemon in a controlled manner; merely updating the package version
   does not replace the still-running vulnerable process.
2. Run `sudo apt update && sudo apt full-upgrade` and `sudo make -C infrastructure doctor`
   before approval. Check the distribution security tracker when an upstream CVE is marked
   fixed despite an apparently older package version.
3. Never expose the Docker API unencrypted over TCP. The socket is not mounted into any
   container; membership in the `docker` group is treated as root access.
4. Keep default seccomp and AppArmor (or SELinux) enabled. Never introduce
   `seccomp=unconfined`, `apparmor=unconfined`, `privileged: true`, or host PID/network
   namespaces as a convenience workaround.
5. Rootless Docker reduces the risk of daemon/runtime exploits and should be evaluated for
   new installations. Because ports, systemd, backup file permissions, and cgroup limits are
   affected, migration is planned work rather than a silent setup upgrade. Until then, the
   existing separation protects the host: no Docker-group membership, minimal host surface,
   and administrative root calls only.

### Images and build

1. Build only the Dockerfiles defined in the repository and trusted official images. Do not
   use third-party Dockerfiles, BuildKit frontends, `docker load` archives, or uncontrolled
   Compose overrides on the production host.
2. Base images are pinned to concrete version lines. Updates are reviewed changes with build,
   Trivy scan, and smoke test; `latest` is prohibited.
3. The security workflow rebuilds core images on push, manual runs, and weekly. Trivy blocks
   known `HIGH` and `CRITICAL` vulnerabilities with an available fix. OSV remains a complementary
   check for Python and Node lockfiles.
4. Build secrets do not belong in `ARG`, image layers, or build context. The frontend receives
   only explicitly public `VITE_*` values.

### Running containers

- API, migration, and seed run non-root, read-only, without Linux capabilities, and with
  `no-new-privileges`.
- Write access is limited to named data directories and `tmpfs`.
- The database and internal services are not publicly published; local diagnostic ports bind
  to `127.0.0.1`.
- PID limits, separate networks, log rotation, and health checks limit failure impact.
- New services must inherit these properties or document the minimum exception, including the
  threat, required capability, and removal plan.

## Response to a new runtime vulnerability

1. Record the affected component and running version:

   ```bash
   sudo docker version
   sudo docker info
   runc --version
   containerd --version
   dpkg-query -W docker.io docker-ce containerd containerd.io runc 2>/dev/null
   ```

2. Check exposure: are third-party images built/loaded, is `docker cp` used, is the Docker API
   exposed, are there privileged containers, socket mounts, or untrusted admin accounts?
3. Check package sources and the distribution advisory, install the security update, and restart
   the daemon/host. Then recreate containers from newly built images; merely pulling an image does
   not update running containers.
4. Disable the affected path until remediation. If escape is possible, treat the host as compromised:
   isolate it, rotate credentials and backup keys, preserve logs, and rebuild from a trusted state.
5. Run `make validate`, the security workflow, and restore/readiness checks, and document the
   decision and advisory in the security audit.

## Approval check

```bash
sudo make -C infrastructure doctor
sudo docker compose --env-file infrastructure/.env \
  -f infrastructure/compose.yml config
sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

A green image scan does not prove that runtime and kernel are secure. Conversely, an older package
version patched by Debian/Ubuntu is not automatically vulnerable; the distribution advisory is decisive.

### Runtime exposure and upload boundary

The release stack publishes only the HTTP/HTTPS gateway. PostgreSQL has no host port in `compose.release.yml`; the backend bridge is internal, while only the API receives the dedicated outbound network. API and gateway run non-root, read-only, with `no-new-privileges` and all Linux capabilities dropped. Operational debugging uses bounded service logs/diagnostics rather than routine `docker exec -it` sessions.

`POST /api/files` has three independent limits: nginx request/rate limiting, Spring multipart size limits, and the file service's per-type/per-user/global/free-space quotas. The backend validates extension + declared MIME + file signature and normalizes display filenames; frontend validation is only early feedback and is never the trust boundary.
