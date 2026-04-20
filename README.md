# Join — Kanban Project Management

A fullstack Kanban board application built with **Angular 17** and **Django REST Framework**. Features real-time collaboration via WebSockets, drag-and-drop task management, and a responsive PWA-ready interface.

<!-- TODO: Add screenshots here -->
<!-- ![Board View](docs/screenshots/board.png) -->

## Features

**Boards & Tasks**
- Drag-and-drop columns and tasks with Angular CDK
- Task priority, due dates, assignees (multi-select), subtasks, and descriptions
- Color-coded labels (Many-to-Many) for task categorization
- File attachments with upload/download (max 5 MB)
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
- CSV export (all active tasks with columns, priority, assignees, labels, due date)
- Swimlane grouping within columns (by priority or assignee)
- Board activity log (created, moved, deleted, updated events)

**Collaboration**
- Real-time board updates via WebSockets (Django Channels + Redis)
- Board sharing — invite members by email
- Granular roles: owner (full control), admin (manage members), editor (modify tasks), viewer (read-only)
- Role management UI with dropdown per member

**Views & Filters**
- Monthly calendar view for tasks with due dates
- Search, filter by priority, assignee, and due date
- Board statistics with Chart.js (tasks per column, priority distribution)
- Overdue and due-soon highlighting

**Notifications & Automation**
- In-app notification center (assignments, mentions, due dates)
- Automated due-date reminders (Celery Beat, 24h before deadline)

**User Experience**
- Dark mode with toggle and `prefers-color-scheme` detection
- Keyboard shortcuts (`?` to show overview)
- Board accent color picker
- Loading spinners and error states
- Toast notifications
- PWA — installable with service worker

**Authentication & Security**
- Session-based auth with CSRF protection
- Email verification on registration
- Password reset via email
- Nginx rate limiting (API: 10r/s, Auth: 3r/s)
- Django Admin at `/manage/` (IP-restricted via Nginx)

**Infrastructure**
- Docker Compose: Nginx, Django (Daphne/ASGI), PostgreSQL, Redis, Celery Worker, Celery Beat
- Automated daily PostgreSQL backups
- HTTPS via Certbot/Let's Encrypt
- GitHub Actions CI (backend tests + frontend build)
- Lazy-loaded routes (initial bundle ~300 kB)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 17, TypeScript, SCSS, Angular CDK, Chart.js, ng2-charts |
| Backend | Django 6, Django REST Framework, Django Channels, Daphne |
| Task Queue | Celery 5.4 with Redis broker, Celery Beat for scheduling |
| Database | PostgreSQL 16 |
| Cache/WS | Redis 7 |
| Proxy | Nginx with rate limiting and SSL termination |
| CI/CD | GitHub Actions |
| Testing | Django TestCase (205+ tests), Playwright (E2E) |

## Architecture

```
                    ┌──────────────┐
                    │   Browser    │
                    └──────┬───────┘
                           │ HTTPS
                    ┌──────▼───────┐
                    │    Nginx     │
                    │  (SSL, Rate  │
                    │   Limiting)  │
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
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Log in |
| POST | `/auth/logout` | Log out |
| GET | `/auth/me` | Current user |
| GET/POST | `/boards/` | List / create boards |
| GET/PATCH/DELETE | `/boards/:id/` | Board detail |
| POST/DELETE | `/boards/:id/favorite/` | Favorite / unfavorite |
| GET | `/boards/:id/export/csv/` | CSV export |
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
| GET | `/contacts/` | Contacts |
| GET | `/notifications/` | User notifications |
| WS | `/ws/board/:id/` | Real-time board events |

## Deployment

Frontend and backend are deployed separately:

- **Frontend** (Angular build) is served as static files on the frontend host (e.g. all-inkl).
- **Backend** (Django + Postgres + Redis + Nginx reverse proxy) runs via Docker Compose on its own server (e.g. Hostinger).

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
