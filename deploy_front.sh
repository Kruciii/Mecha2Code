#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
FRONT_DIR="${PROJECT_DIR}/front"
WEB_ROOT="${WEB_ROOT:-/www}"

required_files=("index.html" "styles.css" "app.js")

for file in "${required_files[@]}"; do
    if [[ ! -f "${FRONT_DIR}/${file}" ]]; then
        echo "Brak pliku frontu: ${FRONT_DIR}/${file}" >&2
        exit 1
    fi
done

echo "Wdrażanie frontendu z ${FRONT_DIR} do ${WEB_ROOT}..."

sudo install -d -m 0755 "${WEB_ROOT}"
for file in "${required_files[@]}"; do
    sudo install -m 0644 "${FRONT_DIR}/${file}" "${WEB_ROOT}/${file}"
done

echo "Frontend został wdrożony w ${WEB_ROOT}."
printf 'Pliki:\n'
for file in "${required_files[@]}"; do
    printf '  %s\n' "${WEB_ROOT}/${file}"
done
