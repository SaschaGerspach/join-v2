#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "ERROR: .env missing. Copy .env.example to .env and fill it in." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${DOMAIN:?DOMAIN must be set in .env}"
: "${DJANGO_SECRET_KEY:?DJANGO_SECRET_KEY must be set in .env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set in .env}"

EMAIL="${CERTBOT_EMAIL:-}"
if [[ -z "$EMAIL" ]]; then
  echo "ERROR: CERTBOT_EMAIL must be set in .env (used for Let's Encrypt registration)" >&2
  exit 1
fi

CERT_PATH="/etc/letsencrypt/live/${DOMAIN}"

echo "==> Creating dummy certificate so nginx can start…"
docker compose run --rm --entrypoint "\
  sh -c 'mkdir -p ${CERT_PATH} && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout ${CERT_PATH}/privkey.pem \
    -out ${CERT_PATH}/fullchain.pem \
    -subj \"/CN=${DOMAIN}\"'" certbot

echo "==> Starting all services with dummy cert…"
docker compose up -d --build

echo "==> Waiting for nginx to be ready…"
sleep 5

echo "==> Deleting dummy certificate…"
docker compose run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/${DOMAIN} \
         /etc/letsencrypt/archive/${DOMAIN} \
         /etc/letsencrypt/renewal/${DOMAIN}.conf" certbot

echo "==> Requesting real certificate from Let's Encrypt…"
docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email ${EMAIL} \
    --agree-tos --no-eff-email \
    -d ${DOMAIN} -d www.${DOMAIN}" certbot

echo "==> Reloading nginx with real certificate…"
docker compose exec frontend nginx -s reload

echo "==> Running migrations and collectstatic…"
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py collectstatic --noinput

echo ""
echo "==> Initial setup complete."
echo "==> Next: docker compose exec backend python manage.py createsuperuser"
docker compose ps
