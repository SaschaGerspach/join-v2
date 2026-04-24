# Join — Kanban Project Management

A fullstack Kanban board application built with **Angular 17** and **Django REST Framework**. Features real-time collaboration via WebSockets, drag-and-drop task management, and a responsive PWA-ready interface.

## Features

**Boards & Tasks**
- Drag-and-drop columns and tasks with Angular CDK
- Task priority, due dates, assignees (multi-select), subtasks, and descriptions
- Color-coded labels (Many-to-Many) for task categorization
- File attachments with upload/download (max 5 MB, MIME validation)
- Task comments with edit/delete and @-mention autocomplete
- Markdown rendering in descriptions and comments (via marked + DOMPurify)
- Bulk select, move, and delete tasks
- Inline rename for boards and columns (double-click)
- Task dependencies — "blocked by" relationships with transitive circular detection
- Recurring tasks (daily/weekly/biweekly/monthly) — auto-creates next instance on archive
- Custom fields per board (text, number, date, select) with per-task values
- Time tracking — log minutes per task with notes and total sum
- WIP limits per column (visual warning when exceeded)
- Task archive with restore functionality

**Boards**
- Board templates (Kanban, Scrum, Bug Tracking) with pre-configured columns
- Favorite boards (star/unstar, favorites sorted first)
- CSV export and import
- Swimlane grouping within columns (by priority or assignee)
- Saved filters (persist filter combinations per board)
- Board activity log tracking tasks, columns, and comments (created, moved, updated, deleted)

**Teams**
- Create and manage teams with member invitations
- Team roles: admin and member
- Assign teams to boards for shared access

**Collaboration**
- Real-time board updates via WebSockets (Django Channels + Redis)
- Real-time notification push via dedicated WebSocket (`/ws/notifications/`)
- Board sharing — invite members by email (with notification email)
- Granular roles: owner (full control), admin (manage members), editor (modify tasks), viewer (read-only)
- Role management UI with dropdown per member
- Account deletion with automatic board ownership transfer to next admin/editor

**Views & Filters**
- Global search across boards, tasks, and contacts
- Monthly calendar view for tasks with due dates
- Search, filter by priority, assignee, and due date
- Board statistics with Chart.js (tasks per column, priority distribution)
- Overdue and due-soon highlighting

**Notifications & Automation**
- In-app notification center with types: assignment, comment, mention
- Real-time push via WebSocket (no page reload needed)
- Notification preferences (in-app, email per event, daily digest)
- Daily digest emails (Celery Beat, summary of unread notifications)
- Automated due-date reminders (Celery Beat, hourly check, 24h window configurable via `DUE_DATE_REMINDER_HOURS`)

**Admin Dashboard**
- Overview stats with weekly trends (users, boards, tasks)
- Warning cards for unverified, inactive, and never-logged-in users (expandable lists)
- Audit log with filterable event types and human-readable labels
- Board activity overview (active/inactive boards, top boards by task count)
- Django Admin at `/manage/` (env-gated via `DJANGO_ADMIN_ENABLED`)

**User Experience**
- Dark mode with toggle and `prefers-color-scheme` detection
- Keyboard shortcuts (`?` to show overview)
- Board accent color picker
- Loading spinners and error states
- Toast notifications with i18n (DE/EN)
- PWA — installable with service worker

**User Management**
- User profile editing (name, email, password)
- User avatars with upload, resize (256×256), and JPEG conversion
- Two-factor authentication (TOTP) with QR code setup
- Account deletion with board ownership transfer
- Contact management (shared address book for assignees)

**Authentication & Security**
- JWT auth with HttpOnly refresh cookie and CSRF protection
- Two-factor authentication (TOTP/2FA) with encrypted secrets
- Email verification on registration (with resend option)
- Password reset via email with token-based confirmation
- Audit logging (login, password reset, 2FA, member changes, account deletion)
- Security headers: HSTS, X-Frame-Options DENY, Referrer-Policy
- Private media storage for attachments (not publicly accessible)

**Infrastructure**
- Docker Compose: Traefik, Django (Daphne/ASGI), PostgreSQL, Redis, Celery Worker, Celery Beat, Backup
- Resource limits per container (memory + CPU caps)
- Automated daily PostgreSQL backups (pg_dump in dedicated container)
- HTTPS via Traefik + Let's Encrypt (automatic certificate renewal)
- GitHub Actions CI: ruff lint, pip-audit, npm audit, backend tests, frontend production build
- Health check endpoint (`/health/`) for container orchestration
- OpenAPI schema + Swagger UI + ReDoc (dev mode)
- Lazy-loaded routes (initial bundle ~410 kB)
- Gzip compression for all text assets (CSS, JS, JSON, SVG, fonts)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 17, TypeScript, SCSS, Angular CDK, Chart.js, ng2-charts |
| Backend | Django 6, Django REST Framework, Django Channels, Daphne |
| Task Queue | Celery 5.4 with Redis broker, Celery Beat for scheduling |
| Database | PostgreSQL 16 |
| Cache/WS | Redis 7 |
| Proxy | Traefik with automatic HTTPS via Let's Encrypt |
| CI/CD | GitHub Actions |
| Testing | Django TestCase (207 tests), Playwright (10 E2E specs) |

## Architecture

```
                    ┌──────────────┐
                    │   Browser    │
                    └──────┬───────┘
                           │ HTTPS
                    ┌──────▼───────┐
                    │   Traefik    │
                    │  (SSL, Auto  │
                    │   Certs)     │
                    └──┬───────┬───┘
              /api/    │       │   /ws/
          ┌────────────▼─┐  ┌─▼────────────┐
          │   Django     │  │   Daphne      │
          │   REST API   │  │  (WebSocket)  │
          └──┬───────┬───┘  └──────┬────────┘
             │       │             │
             │  ┌────▼──────────┐  │
             │  │ Celery Worker │  │
             │  │ + Beat        │  │
             │  └────┬──────────┘  │
             │       │             │
          ┌──▼───────▼───┐  ┌─────▼─────┐
          │ PostgreSQL   │  │   Redis    │
          │   16         │  │ (Broker +  │
          │              │  │  Channels) │
          └──────────────┘  └───────────┘
```

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Quick Start

```bash
# Clone the repository
git clone https://github.com/SaschaGerspach/join-v2.git
cd join-v2

# Copy and configure environment variables
cp .env.example .env

# Start all services
docker compose up -d

# The app is now running at http://localhost
```

### Local Development (with Docker)

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Frontend: `http://localhost:4200` (Angular dev server with hot reload)
- Backend: `http://localhost:8000` (Django runserver with auto reload)
- PostgreSQL: `localhost:5432`

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npx ng serve
```

The frontend runs on `http://localhost:4200`, the backend API on `http://localhost:8000`.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register/` | Create account |
| POST | `/auth/login/` | Log in |
| POST | `/auth/logout/` | Log out |
| POST | `/auth/token/refresh/` | Refresh access token |
| GET | `/auth/me/` | Current user |
| POST | `/auth/verify-email/` | Verify email token |
| POST | `/auth/resend-verification/` | Resend verification email |
| POST | `/auth/password-reset/` | Request password reset |
| POST | `/auth/password-reset/confirm/` | Confirm reset with token |
| POST/DELETE | `/auth/avatar/` | Upload / remove avatar |
| POST | `/auth/totp/setup/` | Setup 2FA |
| POST | `/auth/totp/confirm/` | Confirm 2FA setup |
| POST | `/auth/totp/disable/` | Disable 2FA |
| GET/PATCH/DELETE | `/users/:id/` | Profile / update / delete account |
| GET | `/users/export/` | Export personal data |
| GET/POST | `/boards/` | List / create boards |
| GET/PATCH/DELETE | `/boards/:id/` | Board detail |
| POST/DELETE | `/boards/:id/favorite/` | Favorite / unfavorite |
| GET | `/boards/:id/export/csv/` | CSV export |
| POST | `/boards/:id/import/csv/` | CSV import |
| GET/POST | `/boards/:id/members/` | Board members |
| PATCH/DELETE | `/boards/:id/members/:userId/` | Change role / remove member |
| DELETE | `/boards/:id/members/leave/` | Leave board |
| GET/POST | `/boards/:id/labels/` | Board labels |
| GET/POST | `/boards/:id/fields/` | Custom fields (CRUD) |
| PATCH/DELETE | `/boards/:id/fields/:id/` | Custom field detail |
| GET/POST | `/columns/?board=:id` | List / create columns |
| GET/POST | `/tasks/?board=:id` | List / create tasks |
| GET | `/tasks/my/` | All my tasks across boards |
| GET | `/tasks/archive/?board=:id` | Archived tasks |
| PATCH/DELETE | `/tasks/:id/` | Update / archive task |
| POST | `/tasks/:id/restore/` | Restore archived task |
| POST | `/tasks/reorder/` | Bulk reorder tasks |
| GET/POST | `/tasks/:id/subtasks/` | Subtasks |
| GET/POST | `/tasks/:id/comments/` | Comments |
| GET/POST | `/tasks/:id/attachments/` | File attachments |
| GET/POST | `/tasks/:id/dependencies/` | Task dependencies |
| DELETE | `/tasks/:id/dependencies/:id/` | Remove dependency |
| GET/PUT | `/tasks/:id/fields/` | Task custom field values |
| GET/POST | `/tasks/:id/time/` | Time entries |
| DELETE | `/tasks/:id/time/:id/` | Delete time entry |
| GET/POST | `/contacts/` | Contacts (CRUD) |
| GET/POST | `/teams/` | List / create teams |
| GET/PATCH/DELETE | `/teams/:id/` | Team detail |
| GET/POST | `/teams/:id/members/` | Team members |
| PATCH/DELETE | `/teams/:id/members/:userId/` | Member role / removal |
| GET | `/notifications/` | User notifications |
| POST/PATCH | `/notifications/preferences/` | Notification preferences |
| GET | `/activity/?board=:id` | Board activity log |
| GET | `/admin-api/stats/` | Admin stats with trends |
| GET | `/admin-api/audit-log/` | Audit log (filterable) |
| GET | `/admin-api/boards/` | Board activity overview |
| GET | `/health/` | Health check |
| WS | `/ws/board/:id/` | Real-time board events |
| WS | `/ws/notifications/` | Real-time notification push |

## Deployment

Frontend and backend are deployed separately:

- **Frontend** (Angular build) is served as static files on the frontend host (e.g. all-inkl).
- **Backend** (Django + Postgres + Redis + Traefik reverse proxy) runs via Docker Compose on its own server (e.g. Hostinger).

The Angular app calls the backend by the absolute URL in `frontend/src/environments/environment.prod.ts`.

### Backend deploy

The backend runs behind a shared Traefik reverse proxy on the host (network `root_default`). Traefik handles HTTPS via Let's Encrypt automatically through container labels.

After DNS A-record points `DOMAIN` to the server and `.env` is filled in:

```bash
./deploy.sh
```

### Frontend build for production

```bash
cd frontend
npx ng build --configuration=production
# Upload the contents of frontend/dist/<project>/ to the frontend host.
```

## License

This project is for educational and portfolio purposes.
