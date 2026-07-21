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
- Redis 기반 상태 조회 캐시 (TTL 30초, Write-Through 갱신)
- Redis 기반 반복 액션 rate limiting

### 인프라 / 운영
- Docker Compose 기본 구성과 운영용 override 구성 분리
- Oracle Cloud VM(Ubuntu 22.04) 배포, 공인 IP 외부 접속
- HAProxy L7 HTTP 프록시 (주 서버 + 대기 서버, HTTP 헬스체크 기반 자동 페일오버)
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
- GitHub Actions CI (backend pytest, frontend production build)
- RUNBOOK.md 운영 절차 문서화

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | React, Vite, Nginx |
| Backend | Python, FastAPI, SQLAlchemy |
| Database | PostgreSQL, Redis |
| Infrastructure | Docker / Docker Compose, Oracle Cloud VM |
| Traffic / Failover | Nginx, HAProxy (L7 HTTP, Active-Standby) |
| Monitoring | Prometheus, Grafana, Alertmanager, node-exporter |
| VPN | WireGuard |
| SSL | Let's Encrypt + certbot |
| CI | GitHub Actions, pytest, Vite production build |

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
[ HAProxy :80 ] ← L7 HTTP 프록시
    |              |
    v              v
[ FastAPI ]   [ FastAPI ]   ← primary / standby
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
docker compose --env-file .env up -d --build
```

접속 주소:
- Frontend: `http://localhost`
- Backend Swagger: `http://localhost:8000/docs`
- HAProxy Stats: `http://localhost:8404/stats`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

기본 구성은 로컬 확인을 위해 HTTP로 실행됩니다. 운영 환경에서는 `.env.prod`와 `docker-compose.prod.yml`을 함께 사용하여 HTTPS를 활성화합니다.

```bash
cp .env.prod.example .env.prod
sudo docker compose \
  --env-file .env.prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --build
```

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

## 테스트

백엔드 테스트는 SQLite 인메모리 데이터베이스를 사용하며 헬스 체크와 핵심 펫 액션 흐름을 검증합니다.

```bash
cd backend
pytest -q
```

배포 후에는 `healthcheck.sh`와 `smoke_test.sh`로 준비 상태와 사용자 생성 → 펫 생성 → 부화 → 케어 액션의 핵심 흐름을 확인합니다. Locust 성능 테스트의 시나리오와 실행 조건은 [`docs/PERFORMANCE_TEST.md`](docs/PERFORMANCE_TEST.md)에 정리했습니다.

---

## 개발하면서 신경 쓴 점

### 1. 시간 경과 기반 상태 모델
버튼을 누를 때만 값이 바뀌는 방식이 아니라, 조회 시점 기준으로 경과 시간을 계산해 배고픔, 청결, 에너지 등에 반영하도록 구성했습니다. 마지막 decay 시각을 기록하고 분 단위로 누적 처리합니다.

### 2. 케어 이력 기반 진화 결정
단순히 스탯 수치만 보는 것이 아니라, 성장 기간 동안 어떤 액션을 얼마나 수행했는지를 tally로 누적해 최종 진화형을 결정합니다. 같은 캐릭터라도 플레이 방식에 따라 다른 어른이 됩니다.

### 3. Redis 기반 캐시와 rate limiting
상태 조회 API에 TTL 30초 캐시를 적용합니다. 액션 발생 시 캐시를 삭제하지 않고 Write-Through 패턴으로 즉시 갱신하여 Cache Stampede를 방지합니다. 동일 액션 반복 호출은 Redis INCR 기반 rate limiting으로 제어했습니다. Redis 장애 시에도 서비스는 계속 동작합니다.

### 4. L7 HTTP 프록시 기반 가용성
Nginx의 `/api` 요청을 HAProxy로 전달하고, HAProxy가 주 백엔드의 `/api/health/live`를 3초마다 확인하도록 구성했습니다. 주 서버가 2회 연속 실패하면 대기 서버로 전환하고, 주 서버가 3회 연속 정상 응답하면 자동으로 복귀합니다.

### 5. 통합 모니터링
node-exporter로 서버 CPU / 메모리 / 디스크를 수집하고, prometheus-fastapi-instrumentator로 API 응답시간과 에러율을 계측합니다. Alertmanager로 주요 임계치 초과 시 알림이 발송됩니다.

### 6. 백업 및 복구 절차
pg_dump 전체 백업 자동화, gzip 무결성 검증, 보존 기간 관리를 스크립트로 처리했습니다. 단순 백업 파일 생성에 그치지 않고, 복구 절차까지 RUNBOOK.md에 정리했습니다.

---

## 트러블슈팅

### Cache Stampede — 기록된 P99 응답시간 3.5s → 0.12s

**문제**

Locust 부하 테스트 중 동시 펫 케어 액션이 집중되자 API P99 응답시간이 3.5초까지 치솟고, HAProxy 백엔드 헬스 체크가 끊어지며 서비스 전체가 다운되었다.

**원인 파악**

Alertmanager 레이턴시 알림을 시작점으로 Grafana 대시보드와 애플리케이션 로직을 분석한 결과, 액션 발생 시마다 캐시를 삭제(`invalidate_pet_cache`)하는 동작을 원인으로 좁혔습니다. 삭제 직후 다수의 요청이 동시에 캐시 미스를 일으켜 PostgreSQL에 부하가 집중되는 Cache Stampede가 발생하고 있었습니다.

**해결**

캐시 삭제 방식을 Write-Through 패턴으로 전환했습니다. DB 커밋 직후 캐시를 삭제하는 대신 최신 상태로 즉시 덮어씌워(`write_through_pet_cache`), 후속 조회 요청이 캐시 미스로 동시에 데이터베이스에 전달되는 상황을 줄였습니다.

기록된 테스트에서 P99 응답시간이 3.5s에서 0.12s로 감소했고 서비스 가용성이 복구되었습니다. 이후 동일 조건의 비교와 결과 보관을 위해 재현 가능한 Locust 시나리오와 측정 절차를 [`docs/PERFORMANCE_TEST.md`](docs/PERFORMANCE_TEST.md)에 추가했습니다.

```python
# Before: 액션 후 캐시 삭제 → Cache Stampede 발생
invalidate_pet_cache(pet_id)

# After: Write-Through — DB 커밋 직후 캐시를 최신 상태로 즉시 갱신
response = build_pet_state_response(pet, cached=False)
write_through_pet_cache(pet_id, response)
```

# Hatch 5G SA Protocol Validation Lab

Open5GS와 UERANSIM으로 구성한 독립형 5G SA 시험환경이다. 가상 UE 등록, PDU Session 생성, 사용자 평면을 통한 Hatch API 연결을 시험하고 Wireshark로 프로토콜 근거를 남기는 것이 목적이다.

이 Lab은 실제 RF 장비나 상용 스몰셀을 사용하지 않는다. UERANSIM의 가상 UE/gNB를 활용한 소프트웨어 기반 프로토콜 검증 환경이다.

## 검증 범위

| 구간 | 확인 항목 | 주요 프로토콜 |
|---|---|---|
| gNB ↔ AMF | SCTP 연결, NG Setup | SCTP, NGAP |
| UE ↔ 5G Core | 가입자 인증 및 등록 | NAS-5GS, NGAP |
| SMF ↔ UPF | PDU Session과 사용자 평면 생성 | PFCP, GTP-U |
| UE ↔ Hatch | 준비 상태 API 종단 간 연결 | GTP-U, TCP, TLS, HTTP |

## 구성

```text
UERANSIM UE
  └─ UERANSIM gNB
       ├─ N2/SCTP/NGAP ─ Open5GS AMF
       └─ N3/GTP-U ───── Open5GS UPF
                            └─ Hatch /api/health/ready
```

Open5GS Network Function은 NRF, AUSF, UDM, UDR, NSSF, BSF, PCF, AMF, SMF, UPF로 분리했다. MongoDB에는 공개 가능한 실습 전용 가입자만 등록한다.

## 실행 환경

- Linux Docker 호스트. Ubuntu 22.04 이상 권장
- Docker Engine과 Docker Compose V2
- `/dev/net/tun` 사용 가능
- SCTP와 TUN 커널 모듈
- 이미지 다운로드와 Hatch 공개 주소 접근을 위한 인터넷 연결
- 권장 여유 자원: 4 vCPU, RAM 8GB, 디스크 10GB 이상

운영 중인 Hatch 서버에 상시 실행하기보다 로컬 Linux 또는 별도 시험 VM에서 필요할 때만 실행한다.

## 빠른 시작

```bash
cd lab/5g
cp .env.example .env
```

`.env`의 `HATCH_HEALTH_URL`을 실제 준비 상태 주소로 변경한다.

```dotenv
HATCH_HEALTH_URL=https://your-domain.example/api/health/ready
```

호스트 조건을 확인하고 Lab을 시작한다.

```bash
sudo modprobe tun
sudo modprobe sctp
./scripts/start_lab.sh
```

성공하면 UE 컨테이너에 `uesimtun0`과 `10.45.0.0/16` 범위 주소가 나타난다.

## 시험 실행

```bash
./scripts/run_test.sh
```

실행 결과는 `evidence/test-result-*.md`에 생성된다. 결과 파일은 명령 실행 당시의 실제 출력만 기록한다.

패킷을 캡처하려면 다음을 실행한다.

```bash
./scripts/capture_packets.sh 30
```

캡처 시작 후 UE를 재시작하여 등록 절차를 다시 발생시킨다. 생성 파일은 `evidence/registration-*.pcap`이다.

Wireshark 표시 필터 예시:

```text
sctp || ngap || nas-5gs || pfcp || gtp
```

## 가입자 재등록

MongoDB 볼륨이 이미 생성된 상태에서 가입자 문서를 다시 적용하려면 다음을 실행한다.

```bash
./scripts/register_subscriber.sh
```

스크립트는 IMSI 기준 upsert를 사용하므로 반복 실행해도 동일 가입자가 중복 생성되지 않는다.

## 종료

```bash
./scripts/stop_lab.sh
```

기본 종료는 MongoDB 볼륨을 보존한다. 가입자 데이터까지 제거하려는 경우에만 명시적으로 실행한다.

```bash
./scripts/stop_lab.sh --purge
```

## 시험 문서

- [TC-01 UE Registration](testcases/TC01_registration.md)
- [TC-02 PDU Session Establishment](testcases/TC02_pdu_session.md)
- [TC-03 Hatch API End-to-End Connectivity](testcases/TC03_hatch_connectivity.md)
- [TC-04 Subscriber Authentication Failure](testcases/TC04_registration_failure.md)

## 문제 확인 순서

### `uesimtun0`이 생성되지 않는 경우

```bash
docker compose --env-file .env -f docker-compose.5g.yml logs --tail=150 amf smf gnb ue
```

다음 순서로 비교한다.

1. UE와 MongoDB의 IMSI, K, OPc가 같은가
2. MCC/MNC, TAC, S-NSSAI가 AMF/gNB/UE에서 같은가
3. DNN이 모두 `internet`인가
4. gNB-AMF 사이 SCTP/NGAP 연결이 성립했는가
5. SMF-UPF 사이 PFCP 연결이 성립했는가

### UE 등록은 성공했지만 Hatch에 접속하지 못하는 경우

```bash
docker compose --env-file .env -f docker-compose.5g.yml exec ue ip route
docker compose --env-file .env -f docker-compose.5g.yml logs --tail=150 smf upf ue
```

UE 터널 주소, UPF NAT/포워딩, DNS, 목적지 방화벽, Hatch HTTPS 상태를 순서대로 확인한다.

## 증거 작성 원칙

- 성공 결과를 실행 전에 작성하지 않는다.
- 정상과 실패 PCAP을 동일 조건에서 비교한다.
- 포트폴리오에는 실제 실행 시각, 명령, 결과, 원본 파일 경로를 함께 표기한다.
- 실제 기지국 경험으로 표현하지 않고 `가상 UE/gNB 기반 5G SA 프로토콜 검증`으로 표현한다.
