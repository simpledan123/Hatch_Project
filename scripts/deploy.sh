#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

cd "$PROJECT_ROOT"

echo "[1/4] Start or rebuild containers"
sudo docker compose -f "$COMPOSE_FILE" up -d --build

echo "[2/4] Wait for service readiness"
for attempt in {1..20}; do
  if "$SCRIPT_DIR/healthcheck.sh" "$BASE_URL" >/dev/null 2>&1; then
    echo "[OK] Health check passed on attempt $attempt"
    break
  fi

  if [[ "$attempt" == "20" ]]; then
    echo "[ERROR] Service did not become ready in time"
    sudo docker compose -f "$COMPOSE_FILE" logs backend --tail 100
    exit 1
  fi

  sleep 3
done

echo "[3/4] Run smoke test"
"$SCRIPT_DIR/smoke_test.sh" "$BASE_URL"

echo "[4/4] Deployment flow completed successfully"