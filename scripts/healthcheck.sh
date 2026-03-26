#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${1:-http://localhost:8000}"
BASE_URL="${BASE_URL%/}"
LIVE_URL="$BASE_URL/api/health/live"
READY_URL="$BASE_URL/api/health/ready"

request() {
  local url="$1"
  local tmp
  tmp="$(mktemp)"

  if ! HTTP_CODE="$(curl -sS -o "$tmp" -w "%{http_code}" "$url")"; then
    echo "[ERROR] Request failed: $url"
    rm -f "$tmp"
    exit 1
  fi

  HTTP_BODY="$(cat "$tmp")"
  rm -f "$tmp"
}

echo "[INFO] Live check -> $LIVE_URL"
request "$LIVE_URL"
echo "[INFO] live status=$HTTP_CODE body=$HTTP_BODY"
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "[ERROR] Live check failed"
  exit 1
fi

echo "[INFO] Ready check -> $READY_URL"
request "$READY_URL"
echo "[INFO] ready status=$HTTP_CODE body=$HTTP_BODY"
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "[ERROR] Ready check failed"
  exit 1
fi

echo "[OK] Service health checks passed"