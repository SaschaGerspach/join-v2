# Join — Kanban Project Management

A fullstack Kanban board application built with **Angular 17** and **Django REST Framework**. Features real-time collaboration via WebSockets, drag-and-drop task management, a Gantt timeline, workload heatmaps, board time-travel, automation rules, and a responsive PWA-ready interface.

## Features

**Boards & Tasks**
- Drag-and-drop columns and tasks with Angular CDK
- Task priority, start/due dates, assignees (multi-select), subtasks, and descriptions
- Color-coded labels (Many-to-Many) for task categorization
- Priority color strips on task cards (border-left by priority)
- Cover images on task cards (URL-based)
- File attachments with upload/download (max 5 MB, MIME validation)
- Task comments with edit/delete, @-mention autocomplete, and emoji reactions
- Markdown rendering in descriptions and comments with edit/preview toggle
- Bulk select, move, and delete tasks
- Inline rename for boards and columns (double-click)
- Task dependencies — "blocked by" relationships with transitive circular detection
- Recurring tasks (daily/weekly/biweekly/monthly) — auto-creates next instance on archive
- Custom fields per board (text, number, date, select) with per-task values
- Time tracking — log minutes per task with notes and total sum
- WIP limits per column (visual warning when exceeded)
- Task watchers — watch/unwatch with watcher count
- Task deep-links (`/boards/:id/tasks/:taskId`) and copy-link button
- Task archive with restore functionality
- Task templates — reusable presets with subtasks, priority, labels; create task from template

**Boards**
- Board templates (Kanban, Scrum, Bug Tracking) with pre-configured columns
- Favorite boards with drag-and-drop reorder on summary page
- Board invite links — token-based sharing via clipboard
- CSV export and import
- PDF export (landscape Kanban layout via WeasyPrint)
- Swimlane grouping within columns (by priority or assignee)
- Saved filters (persist filter combinations per board)
- Board activity log tracking tasks, columns, and comments

**Views & Analytics**
- Global search across boards, tasks, and contacts
- Monthly calendar view for tasks with due dates
- **Gantt Chart** — timeline view with zoom levels (day/week/month), dependency arrows (SVG), today-line, unscheduled section, and task info panel
- **Workload Heatmap** — cross-board GitHub-style contribution graph showing assignee workload per day with color intensity, range selector (1/3/6 months), and hover detail panel
- **Board Time-Travel** — animated timeline slider to replay board evolution over time, play/pause controls, mini Kanban snapshot at any past date, activity feed around selected time
- **Time Tracking Reports** — per-user, per-task, and daily trend charts with board-level time report endpoint
- Board statistics with Chart.js (tasks per column, priority distribution, creation trend, activity timeline, assignee workload)
- Search, filter by priority, assignee, and due date
- Overdue and due-soon highlighting

**Automations**
- Rule-based automation engine: when X happens (with optional conditions), do Y
- Triggers: task created, task moved to column, priority set, label added, all subtasks done, deadline approaching
- Conditions: priority equals, label set, assignee equals
- Actions: move to column, set priority, assign user, add/remove label, notify creator / assignees / a specific user
- Execution log of applied rules
- Per-board automation management UI

**Webhooks**
- Outgoing webhooks with configurable event subscriptions
- HMAC-signed payloads for verification
- Auto-format payloads as Slack Block Kit or Teams MessageCard based on target URL
- Delivery history with response status tracking
- Celery-based async delivery with retry logic

**AI Assist** (optional, admin-toggled)
- Generate a task description from a title and keywords
- Suggest sensible subtasks for a task
- Summarize a board or its open tasks
- Auto-categorize: suggest priority and labels from the task text
- Per-feature on/off toggles in the admin dashboard
- Pluggable providers (Anthropic, OpenAI); features stay disabled until a provider key is configured

**Teams & Collaboration**
- Create and manage teams with member invitations
- Team roles: admin and member
- Assign teams to boards for shared access
- Real-time board updates via WebSockets (Django Channels + Redis)
- Real-time notification push via dedicated WebSocket (`/ws/notifications/`)
- Board sharing — invite members by email or via invite link
- Granular per-board/per-team roles: owner, admin, editor, viewer
- Account deletion with automatic board ownership transfer

**Notifications & Scheduling**
- In-app notification center with types: assignment, comment, mention
- Real-time push via WebSocket
- Notification preferences (in-app, email per event, daily digest)
- Daily digest emails (Celery Beat)
- Automated due-date reminders (Celery Beat, configurable window)

**Admin Dashboard**
- Overview stats with weekly trends (users, boards, tasks)
- Warning cards for unverified, inactive, and never-logged-in users
- Audit log with filterable event types
- Board activity overview

**User Experience**
- Dark mode with toggle and `prefers-color-scheme` detection
- PWA — installable with service worker, offline support via IndexedDB queue, update banner
- Keyboard shortcuts (`?` to show overview)
- Board accent color picker
- Loading spinners and error states
- Toast notifications with i18n (DE/EN)

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
- Tiered admin access: a platform admin (`is_staff`) reaches the admin dashboard only — never private boards or teams; a separate superuser holds the cross-board/-team override, and every such access is recorded in the audit log
- Security headers: HSTS, X-Frame-Options DENY, Referrer-Policy
- Private media storage for attachments (not publicly accessible)

**Infrastructure**
- Docker Compose: Traefik, Django (Daphne/ASGI), PostgreSQL, Redis, Celery Worker, Celery Beat, Backup
- Resource limits per container (memory + CPU caps)
- Automated daily PostgreSQL backups with 30-day retention
- HTTPS via Traefik + Let's Encrypt (automatic certificate renewal)
- GitHub Actions CI: ruff lint, pip-audit, npm audit, backend tests, frontend production build
- Health check endpoint (`/health/`) for container orchestration
- OpenAPI schema + Swagger UI + ReDoc (dev mode)
- Lazy-loaded routes
- Gzip compression for all text assets

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
| Testing | Django TestCase (532 tests), Angular Karma (51 unit tests), Playwright (26 E2E specs) |

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

# Required environment variables
export DJANGO_SECRET_KEY="your-secret-key"
export DJANGO_DEBUG="true"

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
| POST | `/boards/:id/favorites/reorder/` | Reorder favorites |
| GET/POST/DELETE | `/boards/:id/invite-link/` | Manage invite link |
| POST | `/boards/join/:token/` | Join board via invite link |
| GET | `/boards/:id/export/csv/` | CSV export |
| GET | `/boards/:id/export/pdf/` | PDF export (landscape Kanban layout) |
| POST | `/boards/:id/import/csv/` | CSV import |
| GET | `/boards/:id/time-report/` | Time tracking report (per user/task/day) |
| GET/POST | `/boards/:id/members/` | Board members |
| PATCH/DELETE | `/boards/:id/members/:userId/` | Change role / remove member |
| DELETE | `/boards/:id/members/leave/` | Leave board |
| GET/POST | `/boards/:id/labels/` | Board labels |
| GET/POST | `/boards/:id/fields/` | Custom fields |
| PATCH/DELETE | `/boards/:id/fields/:id/` | Custom field detail |
| GET/POST | `/boards/:id/automations/` | Automation rules |
| PATCH/DELETE | `/boards/:id/automations/:id/` | Automation detail |
| GET/POST | `/columns/?board=:id` | List / create columns |
| POST | `/columns/reorder/` | Batch reorder columns |
| GET/POST | `/tasks/?board=:id` | List / create tasks |
| GET | `/tasks/my/` | All my tasks across boards |
| GET | `/tasks/workload/` | Cross-board workload data |
| GET | `/tasks/archive/?board=:id` | Archived tasks |
| PATCH/DELETE | `/tasks/:id/` | Update / archive task |
| POST | `/tasks/:id/duplicate/` | Duplicate task |
| POST | `/tasks/:id/restore/` | Restore archived task |
| GET/POST/DELETE | `/tasks/:id/watch/` | Watch / unwatch task |
| GET | `/tasks/:id/history/` | Task change history |
| POST | `/tasks/reorder/` | Bulk reorder tasks |
| GET/POST | `/tasks/:id/subtasks/` | Subtasks |
| POST | `/tasks/:id/subtasks/reorder/` | Reorder subtasks |
| GET/POST | `/tasks/:id/comments/` | Comments |
| PATCH/DELETE | `/tasks/:id/comments/:id/` | Edit / delete comment |
| POST | `/tasks/:id/comments/:id/reactions/` | Toggle emoji reaction |
| GET/POST | `/tasks/:id/attachments/` | File attachments |
| GET/POST | `/tasks/:id/dependencies/` | Task dependencies |
| DELETE | `/tasks/:id/dependencies/:id/` | Remove dependency |
| GET/PUT | `/tasks/:id/fields/` | Task custom field values |
| GET/POST | `/tasks/:id/time/` | Time entries |
| DELETE | `/tasks/:id/time/:id/` | Delete time entry |
| GET/POST | `/tasks/templates/?board=:id` | Task templates |
| PATCH/DELETE | `/tasks/templates/:id/` | Template detail |
| POST | `/tasks/templates/:id/create-task/` | Create task from template |
| GET/POST | `/webhooks/?board=:id` | Webhooks |
| PATCH/DELETE | `/webhooks/:id/` | Webhook detail |
| GET | `/webhooks/:id/deliveries/` | Delivery history |
| GET | `/webhooks/events/` | Available event types |
| GET | `/ai/features/` | Enabled AI features for the current user |
| POST | `/ai/generate-description/` | Generate a task description |
| POST | `/ai/suggest-subtasks/` | Suggest subtasks |
| POST | `/ai/summarize/` | Summarize a board / open tasks |
| POST | `/ai/categorize/` | Suggest priority and labels |
| GET | `/ai/admin/features/` | List AI features with status (admin) |
| PATCH | `/ai/admin/features/:key/` | Enable / disable an AI feature (admin) |
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
