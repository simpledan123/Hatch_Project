# RUNBOOK

> hatch_project 운영 절차 문서
> 서비스 기동, 상태 점검, 장애 대응, 배포, 인증서 갱신, 백업 절차를 정리한 문서입니다.

운영 서버에서는 아래 함수를 셸에 등록한 뒤 이후 명령의 `dc`로 사용합니다.

```bash
dc() {
  sudo docker compose \
    --env-file .env.prod \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    "$@"
}
```

---

## 목차

1. [서비스 기동 / 중지 / 재시작](#1-서비스-기동--중지--재시작)
2. [상태 확인](#2-상태-확인)
3. [장애 대응](#3-장애-대응)
4. [배포 절차](#4-배포-절차)
5. [SSL 인증서 갱신](#5-ssl-인증서-갱신)
6. [로그 확인](#6-로그-확인)
7. [데이터베이스 백업 및 복구](#7-데이터베이스-백업-및-복구)

---

## 1. 서비스 기동 / 중지 / 재시작

### 기동
```bash
cd /path/to/hatch_project
dc up -d
```

### 중지
```bash
dc down
```

### 재시작 (전체)
```bash
dc down
dc up -d
```

### 특정 컨테이너만 재시작
```bash
dc restart backend
dc restart frontend
```

### 컨테이너 상태 확인
```bash
dc ps
```

정상 상태 예시:
```
NAME                  STATUS
hatch-db              Up (healthy)
hatch-redis           Up (healthy)
hatch-backend         Up
hatch-backend2        Up
hatch-haproxy         Up
hatch-frontend        Up
hatch-wireguard       Up
hatch-prometheus      Up
hatch-grafana         Up
hatch-alertmanager    Up
hatch-node-exporter   Up
```

---

## 2. 상태 확인

### 헬스 체크 스크립트 실행
```bash
./scripts/healthcheck.sh
```

정상 출력 예시:
```
[INFO] Live check -> http://localhost:8000/api/health/live
[INFO] live status=200 body={"status":"ok"}
[INFO] Ready check -> http://localhost:8000/api/health/ready
[INFO] ready status=200 body={"status":"ok","database":true,"redis":true}
[OK] Service health checks passed
```

### HAProxy HTTP 프록시 상태 확인
```bash
# 통계 대시보드 (브라우저)
http://localhost:8404/stats

# 백엔드 풀 상태 확인
curl -s http://localhost:8080/api/health/live
```

HAProxy stats에서 확인할 항목:
- `backend1`이 정상이고 `backend2`가 backup 상태 → 주 서버가 요청 처리 중
- `backend1`이 DOWN이고 `backend2`가 요청 처리 중 → 대기 서버로 자동 전환된 상태
- `backend1`이 3회 연속 정상 응답 → 주 서버로 자동 복귀

### WireGuard VPN 상태 확인
```bash
./scripts/wireguard_peer.sh show
./scripts/wireguard_peer.sh list
```

### 수동 확인
```bash
curl -s http://localhost:8000/api/health/live
curl -s http://localhost:8000/api/health/ready
```

### 외부 접속 확인
```bash
curl -I https://your-name.duckdns.org
```

---

## 3. 장애 대응

### 3-1. 컨테이너가 올라오지 않는 경우

```bash
dc logs --tail 100
dc logs backend --tail 100
dc logs db --tail 100
dc logs frontend --tail 100
```

조치 순서:
1. 로그에서 에러 메시지 확인
2. `.env.prod` 환경변수 누락 여부 확인
3. 포트 충돌 여부 확인 (`sudo ss -tlnp | grep 80`)
4. 컨테이너 내리고 다시 기동

---

### 3-2. DB 연결 실패 (`"database": false`)

```bash
dc ps db
dc logs db --tail 50
dc restart db
./scripts/healthcheck.sh
```

DB 재시작 후 backend도 재시작:
```bash
dc restart backend backend2
```

---

### 3-3. Redis 연결 실패 (`"redis": false`)

```bash
dc exec redis redis-cli ping
dc restart redis
dc restart backend backend2
```

Redis 장애 시 캐시 및 rate limiting만 비활성화되고 서비스는 계속 동작합니다.

---

### 3-4. HAProxy 백엔드 서버 장애

```bash
# HAProxy stats 확인
curl http://localhost:8404/stats

# 장애 서버 로그 확인
dc logs backend --tail 100

# 서버 재시작 (HAProxy가 자동으로 복귀 감지)
dc restart backend
```

fall 2 설정으로 2회 헬스체크 실패 시 자동 제외, rise 3 설정으로 3회 성공 시 자동 복귀합니다.

---

### 3-5. Nginx (프론트엔드) 접속 불가

```bash
dc logs frontend --tail 50
dc exec frontend nginx -t
dc restart frontend
sudo certbot certificates
```

---

### 3-6. 외부 접속 불가

확인 순서:
1. Oracle Security List 80, 443 Ingress 허용 여부 확인
2. ufw 상태 확인: `sudo ufw status`
3. iptables 확인: `sudo iptables -L INPUT -n | grep -E "80|443"`
4. Duck DNS 도메인 → 공인 IP 확인

---

## 4. 배포 절차

```bash
git pull origin main
./scripts/deploy.sh
```

로컬 배포는 `deploy.sh`, 운영 배포는 `.env.prod`와 두 Compose 파일을 사용하는 `remote_deploy.sh`를 실행합니다. 스크립트 내부 동작은 다음과 같습니다.
1. `docker compose up -d --build`
2. healthcheck 통과 대기 (최대 60초)
3. smoke test 실행
4. 완료 메시지 출력

---

## 5. SSL 인증서 갱신

### 자동 갱신 확인
```bash
sudo crontab -l | grep certbot
```

### 수동 갱신
```bash
dc down
sudo certbot renew
dc up -d
```

### 인증서 만료일 확인
```bash
sudo certbot certificates
```

---

## 6. 로그 확인

```bash
dc logs --tail 100
dc logs backend --tail 100
dc logs -f backend
```

### request_id 기반 요청 추적
```bash
dc logs backend | grep "request_id=abc-123"
```

---

## 7. 데이터베이스 백업 및 복구

### 백업 정책

| 항목 | 설정 |
|---|---|
| 백업 방식 | pg_dump 전체 백업 (plain SQL + gzip 압축) |
| 보존 기간 | 7일 (BACKUP_RETENTION_DAYS로 조정 가능) |
| 백업 위치 | `./backups/` |
| 파일명 형식 | `hatch_db_YYYYMMDD_HHMMSS.sql.gz` |

### 수동 백업 실행
```bash
chmod +x scripts/backup_db.sh
./scripts/backup_db.sh
```

정상 출력 예시:
```
[2025-01-01 02:00:00] INFO 백업 시작: hatch_db_20250101_020000.sql.gz
[2025-01-01 02:00:03] INFO 백업 완료: ./backups/hatch_db_20250101_020000.sql.gz (2.1M)
[2025-01-01 02:00:03] INFO 무결성 확인 통과
[2025-01-01 02:00:03] INFO 7일 초과 백업 정리 중...
[2025-01-01 02:00:03] INFO 정리 완료: 0개 삭제
[2025-01-01 02:00:03] INFO 백업 프로세스 완료
```

### 자동 백업 cron 등록 (매일 새벽 2시)
```bash
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/hatch_project/scripts/backup_db.sh >> /var/log/hatch_backup.log 2>&1") | crontab -

# 등록 확인
crontab -l | grep backup
```

### 원격 서버 전송 활성화 (.env.prod에 추가)
```env
REMOTE_BACKUP_ENABLED=true
REMOTE_HOST=backup-server-ip
REMOTE_USER=ubuntu
REMOTE_PATH=/backups/hatch
REMOTE_SSH_KEY=/home/ubuntu/.ssh/id_rsa
```

### 백업 목록 확인
```bash
ls -lh backups/
```

### 복구 절차

#### 1. 복구할 백업 파일 선택
```bash
ls -lht backups/
```

#### 2. 서비스 중지
```bash
dc stop backend backend2 haproxy
```

#### 3. 기존 DB 초기화 및 복구
```bash
# 압축 해제 후 복구
gunzip -c backups/hatch_db_YYYYMMDD_HHMMSS.sql.gz \
  | dc exec -T db \
    psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

#### 4. 서비스 재시작
```bash
dc start backend backend2 haproxy
./scripts/healthcheck.sh
```

#### 5. 복구 확인
```bash
./scripts/smoke_test.sh
```
