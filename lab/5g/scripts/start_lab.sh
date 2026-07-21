#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

require_linux_runtime

printf '1/3 컨테이너 이미지를 확인합니다.\n'
compose pull

printf '2/3 5G Core와 UERANSIM을 시작합니다.\n'
compose up -d

printf '3/3 UE PDU Session(TUN 인터페이스)을 확인합니다.\n'
for attempt in $(seq 1 30); do
  if compose exec -T ue ip link show uesimtun0 >/dev/null 2>&1; then
    printf '성공: uesimtun0 인터페이스가 생성되었습니다.\n'
    compose exec -T ue ip -brief address show uesimtun0
    compose ps
    exit 0
  fi

  if (( attempt % 5 == 0 )); then
    printf '대기 중: UE 등록 및 PDU Session 생성 확인 (%s/30)\n' "${attempt}"
  fi
  sleep 4
done

printf '오류: 제한 시간 안에 uesimtun0이 생성되지 않았습니다.\n' >&2
printf '확인 명령: %s\n' "docker compose -f lab/5g/docker-compose.5g.yml logs amf smf gnb ue" >&2
compose logs --no-color --tail=120 amf smf gnb ue >&2
exit 1
