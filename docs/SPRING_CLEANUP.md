# Spring Cleanup Pass

This pass followed the larger backend module refactor and focused on removing transitional clutter while keeping the application behavior unchanged.

## Backend cleanup

- Moved FastAPI app creation from `app/__init__.py` into `app/core/app_factory.py`.
- Kept `app/__init__.py` as a tiny package-level export only.
- Moved route implementations out of `routes/__init__.py` into `routes/router.py`.
- Removed global compatibility aggregate packages:
  - `app/models`
  - `app/schemas`
  - `app/services`
- Removed empty placeholder subpackages from `modules/content`.
- Removed old schema aggregator modules such as `schemas/auth.py`, `schemas/build.py`, `schemas/fleet.py` and similar re-export-only files.
- Centralized duplicated schema constants into module-level `schemas/constants.py` files.
- Kept each concrete backend class in exactly one file.

## Storage cleanup

- Root-level `storage/` remains removed.
- The repository contains only `backend/storage/uploads/demo` for demo upload assets.
- Runtime upload storage remains configured only through `UPLOAD_DIR`.

## Validation

Run the standard checks after structural changes:

```bash
cd frontend
npm run check:locales
npm run build
npm audit --omit=dev
find src -name '*.js' -print0 | xargs -0 -n1 node --check

cd ..
python -m compileall -q backend/src
```

For backend smoke tests, use a valid temporary `backend/.env` and reset a local demo DB before calling API routes.
