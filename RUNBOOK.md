# RUNBOOK

> hatch_project 운영 절차 문서
> 서비스 기동, 상태 점검, 장애 대응, 배포, 인증서 갱신 절차를 정리한 문서입니다.

---

## 목차

1. [서비스 기동 / 중지 / 재시작](#1-서비스-기동--중지--재시작)
2. [상태 확인](#2-상태-확인)
3. [장애 대응](#3-장애-대응)
4. [배포 절차](#4-배포-절차)
5. [SSL 인증서 갱신](#5-ssl-인증서-갱신)
6. [로그 확인](#6-로그-확인)

---

## 1. 서비스 기동 / 중지 / 재시작

### 기동
```bash
cd /path/to/hatch_project
sudo docker compose --env-file .env.prod up -d
```

### 중지
```bash
sudo docker compose --env-file .env.prod down
```

### 재시작 (전체)
```bash
sudo docker compose --env-file .env.prod down
sudo docker compose --env-file .env.prod up -d
```

### 특정 컨테이너만 재시작
```bash
# 백엔드만
sudo docker compose --env-file .env.prod restart backend

# 프론트엔드(Nginx)만
sudo docker compose --env-file .env.prod restart frontend
```

### 컨테이너 상태 확인
```bash
sudo docker compose ps
```

정상 상태 예시:
```
NAME             STATUS
hatch-db         Up (healthy)
hatch-redis      Up (healthy)
hatch-backend    Up
hatch-frontend   Up
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

### 수동 확인
```bash
# 서비스 생존 여부
curl -s http://localhost:8000/api/health/live

# DB / Redis 연결 상태 포함
curl -s http://localhost:8000/api/health/ready
```

`/ready` 응답 필드 설명:

| 필드 | 정상값 | 비정상값 |
|---|---|---|
| status | ok | degraded |
| database | true | false |
| redis | true | false |

### 외부 접속 확인
```bash
curl -I https://your-name.duckdns.org
```

HTTP 200 또는 301 응답이 와야 정상입니다.

---

## 3. 장애 대응

### 3-1. 컨테이너가 올라오지 않는 경우

```bash
# 전체 로그 확인
sudo docker compose logs --tail 100

# 특정 컨테이너 로그 확인
sudo docker compose logs backend --tail 100
sudo docker compose logs db --tail 100
sudo docker compose logs frontend --tail 100
```

조치 순서:
1. 로그에서 에러 메시지 확인
2. `.env.prod` 환경변수 누락 여부 확인
3. 포트 충돌 여부 확인 (`sudo ss -tlnp | grep 80`)
4. 컨테이너 내리고 다시 기동

---

### 3-2. DB 연결 실패 (`"database": false`)

```bash
# DB 컨테이너 상태 확인
sudo docker compose ps db

# DB 로그 확인
sudo docker compose logs db --tail 50

# DB 컨테이너 재시작
sudo docker compose restart db

# DB 재시작 후 헬스 체크 재확인
./scripts/healthcheck.sh
```

DB 컨테이너가 healthy 상태가 될 때까지 대기 후 backend를 재시작합니다.
```bash
sudo docker compose restart backend
```

---

### 3-3. Redis 연결 실패 (`"redis": false`)

```bash
# Redis 컨테이너 상태 확인
sudo docker compose ps redis

# Redis 직접 ping 테스트
sudo docker compose exec redis redis-cli ping
# 정상: PONG

# Redis 재시작
sudo docker compose restart redis
sudo docker compose restart backend
```

Redis 장애 시 서비스는 DB fallback으로 계속 동작합니다.
캐시 및 rate limiting 기능만 일시적으로 비활성화됩니다.

---

### 3-4. Nginx (프론트엔드) 접속 불가

```bash
# Nginx 로그 확인
sudo docker compose logs frontend --tail 50

# Nginx 설정 문법 검사
sudo docker compose exec frontend nginx -t

# Nginx 재시작
sudo docker compose restart frontend
```

HTTPS 접속 불가 시 인증서 만료 여부를 먼저 확인합니다.
```bash
sudo certbot certificates
```

---

### 3-5. 외부 접속 불가 (서버는 정상인데 브라우저에서 안 열림)

확인 순서:

1. Oracle Security List에서 80, 443 Ingress 허용 여부 확인 (Oracle 콘솔)
2. ufw 상태 확인
```bash
sudo ufw status
```
3. iptables 규칙 확인
```bash
sudo iptables -L INPUT -n | grep -E "80|443"
```
4. Duck DNS에서 도메인이 올바른 공인 IP를 가리키는지 확인

---

## 4. 배포 절차

### 일반 배포 (코드 변경 후)
```bash
cd /path/to/hatch_project

# 최신 코드 받기
git pull origin main

# 배포 스크립트 실행 (빌드 → 기동 → healthcheck → smoke test 순서)
./scripts/deploy.sh
```

`deploy.sh` 내부 동작 순서:
1. `docker compose up -d --build`
2. healthcheck 통과 대기 (최대 60초, 3초 간격)
3. smoke test 실행
4. 완료 메시지 출력

smoke test 실패 시 backend 로그를 먼저 확인합니다.
```bash
sudo docker compose logs backend --tail 100
```

---

## 5. SSL 인증서 갱신

### 자동 갱신 확인
certbot 자동 갱신 크론이 등록되어 있습니다. (매일 새벽 3시)

```bash
# 크론 등록 여부 확인
sudo crontab -l | grep certbot
```

### 수동 갱신 (만료 임박 시)
```bash
# 컨테이너 중지
sudo docker compose down

# 인증서 갱신
sudo certbot renew

# 컨테이너 재시작
sudo docker compose --env-file .env.prod up -d
```

### 인증서 만료일 확인
```bash
sudo certbot certificates
```

출력 예시:
```
Expiry Date: 2025-09-01 (VALID: 89 days)
```

---

## 6. 로그 확인

### 전체 컨테이너 로그
```bash
sudo docker compose logs --tail 100
```

### 컨테이너별 로그
```bash
sudo docker compose logs backend --tail 100
sudo docker compose logs db --tail 50
sudo docker compose logs redis --tail 50
sudo docker compose logs frontend --tail 50
```

### 실시간 로그 스트리밍
```bash
sudo docker compose logs -f backend
```

### request_id 기반 요청 추적

백엔드는 모든 요청에 `request_id`와 처리 시간(`elapsed_ms`)을 로그로 남깁니다.

```
2025-01-01 12:00:00 | INFO | request_id=abc-123 method=POST path=/api/pets/1/actions/feed status=200 elapsed_ms=45.2
```

특정 요청 추적 시:
```bash
sudo docker compose logs backend | grep "request_id=abc-123"
```
