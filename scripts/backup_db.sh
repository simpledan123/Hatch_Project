#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# backup_db.sh
# PostgreSQL 데이터베이스 자동 백업 스크립트
#
# 기능:
#   - pg_dump 기반 전체 백업 (plain SQL)
#   - 백업 파일 gzip 압축
#   - 보존 기간 초과 백업 자동 삭제 (기본 7일)
#   - 백업 성공/실패 로그 기록
#   - 선택적 원격 서버 전송 (scp)
#
# 사용법:
#   ./scripts/backup_db.sh
#   BACKUP_RETENTION_DAYS=14 ./scripts/backup_db.sh
#
# cron 등록 예시 (매일 새벽 2시):
#   0 2 * * * /path/to/hatch_project/scripts/backup_db.sh >> /var/log/hatch_backup.log 2>&1
# ---------------------------------------------------------------------------
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.prod}"

# ── 환경변수 로드 ────────────────────────────────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] $ENV_FILE 파일이 없습니다."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

# ── 설정 ─────────────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILENAME="hatch_db_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

# 원격 전송 설정 (선택 — 환경변수로 활성화)
REMOTE_BACKUP_ENABLED="${REMOTE_BACKUP_ENABLED:-false}"
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_USER="${REMOTE_USER:-}"
REMOTE_PATH="${REMOTE_PATH:-/backups/hatch}"
REMOTE_SSH_KEY="${REMOTE_SSH_KEY:-$HOME/.ssh/id_rsa}"

# ── 백업 디렉토리 생성 ───────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# ── 1. pg_dump 실행 ───────────────────────────────────────────────────────
log "INFO 백업 시작: ${BACKUP_FILENAME}"

if ! sudo docker compose --env-file "$ENV_FILE" -f "$PROJECT_ROOT/docker-compose.yml" \
  exec -T db \
  pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
  | gzip > "$BACKUP_PATH"; then
  log "ERROR pg_dump 실패"
  rm -f "$BACKUP_PATH"
  exit 1
fi

BACKUP_SIZE="$(du -sh "$BACKUP_PATH" | cut -f1)"
log "INFO 백업 완료: ${BACKUP_PATH} (${BACKUP_SIZE})"

# ── 2. 백업 파일 무결성 확인 ─────────────────────────────────────────────
if ! gzip -t "$BACKUP_PATH" 2>/dev/null; then
  log "ERROR 백업 파일 손상 감지: ${BACKUP_PATH}"
  rm -f "$BACKUP_PATH"
  exit 1
fi
log "INFO 무결성 확인 통과"

# ── 3. 원격 서버 전송 (선택) ─────────────────────────────────────────────
if [[ "$REMOTE_BACKUP_ENABLED" == "true" ]]; then
  if [[ -z "$REMOTE_HOST" || -z "$REMOTE_USER" ]]; then
    log "WARN REMOTE_HOST 또는 REMOTE_USER 미설정 — 원격 전송 건너뜀"
  else
    log "INFO 원격 전송 시작: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
    if scp -i "$REMOTE_SSH_KEY" -o StrictHostKeyChecking=no \
      "$BACKUP_PATH" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"; then
      log "INFO 원격 전송 완료"
    else
      log "WARN 원격 전송 실패 — 로컬 백업은 유지됩니다"
    fi
  fi
fi

# ── 4. 오래된 백업 삭제 ───────────────────────────────────────────────────
log "INFO ${BACKUP_RETENTION_DAYS}일 초과 백업 정리 중..."
DELETED_COUNT=0
while IFS= read -r old_file; do
  rm -f "$old_file"
  log "INFO 삭제: $(basename "$old_file")"
  ((DELETED_COUNT++))
done < <(find "$BACKUP_DIR" -name "hatch_db_*.sql.gz" -mtime +"$BACKUP_RETENTION_DAYS")

log "INFO 정리 완료: ${DELETED_COUNT}개 삭제"

# ── 5. 백업 목록 출력 ─────────────────────────────────────────────────────
log "INFO 현재 보관 중인 백업 목록:"
find "$BACKUP_DIR" -name "hatch_db_*.sql.gz" -printf "  %f (%s bytes)\n" | sort

log "INFO 백업 프로세스 완료"