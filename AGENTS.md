# join-v2 — Project Rules

## Stack & Structure

- Backend: Django + DRF, 13 apps under `backend/`.
- Frontend: Angular, split into `frontend/src/app/{features,core,shared}`.
- WebSockets via Django Channels/Redis, auth via JWT (simplejwt).

## Validation (run after every change)

Mirrors the CI pipeline (.github/workflows/ci.yml) exactly, so green locally = green in CI.

- Backend changed (from `backend/`):
  - Tests: `coverage run manage.py test` and `coverage report --fail-under=80`
  - Lint: `ruff check .`
  - Quick run without coverage: `python manage.py test`
- Frontend changed (from `frontend/`):
  - Tests: `npm test -- --watch=false --browsers=ChromeHeadlessCI`
  - Build: `npm run build -- --configuration=production`
- For frontend-only changes, do not test the backend, and vice versa.
- The frontend has no lint script — do not search for one or invent one.

## Important Environment Notes

- In CI, backend tests run against PostgreSQL 16 (POSTGRES\_\* env vars set).
  A test can pass locally with SQLite and still fail in CI on PostgreSQL
  specifics — when in doubt, the CI run is authoritative.
- `coverage report --fail-under=80` means: tests can pass functionally and
  the step can still fail if coverage drops below 80 %. If the coverage
  step fails, add the missing tests instead of lowering the threshold.

## Commits

- Conventional Commits with scope: `type(scope): description`
  (e.g. `fix(board): ...`, `test(tasks): ...`).

## Architecture Decisions

- Deliberate decisions are documented as comments at the affected code
  (e.g. the DOMPurify safeguard in `shared/pipes/markdown.pipe.ts`),
  not in this file. Read the comment before changing such places.
