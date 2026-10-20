#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_DIR="$(cd -- "${PROJECT_DIR}/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-${REPOSITORY_DIR}/docker-compose.yml}"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo "Brak pliku Compose: ${COMPOSE_FILE}" >&2
    exit 1
fi

cd "${REPOSITORY_DIR}"

echo "Pobieranie najnowszego kodu..."
git pull --ff-only

echo "Budowanie aktualnego obrazu API bez cache..."
docker compose -f "${COMPOSE_FILE}" build --no-cache api

echo "Uruchamianie i odtwarzanie wszystkich usług..."
docker compose -f "${COMPOSE_FILE}" up -d --force-recreate

echo "Wdrażanie frontendu..."
"${PROJECT_DIR}/deploy_front.sh"

echo
echo "Wdrożenie zakończone. Status usług:"
docker compose -f "${COMPOSE_FILE}" ps
