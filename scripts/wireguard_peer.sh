#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# wireguard_peer.sh
# WireGuard 피어(peer) 추가 / 제거 / 목록 확인 스크립트
#
# 사용법:
#   ./scripts/wireguard_peer.sh add <peer_name>
#   ./scripts/wireguard_peer.sh remove <peer_name>
#   ./scripts/wireguard_peer.sh list
#   ./scripts/wireguard_peer.sh show
#
# 사전 조건:
#   - wg, wg-quick 설치 또는 WireGuard 컨테이너 실행 중
#   - 실행 환경: Oracle Cloud VM (Ubuntu 22.04)
# ---------------------------------------------------------------------------
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WG_DIR="${PROJECT_ROOT}/wireguard"
SERVER_CONF="${WG_DIR}/wg0.conf"
PEERS_DIR="${WG_DIR}/peers"
WG_INTERFACE="wg0"

# VPN 서버 주소 (클라이언트 설정 파일에 들어갈 엔드포인트)
SERVER_ENDPOINT="${WG_SERVER_ENDPOINT:-$(curl -s ifconfig.me):51820}"

# 피어에게 허용할 DNS
WG_DNS="${WG_DNS:-1.1.1.1}"

mkdir -p "$PEERS_DIR"

usage() {
  echo "사용법: $0 <command> [peer_name]"
  echo ""
  echo "Commands:"
  echo "  add <peer_name>     새 피어 생성 및 서버에 등록"
  echo "  remove <peer_name>  피어 제거"
  echo "  list                등록된 피어 목록 확인"
  echo "  show                현재 WireGuard 연결 상태 확인"
  exit 1
}

# 다음으로 사용 가능한 피어 IP 반환 (10.0.0.2 부터 순차 할당)
next_peer_ip() {
  local last_ip
  last_ip=$(grep -h "AllowedIPs" "$SERVER_CONF" 2>/dev/null | grep -oP "10\.0\.0\.\K[0-9]+" | sort -n | tail -1 || echo "1")
  echo "10.0.0.$((last_ip + 1))"
}

add_peer() {
  local peer_name="$1"
  local peer_dir="${PEERS_DIR}/${peer_name}"

  if [[ -d "$peer_dir" ]]; then
    echo "[ERROR] 피어 '${peer_name}' 이 이미 존재합니다."
    exit 1
  fi

  mkdir -p "$peer_dir"

  echo "[1/4] 피어 키 생성: ${peer_name}"
  local peer_private_key peer_public_key peer_psk
  peer_private_key=$(wg genkey)
  peer_public_key=$(echo "$peer_private_key" | wg pubkey)
  peer_psk=$(wg genpsk)

  echo "$peer_private_key" > "${peer_dir}/private.key"
  echo "$peer_public_key"  > "${peer_dir}/public.key"
  echo "$peer_psk"         > "${peer_dir}/preshared.key"
  chmod 600 "${peer_dir}/private.key" "${peer_dir}/preshared.key"

  local peer_ip
  peer_ip=$(next_peer_ip)

  echo "[2/4] 서버 설정에 피어 추가 (${peer_ip})"
  local server_public_key
  server_public_key=$(grep "PrivateKey" "$SERVER_CONF" | awk '{print $3}' | wg pubkey 2>/dev/null || echo "<서버 공개키>")

  cat >> "$SERVER_CONF" <<EOF

# Peer: ${peer_name}
[Peer]
PublicKey = ${peer_public_key}
PresharedKey = ${peer_psk}
AllowedIPs = ${peer_ip}/32
EOF

  echo "[3/4] 클라이언트 설정 파일 생성"
  cat > "${peer_dir}/${peer_name}.conf" <<EOF
[Interface]
PrivateKey = ${peer_private_key}
Address = ${peer_ip}/24
DNS = ${WG_DNS}

[Peer]
PublicKey = ${server_public_key}
PresharedKey = ${peer_psk}
Endpoint = ${SERVER_ENDPOINT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF

  echo "[4/4] 실행 중인 WireGuard 인터페이스에 핫 적용"
  if sudo wg show "$WG_INTERFACE" &>/dev/null; then
    sudo wg addconf "$WG_INTERFACE" <(
      echo "[Peer]"
      echo "PublicKey = ${peer_public_key}"
      echo "PresharedKey = ${peer_psk}"
      echo "AllowedIPs = ${peer_ip}/32"
    )
    echo "[INFO] 재시작 없이 피어 적용 완료"
  else
    echo "[INFO] WireGuard 인터페이스 미실행 — 다음 기동 시 적용됩니다"
  fi

  echo ""
  echo "[OK] 피어 '${peer_name}' 추가 완료"
  echo "[INFO] 클라이언트 설정 파일: ${peer_dir}/${peer_name}.conf"
  echo "[INFO] 할당된 VPN IP: ${peer_ip}"
}

remove_peer() {
  local peer_name="$1"
  local peer_dir="${PEERS_DIR}/${peer_name}"

  if [[ ! -d "$peer_dir" ]]; then
    echo "[ERROR] 피어 '${peer_name}' 을 찾을 수 없습니다."
    exit 1
  fi

  local peer_public_key
  peer_public_key=$(cat "${peer_dir}/public.key")

  echo "[1/3] 실행 중인 인터페이스에서 피어 제거"
  if sudo wg show "$WG_INTERFACE" &>/dev/null; then
    sudo wg set "$WG_INTERFACE" peer "$peer_public_key" remove
    echo "[INFO] 인터페이스에서 피어 제거 완료"
  fi

  echo "[2/3] 서버 설정 파일에서 피어 블록 제거"
  # Peer 블록 전체 삭제 (주석 포함)
  python3 - "$SERVER_CONF" "$peer_public_key" <<'PYEOF'
import sys

conf_path = sys.argv[1]
target_pubkey = sys.argv[2]

with open(conf_path) as f:
    lines = f.readlines()

result = []
skip = False
for line in lines:
    if line.strip().startswith("# Peer:") and not skip:
        # 다음 블록 시작 예고 — 아직 확정 안 함
        pending = [line]
        continue
    if "pending" in dir() and line.strip() == "[Peer]":
        pending.append(line)
        skip = False
        continue
    if "pending" in dir() and f"PublicKey = {target_pubkey}" in line:
        skip = True
        pending = []
        continue
    if "pending" in dir():
        result.extend(pending)
        del pending
    if skip and line.strip() == "" :
        skip = False
        continue
    if not skip:
        result.append(line)

if "pending" in dir():
    result.extend(pending)

with open(conf_path, "w") as f:
    f.writelines(result)
PYEOF

  echo "[3/3] 피어 파일 삭제"
  rm -rf "$peer_dir"

  echo "[OK] 피어 '${peer_name}' 제거 완료"
}

list_peers() {
  echo "=== 등록된 피어 목록 ==="
  if [[ ! -d "$PEERS_DIR" ]] || [[ -z "$(ls -A "$PEERS_DIR" 2>/dev/null)" ]]; then
    echo "(등록된 피어 없음)"
    return
  fi

  for peer_dir in "$PEERS_DIR"/*/; do
    local peer_name
    peer_name=$(basename "$peer_dir")
    local peer_ip
    peer_ip=$(grep "Address" "${peer_dir}/${peer_name}.conf" 2>/dev/null | awk '{print $3}' | cut -d/ -f1 || echo "unknown")
    echo "  - ${peer_name} (VPN IP: ${peer_ip})"
  done
}

show_status() {
  echo "=== WireGuard 연결 상태 ==="
  if sudo wg show "$WG_INTERFACE" &>/dev/null; then
    sudo wg show "$WG_INTERFACE"
  else
    echo "[INFO] WireGuard 인터페이스(${WG_INTERFACE})가 실행 중이지 않습니다."
  fi
}

# ── 메인 ────────────────────────────────────────────────────────────────────
case "${1:-}" in
  add)
    [[ -z "${2:-}" ]] && usage
    add_peer "$2"
    ;;
  remove)
    [[ -z "${2:-}" ]] && usage
    remove_peer "$2"
    ;;
  list)
    list_peers
    ;;
  show)
    show_status
    ;;
  *)
    usage
    ;;
esac