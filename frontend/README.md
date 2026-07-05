# Frontend - WoSB Community Hub

Vue 3 + Vite frontend for the minimal Community Hub prototype.

## Start

```bash
npm install
npm run dev
```

Routes:

```text
/home
/builds
/builds/:id
/builds/new
/register
/login
/profile
/profile/builds
/groups
/groups/:id
/groups/new
/profile/groups
/admin
```

Protected routes use the backend session cookie. `/admin` is available to admins and moderators; only admins see moderator creation. Start the backend and seed the database before logging in.

Seeded admin:

```text
admin / admin123
```
