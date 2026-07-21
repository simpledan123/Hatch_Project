#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

require_linux_runtime

duration="${1:-${CAPTURE_SECONDS:-30}}"
if [[ ! "${duration}" =~ ^[0-9]+$ ]] || (( duration < 5 || duration > 300 )); then
  printf '오류: 캡처 시간은 5~300초 사이 정수여야 합니다.\n' >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
capture_name="registration-${timestamp}.pcap"

mkdir -p "${LAB_DIR}/evidence"
compose --profile tools up -d capture

printf '%s초 동안 NGAP/NAS/PFCP/GTP-U 관련 트래픽을 캡처합니다.\n' "${duration}"
set +e
compose --profile tools exec -T capture \
  timeout "${duration}" tcpdump -i any -s 0 -U \
  -w "/evidence/${capture_name}" \
  'sctp or udp port 2152 or udp port 8805 or udp portrange 4997-4999' &
capture_pid=$!
set -e

sleep 2
compose restart ue >/dev/null

set +e
wait "${capture_pid}"
capture_status=$?
set -e

if [[ "${capture_status}" != "0" && "${capture_status}" != "124" ]]; then
  printf '오류: tcpdump가 상태 코드 %s로 종료되었습니다.\n' "${capture_status}" >&2
  exit "${capture_status}"
fi

if [[ ! -s "${LAB_DIR}/evidence/${capture_name}" ]]; then
  printf '오류: 패킷 캡처 파일이 생성되지 않았습니다.\n' >&2
  exit 1
fi

printf '완료: %s\n' "${LAB_DIR}/evidence/${capture_name}"
printf 'Wireshark 표시 필터: sctp || ngap || nas-5gs || pfcp || gtp\n'
