#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${1:-http://localhost:8000}"
API_BASE="${BASE_URL%/}/api"
NICKNAME="smoke-user-$(date +%s)"
PET_NAME="hatch-$(date +%s)"
SPECIES="egg"

request() {
  local method="$1"
  local url="$2"
  local body="${3:-}"
  local tmp
  tmp="$(mktemp)"

  if [[ -n "$body" ]]; then
    if ! HTTP_CODE="$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" "$url" -H "Content-Type: application/json" -d "$body")"; then
      echo "[ERROR] Request failed: $method $url"
      rm -f "$tmp"
      exit 1
    fi
  else
    if ! HTTP_CODE="$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" "$url")"; then
      echo "[ERROR] Request failed: $method $url"
      rm -f "$tmp"
      exit 1
    fi
  fi

  HTTP_BODY="$(cat "$tmp")"
  rm -f "$tmp"
}

json_get() {
  local json="$1"
  local key="$2"
  python3 -c 'import json,sys; data=json.load(sys.stdin); print(data[sys.argv[1]])' "$key" <<< "$json"
}

echo "[1/4] Create guest user"
request POST "$API_BASE/users/guest" "{\"nickname\":\"$NICKNAME\"}"
echo "[INFO] status=$HTTP_CODE body=$HTTP_BODY"
if [[ "$HTTP_CODE" != "201" ]]; then
  echo "[ERROR] Guest user creation failed"
  exit 1
fi
USER_ID="$(json_get "$HTTP_BODY" id)"

echo "[2/4] Create pet"
request POST "$API_BASE/pets" "{\"user_id\":$USER_ID,\"name\":\"$PET_NAME\",\"species\":\"$SPECIES\"}"
echo "[INFO] status=$HTTP_CODE body=$HTTP_BODY"
if [[ "$HTTP_CODE" != "201" ]]; then
  echo "[ERROR] Pet creation failed"
  exit 1
fi
PET_ID="$(json_get "$HTTP_BODY" id)"

echo "[3/4] Read pet state"
request GET "$API_BASE/pets/$PET_ID"
echo "[INFO] status=$HTTP_CODE body=$HTTP_BODY"
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "[ERROR] Pet read failed"
  exit 1
fi

echo "[4/4] Run feed action"
request POST "$API_BASE/pets/$PET_ID/actions/feed"
echo "[INFO] status=$HTTP_CODE body=$HTTP_BODY"
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "[ERROR] Feed action failed"
  exit 1
fi

echo "[OK] Smoke test passed (user_id=$USER_ID, pet_id=$PET_ID)"