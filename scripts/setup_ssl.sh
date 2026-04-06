#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup_ssl.sh
# Let's Encrypt 인증서 발급 스크립트
#
# 실행 전 확인 사항:
#   1. Duck DNS 도메인이 이 서버의 공인 IP를 가리키고 있어야 함
#   2. Oracle Security List 및 ufw에서 80, 443이 열려 있어야 함
#   3. .env.prod 에 DOMAIN=your-domain.duckdns.org 가 설정되어 있어야 함
#
# 사용법:
#   chmod +x scripts/setup_ssl.sh
#   ./scripts/setup_ssl.sh
# ---------------------------------------------------------------------------
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.prod}"

# .env.prod 에서 DOMAIN 읽기
if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] $ENV_FILE 파일이 없습니다."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [[ -z "${DOMAIN:-}" ]]; then
  echo "[ERROR] .env.prod 에 DOMAIN 변수가 설정되어 있지 않습니다."
  echo "        예시: DOMAIN=your-name.duckdns.org"
  exit 1
fi

echo "[INFO] 도메인: $DOMAIN"

# ── 1. certbot 설치 ─────────────────────────────────────────────────────────
echo "[1/4] certbot 설치 확인"
if ! command -v certbot &>/dev/null; then
  echo "[INFO] certbot 설치 중..."
  sudo apt-get update -qq
  sudo apt-get install -y certbot
else
  echo "[INFO] certbot 이미 설치되어 있음"
fi

# ── 2. 컨테이너 중지 (standalone 모드는 80포트 직접 점유) ───────────────────
echo "[2/4] 기존 컨테이너 중지 (포트 80 확보)"
cd "$PROJECT_ROOT"
sudo docker compose down || true

# ── 3. 인증서 발급 ──────────────────────────────────────────────────────────
echo "[3/4] Let's Encrypt 인증서 발급 (standalone)"
sudo certbot certonly \
  --standalone \
  --non-interactive \
  --agree-tos \
  --register-unsafely-without-email \
  -d "$DOMAIN"

echo "[INFO] 인증서 발급 완료"
echo "[INFO] 경로: /etc/letsencrypt/live/$DOMAIN/"

# ── 4. 자동 갱신 크론 등록 ─────────────────────────────────────────────────
echo "[4/4] 자동 갱신 크론 등록 확인"
CRON_JOB="0 3 * * * certbot renew --quiet --pre-hook 'docker compose -f $PROJECT_ROOT/docker-compose.yml down' --post-hook 'docker compose -f $PROJECT_ROOT/docker-compose.yml up -d'"

if sudo crontab -l 2>/dev/null | grep -q "certbot renew"; then
  echo "[INFO] 자동 갱신 크론이 이미 등록되어 있음"
else
  (sudo crontab -l 2>/dev/null; echo "$CRON_JOB") | sudo crontab -
  echo "[INFO] 자동 갱신 크론 등록 완료 (매일 새벽 3시)"
fi

echo ""
echo "[OK] SSL 설정 완료"
echo "[NEXT] 이제 컨테이너를 다시 시작하세요:"
echo "       sudo docker compose --env-file .env.prod up -d --build"