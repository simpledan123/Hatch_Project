# TC-03 Hatch API End-to-End Connectivity

## 목적

가상 UE의 PDU Session을 통해 실제 배포된 Hatch API까지 종단 간 통신이 가능한지 확인한다.

## 사전 조건

- `.env`의 `HATCH_HEALTH_URL`이 실제 `/api/health/ready` 주소여야 한다.
- TC-01과 TC-02가 통과해야 한다.

## 절차

1. `scripts/run_test.sh`를 실행한다.
2. tester 컨테이너가 `uesimtun0`에 바인딩하여 HTTPS 요청을 전송한다.
3. 생성된 `evidence/test-result-*.md`를 확인한다.

## 통과 기준

- curl 프로세스가 `uesimtun0` 인터페이스를 사용한다.
- Hatch 준비 상태 엔드포인트가 HTTP 2xx로 응답한다.
- 응답 본문이 자동 생성 시험 결과에 보존된다.

## 증거

- 자동 생성된 시험 결과 Markdown
- GTP-U와 Hatch 목적지 트래픽 PCAP
- Hatch 서버의 동일 시각 request ID 로그
