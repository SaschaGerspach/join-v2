# E2E Tests (Playwright)

## Prerequisites

- Backend running locally on `http://localhost:8000`
- Recommended: a fresh test database per run (delete the SQLite file)

## Starting the backend

```bash
cd backend
rm -f db.sqlite3
DJANGO_SECRET_KEY=dev-secret DJANGO_DEBUG=true python manage.py migrate
DJANGO_SECRET_KEY=dev-secret DJANGO_DEBUG=true python manage.py runserver 0.0.0.0:8000
```

`DJANGO_DEBUG=true` automatically raises the API throttle rates (see `DEFAULT_THROTTLE_RATES` in `backend/config/settings.py`), so the tests' login requests are not rate-limited. Never set it in production.

## Running the tests

```bash
cd frontend
npx playwright test
```

`ng serve` is started automatically (`reuseExistingServer: true`).

## Test user

`global-setup.ts` registers `e2e@example.com` (password `E2ePass123!`) once.
If the user already exists, it just logs in. The login storage state is written to `e2e/.auth/user.json` and shared by all specs.

## Debugging

```bash
npx playwright test --headed            # visible browser
npx playwright test --debug             # inspector
npx playwright show-report              # report after a run
```
