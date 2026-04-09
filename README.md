# hatch_project

`hatch_project`는 브라우저에서 펫을 생성하고 돌보는 다마고치 스타일의 웹 게임을 소재로 삼아,
상태 저장형 웹 서비스의 구현과 운영 보강을 함께 다뤄보는 프로젝트입니다.

단순히 화면에서 버튼을 누르는 데모가 아니라, 펫의 상태를 서버와 데이터베이스에 저장하고,
시간이 지남에 따라 상태가 실제로 변화하도록 구성했습니다.

로컬 Docker Compose 환경에서 먼저 실행 및 점검 흐름을 검증한 뒤,
Oracle Cloud VM(Ubuntu 22.04)에 실제 배포하여 공인 IP 기반 외부 접속,
HTTPS 인증서 적용, 방화벽 설정까지 완료

---

## 프로젝트 목표

- 상태 저장형 웹 서비스 설계
- Docker Compose 기반 실행 환경 정리
- health check / smoke test / deploy script 작성
- Oracle Cloud VM(Ubuntu 22.04) 실제 배포
- 공인 IP 기반 외부 접속 환경 구성
- ufw + Oracle Security List 방화벽 설정
- SSH 키 인증 전용 설정 (패스워드 로그인 비활성화)
- Let's Encrypt + certbot HTTPS 인증서 발급 및 자동 갱신
- Duck DNS 도메인 연결
- HAProxy L4 로드밸런서 + 자동 페일오버
- WireGuard VPN 서버 구성 및 peer 관리
- Prometheus + Grafana 기반 서버/서비스 모니터링
- Alertmanager 알림 임계치 설정
- DB 자동 백업 및 복구 절차 구성
- Jira 기반 작업 관리
- Runbook 중심의 운영 문서화

---

## 프로젝트 소개

플레이어는 먼저 게스트 사용자를 만들고, 자신의 펫을 생성한 뒤 상태를 확인할 수 있습니다.
이후 `feed`, `clean`, `play`, `sleep` 액션을 수행하면서 배고픔, 청결도, 행복도, 에너지, 건강 수치를 관리하게 됩니다.

시간이 지나면 상태가 계속 변화하며, 상태에 따라 `alive`, `sick`, `dead`로 구분됩니다.
단순 CRUD 형태를 넘어서, 시간 경과에 따라 상태가 달라지는 작은 웹 서비스를 구현하는 데 초점을 두었습니다.

---

## 현재 구현 기능

- 게스트 사용자 생성
- 펫 생성
- 펫 상태 조회
- `feed / clean / play / sleep` 액션
- 시간 경과에 따른 상태 변화
- 위험 상태(`sick`) 및 사망 상태(`dead`) 반영
- 액션 로그 저장
- Redis 기반 상태 조회 캐시
- Redis 기반 반복 액션 제어 (rate limiting)
- `/api/health/live`, `/api/health/ready` 헬스 체크 엔드포인트
- request id 및 요청 처리 시간 로그
- Prometheus metrics 엔드포인트 (`/metrics`)

---

## 운영 보강 항목

기능 구현 외에도 아래와 같은 운영 보강 요소를 직접 구성하고 검증했습니다.

### 배포 환경
- Docker Compose 기반 실행 환경 통일 (로컬 / prod 분리)
- Oracle Cloud VM(Ubuntu 22.04) 공인 IP 기반 외부 접속 환경 구성
- Nginx 기반 프론트 정적 서빙 및 `/api` 리버스 프록시 구성

### 가용성
- HAProxy L4 로드밸런서 구성 (backend / backend2 라운드로빈)
- `/api/health/live` 기반 헬스체크 (3초 간격, fall 2, rise 3)
- 헬스체크 실패 시 자동 트래픽 제외, 복구 시 자동 편입
- HAProxy 통계 대시보드 (`:8404/stats`)

### 네트워크 / 보안
- ufw + Oracle Security List 이중 방화벽 설정 (22, 80, 443, 51820/udp만 허용)
- SSH 키 인증 전용 설정 (패스워드 로그인 비활성화)
- Let's Encrypt + certbot HTTPS 인증서 발급 및 자동 갱신 (매일 새벽 3시 cron)
- Duck DNS 도메인 연결 (`*.duckdns.org`)
- TLSv1.2 / TLSv1.3 적용, HTTP → HTTPS 강제 리다이렉트
- WireGuard VPN 서버 구성 (UDP 51820)
  - peer 추가 / 제거 / 상태 확인 스크립트
  - 키 생성 및 IP 자동 할당 (10.0.0.0/24)
  - 실행 중인 인터페이스에 재시작 없이 peer 핫 적용

### 모니터링
- Prometheus + node-exporter 기반 서버 리소스 수집 (CPU / 메모리 / 디스크)
- prometheus-fastapi-instrumentator 기반 API 응답시간 / 요청 수 / 에러율 수집
- Grafana 대시보드 (Prometheus datasource 자동 프로비저닝)
- Alertmanager 알림 임계치 설정
  - BackendDown: 백엔드 30초 이상 응답 없음
  - HighCpuUsage: CPU 2분 이상 80% 초과
  - HighMemoryUsage: 메모리 2분 이상 85% 초과
  - HighDiskUsage: 디스크 90% 초과
  - HighApiLatency: API p95 응답시간 1초 초과
  - HighErrorRate: 5xx 에러율 5% 초과

### 백업
- pg_dump 기반 전체 백업 + gzip 압축 자동화
- 백업 파일 무결성 자동 검증 (gzip -t)
- 보존 기간 초과 백업 자동 삭제 (기본 7일)
- 원격 서버 scp 전송 옵션
- cron 기반 자동 실행 (매일 새벽 2시)
- 복구 절차 문서화 (gunzip + psql)

### 운영 스크립트
- `healthcheck.sh`: `/live`, `/ready` 엔드포인트 호출로 서비스 상태 확인
- `smoke_test.sh`: 게스트 생성 → 펫 생성 → 상태 조회 → 액션 수행 핵심 흐름 검증
- `deploy.sh`: 컨테이너 기동 후 healthcheck, smoke test까지 포함한 배포 흐름 재현
- `remote_deploy.sh`: production compose 기준으로 원격 서버 배포 흐름 실행
- `setup_ssl.sh`: certbot 설치, 인증서 발급, 자동 갱신 cron 등록
- `server_bootstrap.sh`: 신규 Ubuntu 서버에 Docker 설치 자동화
- `wireguard_peer.sh`: WireGuard peer 추가 / 제거 / 목록 / 상태 확인
- `backup_db.sh`: DB 전체 백업, 무결성 검증, 오래된 백업 정리, 원격 전송

### 문서화
- `RUNBOOK.md`: 기동 / 점검 / 장애 대응 / 배포 / 인증서 갱신 / 백업 복구 절차 정리
- Jira 기반 스프린트 관리

---

## 기술 스택

### Frontend
- React
- Vite
- Nginx (정적 서빙, 리버스 프록시, HTTPS)

### Backend
- Python
- FastAPI
- SQLAlchemy

### Data
- PostgreSQL
- Redis

### Infrastructure / DevOps
- Docker / Docker Compose
- Oracle Cloud VM (Ubuntu 22.04)
- HAProxy (L4 로드밸런서)
- WireGuard (VPN)
- Prometheus / Grafana / Alertmanager
- node-exporter
- Let's Encrypt + certbot
- Duck DNS
- ufw (방화벽)
- Bash
- GitHub Actions
- Jira

---

## 배포 구조

```text
[ Browser ]
    |
    v (https://your-name.duckdns.org)
[ Duck DNS ] → Oracle Cloud VM 공인 IP
    |
    v
[ ufw + Oracle Security List ] (22, 80, 443, 51820/udp만 허용)
    |
    v
[ Nginx (443 SSL) ]
    |
    v
[ HAProxy :80 ] ← L4 로드밸런서
    |                    |
    v                    v
[ backend:8000 ]   [ backend2:8000 ]
    |
    +→ [ PostgreSQL ]
    +→ [ Redis ]

[ WireGuard :51820/udp ] ← VPN 서버
[ Prometheus :9090 ]     ← 메트릭 수집
[ Grafana :3000 ]        ← 대시보드
[ Alertmanager :9093 ]   ← 알림
[ node-exporter ]        ← 서버 리소스 수집
```

---

## 실행 방법 (로컬)

### 1. 환경 변수 파일 생성
```bash
cp .env.example .env
```

### 2. Docker Compose 실행
```bash
docker compose up --build
```

### 3. 접속 주소
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- HAProxy Stats: `http://localhost:8404/stats`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

---

## Production 배포 방법 (Oracle Cloud VM 기준)

### 사전 조건
- Oracle Cloud VM 생성 완료 (Ubuntu 22.04)
- Oracle Security List에서 22, 80, 443, 51820(UDP) Ingress 허용
- ufw 설정 완료
- SSH 키 인증 설정 완료
- Duck DNS 도메인이 VM 공인 IP를 가리키고 있어야 함

### 1. 서버 초기 설정
```bash
# Docker 설치
chmod +x scripts/server_bootstrap.sh
./scripts/server_bootstrap.sh

# 방화벽 설정
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 51820/udp
sudo ufw enable
```

### 2. SSL 인증서 발급
```bash
chmod +x scripts/*.sh
./scripts/setup_ssl.sh
```

### 3. WireGuard VPN 설정
```bash
# 서버 키 생성
wg genkey | tee wireguard/server_private.key | wg pubkey > wireguard/server_public.key

# 설정 파일 생성
cp wireguard/wg0.conf.template wireguard/wg0.conf
# wg0.conf 에 PrivateKey 값 입력

# peer 추가
./scripts/wireguard_peer.sh add my-laptop
```

### 4. 백업 cron 등록
```bash
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/hatch_project/scripts/backup_db.sh >> /var/log/hatch_backup.log 2>&1") | crontab -
```

### 5. 배포
```bash
./scripts/remote_deploy.sh
```

---

## 운영 스크립트

`scripts/` 폴더에 아래 스크립트를 두고 운영 흐름을 보강했습니다.

| 스크립트 | 역할 |
|---|---|
| `healthcheck.sh` | `/live`, `/ready` 엔드포인트 호출로 서비스 상태 확인 |
| `smoke_test.sh` | 게스트 생성 → 펫 생성 → 상태 조회 → 액션 수행 핵심 흐름 검증 |
| `deploy.sh` | 컨테이너 기동 후 healthcheck, smoke test까지 포함한 배포 흐름 재현 |
| `remote_deploy.sh` | production compose 기준으로 원격 서버 배포 흐름 실행 |
| `setup_ssl.sh` | certbot 설치, 인증서 발급, 자동 갱신 cron 등록 |
| `server_bootstrap.sh` | 신규 Ubuntu 서버에 Docker 설치 자동화 |
| `wireguard_peer.sh` | WireGuard peer 추가 / 제거 / 목록 / 상태 확인 |
| `backup_db.sh` | DB 전체 백업, 무결성 검증, 오래된 백업 정리, 원격 전송 |

---

## 검증 완료 항목

- Docker Compose 기반 로컬 실행
- `/api/health/live`, `/api/health/ready` 응답 확인
- `healthcheck.sh` / `smoke_test.sh` / `deploy.sh` 실행 검증
- Oracle Cloud VM(Ubuntu 22.04) 공인 IP 기반 외부 접속 확인
- ufw + Oracle Security List 이중 방화벽 설정
- SSH 패스워드 로그인 비활성화, 키 인증 전용 설정
- Let's Encrypt HTTPS 인증서 발급 및 외부 브라우저 접속 확인
- certbot 자동 갱신 cron 등록
- Nginx를 통한 HTTP → HTTPS 리다이렉트 확인
- HAProxy 로드밸런서 트래픽 분산 확인
- HAProxy 헬스체크 기반 자동 페일오버 확인
- WireGuard VPN 서버 기동 및 peer 연결 확인
- Prometheus 메트릭 수집 확인 (`/metrics`, node-exporter)
- Grafana 대시보드 접속 및 datasource 자동 등록 확인
- Alertmanager 알림 규칙 로드 확인
- DB 백업 스크립트 실행 및 무결성 검증 확인
- 백업 파일 기반 복구 절차 확인

---

## 개발하면서 신경 쓴 점

### 1. 시간 경과를 반영하는 상태 모델
버튼을 누를 때만 값이 바뀌는 방식이 아니라, 조회 시점 기준으로 경과 시간을 계산해
`hunger`, `cleanliness`, `happiness`, `energy`, `health`에 반영하도록 만들었습니다.

### 2. 조회와 변경을 분리한 API 구조
펫 상태 조회와 액션 수행 API를 분리했습니다.
조회는 상태 확인, 액션은 상태 변경 역할만 맡도록 나눠 UI와 서버 로직을 각각 다루기 쉽게 구성했습니다.

### 3. Redis 기반 캐시와 반복 액션 제어
상태 조회 API에는 Redis TTL 캐시를 적용하고, 액션 발생 시 캐시를 무효화하도록 구성했습니다.
동일 액션이 짧은 시간 안에 반복 호출될 경우를 Redis 기반 rate limiting으로 제어했습니다.

### 4. L4 로드밸런서 기반 가용성 구성
HAProxy를 통해 backend 컨테이너 2대로 트래픽을 분산하고,
헬스체크 실패 시 자동으로 해당 서버를 제외하도록 구성했습니다.
서버 복구 후에는 재시작 없이 자동으로 트래픽이 복귀됩니다.

### 5. VPN 서버 직접 구성
WireGuard VPN 서버를 Oracle Cloud VM에 직접 구성하고,
peer 추가 / 제거 / 상태 확인을 스크립트로 자동화했습니다.
실행 중인 인터페이스에 재시작 없이 peer를 핫 적용할 수 있도록 구성했습니다.

### 6. 서버 리소스 및 서비스 지표 통합 모니터링
node-exporter로 서버 CPU / 메모리 / 디스크를 수집하고,
FastAPI에 prometheus-fastapi-instrumentator를 연동해 API 응답시간과 에러율을 별도로 계측했습니다.
Alertmanager로 주요 임계치 초과 시 알림이 발송되도록 구성했습니다.

### 7. 백업 정책 및 복구 절차 구성
pg_dump 기반 전체 백업을 자동화하고, gzip 무결성 검증과 보존 기간 관리를 스크립트로 처리했습니다.
단순히 백업 파일을 만드는 것에서 나아가 복구 절차까지 RUNBOOK에 정리해 실제 장애 상황에서
사용할 수 있는 형태로 구성했습니다.

### 8. 헬스 체크와 로그 기반 점검 포인트 추가
`/api/health/live`, `/api/health/ready`를 분리하고,
`/ready`에서는 DB 및 Redis 상태를 함께 확인할 수 있도록 구성했습니다.
요청마다 request id와 처리 시간을 로그로 남겨, 실행 중인 서비스 상태를 빠르게 점검할 수 있게 했습니다.

### 9. 운영 환경 수준의 서버 보안 구성
Oracle Cloud VM에 배포하면서 방화벽 이중 구성(ufw + Oracle Security List),
SSH 키 인증 전용 설정, HTTPS 인증서 적용까지 운영 환경에서 실제로 신경 쓰는 보안 요소들을 직접 구성했습니다.

---

## 아키텍처

```text
[ React Frontend ]
        |
        v
[ HAProxy ] ← L4 로드밸런서
    |              |
    v              v
[ FastAPI ]   [ FastAPI ]  ← backend / backend2
   |    |
   v    v
[PostgreSQL] [Redis]
```

---

## 테스트 및 자동화

- `pytest` 기반 backend 테스트
- GitHub Actions backend CI 구성
- Bash 기반 운영 스크립트

---

## 문서화 및 협업 도구

작업 단위 분리와 스프린트 관리는 Jira로 정리하고 있습니다.
실행 절차, 상태 점검, 장애 대응 포인트는 `RUNBOOK.md`에 기록해두고 있습니다.