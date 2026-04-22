# hatch_project

어릴 때 즐겨 하던 Hatchi(다마고치형 모바일 게임)가 서비스 종료로 사라진 것이 아쉬워서 시작한 프로젝트입니다.

브라우저에서 동작하는 웹 버전으로 복원하고, 누구나 접속할 수 있도록 실제 서버에 배포하는 것을 목표로 삼았습니다.

---

## 게임 소개

### 플로우

```
알 (egg)
  ↓ 탭해서 부화
아기 (baby) ── 랜덤 캐릭터 배정 (블롭 / 유령 / 공룡)
  ↓ 시간 + 케어
어린이 (child) → 청소년 (teen)
  ↓ 케어 방식에 따라 진화형 결정
어른 (adult) ── 5가지 진화형 (학자형 / 운동형 / 쾌활형 / 야생형 / 보통형)
  ↓ 보내주기
새 알 시작
```

### 케어 메커니즘

- 밥 먹이기 / 씻기기 / 공부 / 운동 / 놀기 / 재우기
- 시간이 지나면 배고픔, 청결, 에너지 등이 자동으로 변화
- 방치하면 아픈 상태(sick)로 전환되고 약을 먹여야 회복
- 일정 시간마다 배설물이 쌓이며 치우지 않으면 건강 하락
- 성장 기간 동안 공부 / 운동 / 놀기 횟수가 누적되어 최종 진화형 결정

### 캐릭터 & 진화

| 캐릭터 | 진화형 | 결정 조건 |
|--------|--------|-----------|
| 블롭 / 유령 / 공룡 | 학자형 | 공부 횟수 최다 |
| 블롭 / 유령 / 공룡 | 운동형 | 운동 횟수 최다 |
| 블롭 / 유령 / 공룡 | 쾌활형 | 놀기 횟수 최다 |
| 블롭 / 유령 / 공룡 | 야생형 | 아픈 횟수 누적 |
| 블롭 / 유령 / 공룡 | 보통형 | 균형 케어 |

---

## 현재 구현 기능

### 게임 로직
- 알 부화 (탭 인터랙션, 랜덤 캐릭터 배정)
- 펫 이름 짓기
- 6가지 스탯 실시간 표시 (배고픔 / 청결 / 지능 / 활동 / 에너지 / 행복)
- baby → child → teen → adult 자동 성장 (시간 기반)
- 케어 액션: `feed / clean / play / sleep / study / train / medicine / clean_poop`
- 똥 발생 및 청소 메커니즘
- 아픈 상태 시각화 및 약 액션
- 케어 이력 누적 기반 진화형 결정
- 어른 도달 시 보내주기 → 새 게임 시작
- 사망 처리 및 무지개 다리 화면
- Redis 기반 상태 조회 캐시 (TTL 30초, 액션 발생 시 무효화)
- Redis 기반 반복 액션 rate limiting

### 인프라 / 운영
- Docker Compose 기반 실행 환경 (로컬 / prod 분리)
- Oracle Cloud VM(Ubuntu 22.04) 배포, 공인 IP 외부 접속
- HAProxy L4 로드밸런서 (backend 2대 라운드로빈, 헬스체크 기반 자동 페일오버)
- Nginx 정적 서빙 및 `/api` 리버스 프록시, HTTPS 강제 리다이렉트
- Let's Encrypt + certbot HTTPS 인증서 (매일 새벽 3시 자동 갱신)
- Duck DNS 도메인 연결
- ufw + Oracle Security List 이중 방화벽
- SSH 키 인증 전용 (패스워드 로그인 비활성화)
- WireGuard VPN 서버 (peer 추가 / 제거 / 상태 확인 스크립트)
- Prometheus + Grafana 모니터링 (서버 리소스 + API 응답시간 / 에러율)
- Alertmanager 알림 임계치 6종 설정
- pg_dump 자동 백업 (gzip 압축, 무결성 검증, 7일 보존, 원격 전송 옵션)
- `/api/health/live`, `/api/health/ready` 헬스 체크 분리
- request id 및 요청 처리 시간 로그
- Prometheus metrics 엔드포인트 (`/metrics`)
- GitHub Actions backend CI (pytest)
- RUNBOOK.md 운영 절차 문서화

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | React, Vite, Nginx |
| Backend | Python, FastAPI, SQLAlchemy |
| Database | PostgreSQL, Redis |
| Infrastructure | Docker / Docker Compose, Oracle Cloud VM |
| Load Balancer | HAProxy (L4) |
| Monitoring | Prometheus, Grafana, Alertmanager, node-exporter |
| VPN | WireGuard |
| SSL | Let's Encrypt + certbot |
| CI | GitHub Actions |

---

## 아키텍처

```
[ Browser ]
    |
    v (https://*.duckdns.org)
[ Duck DNS ] → Oracle Cloud VM 공인 IP
    |
    v
[ ufw + Oracle Security List ]
    |
    v
[ Nginx (443 SSL) ]
    |
    v
[ HAProxy :80 ] ← L4 로드밸런서
    |              |
    v              v
[ FastAPI ]   [ FastAPI ]   ← backend / backend2
    |    |
    v    v
[PostgreSQL] [Redis]

[ WireGuard :51820/udp ]
[ Prometheus :9090 ] → [ Grafana :3000 ]
[ Alertmanager :9093 ]
[ node-exporter ]
```

---

## 실행 방법 (로컬)

```bash
cp .env.example .env
docker compose up --build
```

접속 주소:
- Frontend: `http://localhost:5173`
- Backend Swagger: `http://localhost:8000/docs`
- HAProxy Stats: `http://localhost:8404/stats`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

---

## 운영 스크립트

| 스크립트 | 역할 |
|----------|------|
| `healthcheck.sh` | `/live`, `/ready` 엔드포인트 호출로 서비스 상태 확인 |
| `smoke_test.sh` | 게스트 생성 → 펫 생성 → 부화 → 액션 수행 핵심 흐름 검증 |
| `deploy.sh` | 컨테이너 기동 후 healthcheck, smoke test까지 포함한 배포 흐름 재현 |
| `remote_deploy.sh` | production compose 기준으로 원격 서버 배포 |
| `setup_ssl.sh` | certbot 설치, 인증서 발급, 자동 갱신 cron 등록 |
| `server_bootstrap.sh` | 신규 Ubuntu 서버에 Docker 설치 자동화 |
| `wireguard_peer.sh` | WireGuard peer 추가 / 제거 / 목록 / 상태 확인 |
| `backup_db.sh` | DB 전체 백업, 무결성 검증, 오래된 백업 정리, 원격 전송 |

---

## 개발하면서 신경 쓴 점

### 1. 시간 경과 기반 상태 모델
버튼을 누를 때만 값이 바뀌는 방식이 아니라, 조회 시점 기준으로 경과 시간을 계산해 배고픔, 청결, 에너지 등에 반영하도록 구성했습니다. 마지막 decay 시각을 기록하고 분 단위로 누적 처리합니다.

### 2. 케어 이력 기반 진화 결정
단순히 스탯 수치만 보는 것이 아니라, 성장 기간 동안 어떤 액션을 얼마나 수행했는지를 tally로 누적해 최종 진화형을 결정합니다. 같은 캐릭터라도 플레이 방식에 따라 다른 어른이 됩니다.

### 3. Redis 기반 캐시와 rate limiting
상태 조회 API에 TTL 30초 캐시를 적용하고, 액션 발생 시 캐시를 무효화합니다. 동일 액션 반복 호출은 Redis INCR 기반 rate limiting으로 제어했습니다. Redis 장애 시에도 서비스는 계속 동작합니다.

### 4. L4 로드밸런서 기반 가용성
HAProxy로 backend 2대에 트래픽을 분산하고, 헬스체크 실패 시 자동으로 제외, 복구 시 재시작 없이 자동 편입되도록 구성했습니다.

### 5. 통합 모니터링
node-exporter로 서버 CPU / 메모리 / 디스크를 수집하고, prometheus-fastapi-instrumentator로 API 응답시간과 에러율을 계측합니다. Alertmanager로 주요 임계치 초과 시 알림이 발송됩니다.

### 6. 백업 및 복구 절차
pg_dump 전체 백업 자동화, gzip 무결성 검증, 보존 기간 관리를 스크립트로 처리했습니다. 단순 백업 파일 생성에 그치지 않고, 복구 절차까지 RUNBOOK.md에 정리했습니다.
