#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

require_linux_runtime

compose up -d db

for attempt in $(seq 1 20); do
  if compose exec -T db mongosh --quiet --eval "db.adminCommand('ping').ok" | grep -q 1; then
    break
  fi
  if [[ "${attempt}" == "20" ]]; then
    printf '오류: MongoDB 준비 상태를 확인하지 못했습니다.\n' >&2
    exit 1
  fi
  sleep 2
done

compose exec -T db mongosh \
  --quiet \
  mongodb://localhost:27017/open5gs \
  /docker-entrypoint-initdb.d/01-subscriber.js

printf '가입자 정보를 멱등 방식으로 등록했습니다.\n'
