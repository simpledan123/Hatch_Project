#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

require_linux_runtime

if [[ -z "${HATCH_HEALTH_URL:-}" || "${HATCH_HEALTH_URL}" == *"example.duckdns.org"* ]]; then
  printf '오류: .env의 HATCH_HEALTH_URL을 실제 Hatch 주소로 변경하세요.\n' >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
result_file="${LAB_DIR}/evidence/test-result-${timestamp}.md"
mkdir -p "${LAB_DIR}/evidence"

registration_status="FAIL"
pdu_status="FAIL"
hatch_status="FAIL"
ue_address="인터페이스 없음"
health_output="요청하지 못함"

if compose ps --status running ue | grep -q hatch-5g-ue; then
  registration_status="RUNNING"
fi

if ue_address="$(compose exec -T ue ip -brief address show uesimtun0 2>/dev/null)"; then
  pdu_status="PASS"
  registration_status="PASS"
fi

compose --profile tools up -d tester >/dev/null
set +e
health_output="$(
  compose --profile tools exec -T tester \
    curl --silent --show-error --fail \
    --max-time 15 \
    --interface uesimtun0 \
    "${HATCH_HEALTH_URL}" 2>&1
)"
curl_status=$?
set -e

if [[ "${curl_status}" == "0" ]]; then
  hatch_status="PASS"
fi

{
  printf '# Hatch 5G Lab 시험 결과\n\n'
  printf -- '- 실행 시각(UTC): `%s`\n' "${timestamp}"
  printf -- '- 대상 주소: `%s`\n\n' "${HATCH_HEALTH_URL}"
  printf '| 시험 항목 | 결과 |\n'
  printf '|---|---|\n'
  printf '| TC-01 UE 등록 | %s |\n' "${registration_status}"
  printf '| TC-02 PDU Session 및 TUN | %s |\n' "${pdu_status}"
  printf '| TC-03 Hatch API 종단 간 연결 | %s |\n\n' "${hatch_status}"
  printf '## UE 인터페이스\n\n```text\n%s\n```\n\n' "${ue_address}"
  printf '## Hatch 응답\n\n```text\n%s\n```\n\n' "${health_output}"
  printf '> 이 파일은 실행 결과로 자동 생성되었습니다. 결과를 임의로 수정하지 말고 원본 로그·PCAP과 함께 보관합니다.\n'
} >"${result_file}"

printf '시험 결과: %s\n' "${result_file}"
printf 'TC-01=%s, TC-02=%s, TC-03=%s\n' \
  "${registration_status}" "${pdu_status}" "${hatch_status}"

if [[ "${pdu_status}" != "PASS" || "${hatch_status}" != "PASS" ]]; then
  exit 1
fi
