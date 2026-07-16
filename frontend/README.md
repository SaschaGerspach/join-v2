# Join Frontend

Angular 17 single-page application for the Join Kanban board. Talks to the Django REST backend and receives real-time updates over WebSockets. See the [main README](../README.md) for the full feature list, architecture and Docker setup.

## Prerequisites

- Node.js (see `Dockerfile` for the version used in production builds)
- A running backend on `http://localhost:8000` (see the main README)

## Development server

```bash
npm install
npm start
```

Serves the app at `http://localhost:4200` with hot reload. The backend URL for local development is configured in `src/environments/environment.ts` (`http://localhost:8000`).

## Build

```bash
npm run build -- --configuration=production
```

Output goes to `dist/`.

## Tests

**Unit tests** (Karma/Jasmine):

```bash
npm test                                        # watch mode
npm test -- --watch=false --browsers=ChromeHeadlessCI   # single run, as in CI
```

**E2E tests** (Playwright — requires a running backend, see [e2e/README.md](e2e/README.md)):

```bash
npm run e2e        # headless
npm run e2e:ui     # Playwright UI mode
```
