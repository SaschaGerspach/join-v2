# E2E Tests (Playwright)

## Voraussetzungen

- Backend läuft lokal auf `http://localhost:8000`
- Empfehlung: leere Test-DB pro Run (SQLite-Datei löschen)

## Backend starten

```bash
cd backend
rm -f db.sqlite3
DJANGO_SECRET_KEY=dev-secret DJANGO_DEBUG=true python manage.py migrate
DJANGO_SECRET_KEY=dev-secret DJANGO_DEBUG=true DJANGO_DISABLE_THROTTLE=true python manage.py runserver 0.0.0.0:8000
```

`DJANGO_DISABLE_THROTTLE=true` setzt die Auth-Throttle-Rate hoch, damit die Login-Requests der Tests nicht gedrosselt werden. In Production niemals setzen.

## Tests ausführen

```bash
cd frontend
npx playwright test
```

Der `ng serve` wird automatisch gestartet (`reuseExistingServer: true`).

## Test-User

`global-setup.ts` registriert einmalig `e2e@example.com` (Passwort `E2ePass123!`).
Falls User schon existiert, wird nur eingeloggt. Der Login-Storage-State landet unter `e2e/.auth/user.json` und wird von allen Specs geteilt.

## Debugging

```bash
npx playwright test --headed            # sichtbarer Browser
npx playwright test --debug             # Inspector
npx playwright show-report              # Reports nach Lauf
```
