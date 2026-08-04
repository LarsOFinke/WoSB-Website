# RBF Frontend

Vue-3-/Vite-Anwendung mit fachlichen Modulen und sieben Sprachen.

```bash
cp .env.example .env
npm ci
npx playwright install chromium
npm run dev
npm test
npm run build
```

API-Regeln werden serverseitig durchgesetzt; das Frontend liefert Interaktion und frühes Feedback.
Siehe [Systemarchitektur](../docs/architecture/ARCHITECTURE.md),
[Entwicklung](../docs/development/DEVELOPMENT.md) und
[Tests](../docs/development/TESTING.md).

## Struktur

Route-Seiten bleiben bewusst dünn: Zustandsbehaftete Use-Cases liegen in
`composables/`, reine Regeln und Payload-Mappings in `domain/`, HTTP-Transport in
`api/`. Details, Modulgrenzen und Erweiterungsregeln stehen in
[`ARCHITECTURE.md`](ARCHITECTURE.md).
