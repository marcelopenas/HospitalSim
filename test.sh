#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ "$#" -ne 0 ]; then
  echo "Usage: bash test.sh" >&2
  exit 2
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Engine/Desktop and Compose v2." >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required (docker compose)." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Cannot reach Docker. Start the Docker daemon and check your access." >&2
  exit 1
fi

# A unique project isolates concurrent runs and the application's database.
project_name="hospitalsim-test-$(date +%s)-$$"
compose=(docker compose --project-name "$project_name" --file compose.test.yml)

cleanup() {
  local result=$?
  trap - EXIT
  if ! "${compose[@]}" down --volumes --remove-orphans; then
    echo "Could not clean up test project $project_name. Run: docker compose --project-name $project_name --file compose.test.yml down --volumes --remove-orphans" >&2
    if [ "$result" -eq 0 ]; then result=1; fi
  fi
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "Running all backend tests with a disposable MySQL database ($project_name)."
"${compose[@]}" up --build --abort-on-container-exit --exit-code-from tests
