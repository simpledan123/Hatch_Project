#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

require_command docker

if [[ "${1:-}" == "--purge" ]]; then
  printf 'Lab 컨테이너와 MongoDB 볼륨을 함께 제거합니다.\n'
  compose --profile tools down --volumes --remove-orphans
else
  compose --profile tools down --remove-orphans
  printf '가입자 데이터 볼륨은 보존했습니다. 완전 삭제: %s --purge\n' "$0"
fi
