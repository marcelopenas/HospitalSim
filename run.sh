#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env with local development defaults. Review it before deploying."
fi

uv export --format requirements-txt --no-dev --no-emit-project --output-file requirements.txt

docker compose down -v
docker compose up --build "$@"
