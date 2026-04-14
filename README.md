# Join — Kanban Project Management

A fullstack Kanban board application built with **Angular 17** and **Django REST Framework**. Features real-time collaboration via WebSockets, drag-and-drop task management, and a responsive PWA-ready interface.

<!-- TODO: Add screenshots here -->
<!-- ![Board View](docs/screenshots/board.png) -->

## Features

**Boards & Tasks**
- Drag-and-drop columns and tasks with Angular CDK
- Task priority, due dates, assignees, subtasks, and descriptions
- Color-coded labels (Many-to-Many) for task categorization
- File attachments with upload/download (max 5 MB)
- Task comments with edit/delete (own comments only)
- Bulk select, move, and delete tasks
- Inline rename for boards and columns (double-click)

**Collaboration**
- Real-time board updates via WebSockets (Django Channels + Redis)
- Board sharing — invite members by email
- Role-based access: owner (full control) vs. member (read/write)

**Views & Filters**
- Monthly calendar view for tasks with due dates
- Search, filter by priority, assignee, and due date
- Board statistics with Chart.js (tasks per column, priority distribution)
- Overdue and due-soon highlighting

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
- Docker Compose: Nginx, Django (Daphne/ASGI), PostgreSQL, Redis
- Automated daily PostgreSQL backups
- HTTPS via Certbot/Let's Encrypt
- GitHub Actions CI (backend tests + frontend build)
- Lazy-loaded routes (initial bundle ~300 kB)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 17, TypeScript, SCSS, Angular CDK, Chart.js, ng2-charts |
| Backend | Django 6, Django REST Framework, Django Channels, Daphne |
| Database | PostgreSQL 16 |
| Cache/WS | Redis 7 |
| Proxy | Nginx with rate limiting and SSL termination |
| CI/CD | GitHub Actions |
| Testing | Jasmine/Karma (frontend), Django TestCase (backend), Playwright (E2E) |

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
          └──────┬───────┘  └──────┬────────┘
                 │                 │
          ┌──────▼───────┐  ┌─────▼─────┐
          │ PostgreSQL   │  │   Redis    │
          │   16         │  │  (Channel  │
          │              │  │   Layer)   │
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
| GET/POST | `/boards/:id/members/` | Board members |
| GET/POST | `/boards/:id/labels/` | Board labels |
| GET/POST | `/columns/?board=:id` | List / create columns |
| GET/POST | `/tasks/?board=:id` | List / create tasks |
| PATCH/DELETE | `/tasks/:id/` | Update / delete task |
| POST | `/tasks/reorder/` | Bulk reorder tasks |
| GET/POST | `/tasks/:id/subtasks/` | Subtasks |
| GET/POST | `/tasks/:id/comments/` | Comments |
| GET/POST | `/tasks/:id/attachments/` | File attachments |
| GET | `/contacts/` | Contacts |
| WS | `/ws/board/:id/` | Real-time board events |

## Deployment

Frontend and backend are deployed separately:

- **Frontend** (Angular build) is served as static files on the frontend host (e.g. all-inkl).
- **Backend** (Django + Postgres + Redis + Nginx reverse proxy) runs via Docker Compose on its own server (e.g. Hostinger).

The Angular app calls the backend by the absolute URL in `frontend/src/environments/environment.prod.ts`.

### Backend — first-time setup (obtains SSL certificate)

On the backend server, after a DNS A-record points the backend domain to the server and `.env` is filled in:

```bash
./init.sh
```

This creates a temporary self-signed cert so Nginx can start, requests a real Let's Encrypt certificate for `DOMAIN`, reloads Nginx, runs migrations, and collects static files.

### Backend — subsequent deploys

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
