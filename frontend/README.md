# RBF Frontend

Vue 3/Vite application with domain modules and seven languages.

```bash
cp .env.example .env
npm ci
npx playwright install chromium
npm run dev
npm test
npm run build
```

API rules are enforced server-side; the frontend provides interaction and early feedback.
See [System Architecture](../docs/architecture/ARCHITECTURE.md),
[Development](../docs/development/DEVELOPMENT.md), and
[Tests](../docs/development/TESTING.md).

## Structure

Route pages intentionally remain thin: stateful use cases live in `composables/`,
pure rules and payload mappings in `domain/`, and HTTP transport in `api/`.
Details, module boundaries, and extension rules are documented in
[`ARCHITECTURE.md`](ARCHITECTURE.md).
