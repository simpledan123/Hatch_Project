#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${LAB_DIR}/docker-compose.5g.yml"
ENV_FILE="${ENV_FILE:-${LAB_DIR}/.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  ENV_FILE="${LAB_DIR}/.env.example"
  printf '알림: .env가 없어 .env.example을 사용합니다. HATCH_HEALTH_URL을 확인하세요.\n' >&2
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

compose() {
  docker compose \
    --project-directory "${LAB_DIR}" \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    "$@"
}

require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    printf '오류: %s 명령을 찾을 수 없습니다.\n' "${command_name}" >&2
    exit 1
  fi
}

require_linux_runtime() {
  require_command docker

  if [[ "$(uname -s)" != "Linux" ]]; then
    printf '오류: UERANSIM TUN 인터페이스는 Linux Docker 호스트에서 실행하세요.\n' >&2
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    printf '오류: Docker 데몬에 연결할 수 없습니다.\n' >&2
    exit 1
  fi

  if [[ ! -c /dev/net/tun ]]; then
    printf '오류: /dev/net/tun이 없습니다. sudo modprobe tun 실행 후 다시 확인하세요.\n' >&2
    exit 1
  fi
}
