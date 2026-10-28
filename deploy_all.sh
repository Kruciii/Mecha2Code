#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_DIR="$(cd -- "${PROJECT_DIR}/.." && pwd)"
if [[ -z "${COMPOSE_FILE:-}" ]]; then
    if [[ -f "${REPOSITORY_DIR}/docker-compose.yml" ]]; then
        COMPOSE_FILE="${REPOSITORY_DIR}/docker-compose.yml"
    elif [[ -f "${PROJECT_DIR}/docker-compose.yml" ]]; then
        COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
    else
        COMPOSE_FILE="${REPOSITORY_DIR}/docker-compose.yml"
    fi
fi

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

MIGRATION_FILE="${PROJECT_DIR}/DB/migrations/20261028_add_user_academic_fields.sql"
if [[ -f "${MIGRATION_FILE}" ]]; then
    DB_SERVICE=""
    if docker compose -f "${COMPOSE_FILE}" config --services | grep -qx "mechacode-db"; then
        DB_SERVICE="mechacode-db"
    elif docker compose -f "${COMPOSE_FILE}" config --services | grep -qx "db"; then
        DB_SERVICE="db"
    fi

    if [[ -n "${DB_SERVICE}" ]]; then
        echo "Uruchamianie migracji users (semester/start_year/major)..."
        docker compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
            sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "${MIGRATION_FILE}"
    else
        echo "Pominięto migrację: nie znaleziono usługi DB (mechacode-db/db)." >&2
    fi
else
    echo "Pominięto migrację: brak pliku ${MIGRATION_FILE}." >&2
fi

echo "Wdrażanie frontendu..."
"${PROJECT_DIR}/deploy_front.sh"

echo
echo "Wdrożenie zakończone. Status usług:"
docker compose -f "${COMPOSE_FILE}" ps
