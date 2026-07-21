# 성능 테스트

## 목적

상태 조회와 케어 액션이 동시에 발생할 때 API 지연시간, 오류율, 데이터베이스 부하와 캐시 동작을 확인합니다. 각 가상 사용자는 테스트 시작 시 게스트 사용자와 펫을 생성하고 부화시킨 뒤 상태 조회와 케어 액션을 반복합니다.

## 실행 방법

서비스를 먼저 기동한 뒤 별도 가상환경에서 Locust를 실행합니다.

```bash
python -m venv .venv-loadtest
source .venv-loadtest/bin/activate
pip install -r loadtest/requirements.txt

locust -f loadtest/locustfile.py \
  --host http://localhost \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --csv loadtest/results/latest
```

`loadtest/results/`에 생성되는 CSV는 테스트 일시와 커밋 SHA를 포함한 디렉터리로 옮겨 보관합니다. 개선 전후 비교 시 사용자 수, spawn rate, 실행 시간, 서버 사양과 데이터 초기 상태를 동일하게 유지합니다.

## 확인 지표

| 구분 | 지표 |
|---|---|
| API | RPS, 실패율, P50, P95, P99 응답시간 |
| 서버 | CPU, 메모리, 디스크 사용률 |
| 애플리케이션 | HTTP 5xx 비율, 요청 처리시간 |
| 데이터 계층 | PostgreSQL 연결 수와 쿼리 부하, Redis 캐시 동작 |
| 가용성 | HAProxy 주 서버 상태와 대기 서버 전환 여부 |

## 기존 장애 분석 기록

기존 테스트에서 액션 직후 캐시를 삭제하던 구현은 후속 상태 조회가 동시에 캐시 미스를 일으켜 PostgreSQL 부하를 증가시켰습니다. 캐시 삭제 대신 DB 커밋 직후 최신 상태를 저장하는 Write-Through 방식으로 변경했습니다. 코드 변경은 `Cache Stampede Error fix` 커밋에서 확인할 수 있습니다.

README에 기록된 기존 측정값은 P99 3.5초에서 0.12초로의 감소입니다. 이후 비교 테스트에서는 위 실행 조건과 CSV 결과를 함께 보관하여 수치의 재현 가능성을 확보합니다.
