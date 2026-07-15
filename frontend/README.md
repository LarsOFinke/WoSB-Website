# RBF Frontend

Vue-3-/Vite-Anwendung mit fachlichen Modulen und sieben Sprachen.

```bash
cp .env.example .env
npm ci
npm run dev
npm test
npm run build
```

API-Regeln werden serverseitig durchgesetzt; das Frontend liefert Interaktion und frühes Feedback.
Siehe `../docs/ARCHITECTURE.md` und `../docs/DEVELOPMENT.md`.

## Struktur

Route-Seiten bleiben bewusst dünn: Zustandsbehaftete Use-Cases liegen in `composables/`, reine Regeln und Payload-Mappings in `domain/`, HTTP-Transport in `api/`. Details und Erweiterungsregeln stehen in [`ARCHITECTURE.md`](ARCHITECTURE.md); die vorgenommenen Schnitte sind in [`REFACTORING.md`](REFACTORING.md) dokumentiert.
