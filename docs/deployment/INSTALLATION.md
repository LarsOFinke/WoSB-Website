# Installation

Production requires a 64-bit Debian/Ubuntu-class host, Docker Engine with Compose v2, at least 2 GiB RAM, adequate backup storage, DNS and TCP 80/443.

## Prepare shared configuration

Create a private environment file from `infrastructure/.env.example`, replace every generated/example secret and configure hostname, database, session, encryption and backup settings. Store it root-readable only.

## First artifact install

The recommended origin path is `./deploy.sh`. On the target server,
`setup_website.sh` can alternatively be run directly, either interactively or with flags.
If Docker or Compose is missing, the assistant automatically uses the existing host
bootstrap from `infrastructure/scripts/lib/host/packages.sh`. `--skip-host` can be used
to disable this step deliberately. If no environment file is specified, the assistant
automatically creates `/srv/rbf/shared/.env` with new secrets and stores the one-time
credentials in `/srv/rbf/shared/first-run-credentials.txt`. On a new installation, the
activation run then verifies these credentials through the public `POST /api/auth/login`
route. A 401 causes first installation to fail closed instead of delivering an unusable
bootstrap identity. Seed credentials are intended exclusively for initial creation and
never reset the password of an already-existing bootstrap administrator.

For a genuinely empty target installation, `setup_website.sh` detects the first-install
case automatically and sets the required confirmation internally. As soon as active or
not-clearly-orphaned release data exists, backup protection remains active and the run
stops without a manual decision.

```bash
sudo ./setup_website.sh \
  --artifact rbf-deployment-1.0.0.tar.gz \
  --checksum rbf-deployment-1.0.0.tar.gz.sha256 \
  --install-root /srv/rbf \
  --env /secure/rbf.env \
  --no-backup
```

For a manual run without flags, use `sudo ./setup_website.sh`. The dialog asks for all
values and, for a first installation, requires explicit confirmation that no backup point exists.

`--no-backup` remains restricted to a genuinely new installation without an
existing database. Normal updates always create the coordinated backup before
the release switch.

The public first-run entry point is `./deploy.sh --configure`. The internal source-tree
setup under `infrastructure/setup.sh` is used only by local development and artifact
workflows and is not a stable production contract.

## Existing database adoption

Stop the old application, take independent database and file backups, then run the fingerprint and adoption scripts through the provided deployment helpers. The gate accepts only the reviewed final legacy schema; unknown or partial schemas fail closed.
