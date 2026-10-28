#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_DIR="$(cd -- "${PROJECT_DIR}/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-${REPOSITORY_DIR}/docker-compose.yml}"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo "Brak pliku Compose: ${COMPOSE_FILE}" >&2
    exit 1
fi

if git -C "${PROJECT_DIR}" rev-parse --show-toplevel >/dev/null 2>&1; then
    GIT_DIR="${PROJECT_DIR}"
elif git -C "${REPOSITORY_DIR}" rev-parse --show-toplevel >/dev/null 2>&1; then
    GIT_DIR="${REPOSITORY_DIR}"
else
    echo "Nie znaleziono repozytorium Git w ${PROJECT_DIR} ani ${REPOSITORY_DIR}." >&2
    echo "Uruchom skrypt po sklonowaniu projektu, np. do ~/mechacode/Mecha2Code." >&2
    exit 1
fi

echo "Pobieranie najnowszego kodu..."
git -C "${GIT_DIR}" pull --ff-only

echo "Budowanie aktualnego obrazu API bez cache..."
docker compose -f "${COMPOSE_FILE}" build --no-cache api

echo "Uruchamianie i odtwarzanie wszystkich usług..."
docker compose -f "${COMPOSE_FILE}" up -d --force-recreate

echo "Wdrażanie frontendu..."
"${PROJECT_DIR}/deploy_front.sh"

echo
echo "Wdrożenie zakończone. Status usług:"
docker compose -f "${COMPOSE_FILE}" ps
