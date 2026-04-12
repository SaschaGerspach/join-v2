#!/usr/bin/env bash
set -euo pipefail

echo "==> Pulling latest changes…"
git pull --ff-only

echo "==> Building and restarting containers…"
docker compose build
docker compose up -d

echo "==> Running database migrations…"
docker compose exec backend python manage.py migrate --noinput

echo "==> Collecting static files…"
docker compose exec backend python manage.py collectstatic --noinput

echo "==> Deploy complete!"
docker compose ps
