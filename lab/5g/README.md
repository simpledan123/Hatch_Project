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
