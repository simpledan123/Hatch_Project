#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.prod}"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.prod.yml}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] $ENV_FILE 파일이 없습니다."
  echo "        .env.prod.example 를 복사해서 .env.prod 를 먼저 만드세요."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

BASE_URL="${BASE_URL:-http://localhost:${BACKEND_PORT:-8000}}"
PUBLIC_URL="${PUBLIC_URL:-http://localhost:${NGINX_PORT:-80}}"

cd "$PROJECT_ROOT"

echo "[1/4] Build and start production containers"
sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

echo "[2/4] Wait for backend readiness"
for attempt in {1..20}; do
  if "$SCRIPT_DIR/healthcheck.sh" "$BASE_URL" >/dev/null 2>&1; then
    echo "[OK] Backend health check passed on attempt $attempt"
    break
  fi

  if [[ "$attempt" == "20" ]]; then
    echo "[ERROR] Backend did not become ready in time"
    sudo docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" logs backend --tail 100
    exit 1
  fi

  sleep 3
done

echo "[3/4] Run smoke test"
"$SCRIPT_DIR/smoke_test.sh" "$BASE_URL"

echo "[4/4] Check frontend entrypoint"
curl -I "$PUBLIC_URL" || true

echo "[OK] Remote deployment flow completed"
echo "[INFO] Frontend URL: $PUBLIC_URL"
echo "[INFO] Backend URL:  $BASE_URL"