# hatch_project

> 작은 상태 저장형 웹 서비스를 예시로 운영 자동화와 배포 흐름을 보강하는 프로젝트

`hatch_project`는 브라우저에서 펫을 생성하고 돌보는 다마고치 스타일의 웹 게임을 소재로 삼아, 상태 저장형 웹 서비스의 구현과 운영 보강을 함께 다뤄보는 프로젝트입니다.  
단순히 화면에서 버튼을 누르는 데모가 아니라, 펫의 상태를 서버와 데이터베이스에 저장하고, 시간이 지남에 따라 상태가 실제로 변화하도록 구성했습니다.

이 프로젝트의 목적은 작은 서비스를 대상으로 **실행 환경 통일, 상태 확인, 자동 검증, 배포 흐름, 운영 문서화**를 직접 정리해보는 데 있습니다.  

로컬 Docker Compose 환경과 WSL Ubuntu 환경에서 먼저 실행 및 점검 흐름을 검증한 뒤, 원격 Ubuntu 서버에도 실제로 배포해 서비스 기동, health check, smoke test, 배포 스크립트 동작까지 확인했습니다.

## 프로젝트 목표

- 상태 저장형 웹 서비스 설계
- Docker Compose 기반 실행 환경 정리
- health check / smoke test / deploy script 작성
- WSL Ubuntu 기반 Linux 실행 경험 축적
- 원격 Ubuntu 서버 배포 경험 추가
- Jira 기반 작업 관리
- Runbook 중심의 운영 문서화
- 이후 CI/CD와 관측성 보강

즉, 이 프로젝트는 **기능 중심 웹앱을 하나 더 만드는 것**이 아니라, **작은 서비스를 대상으로 운영과 배포 흐름을 다뤄보는 실험 프로젝트**입니다.

## 프로젝트 소개

플레이어는 먼저 게스트 사용자를 만들고, 자신의 펫을 생성한 뒤 상태를 확인할 수 있습니다.  
이후 `feed`, `clean`, `play`, `sleep` 액션을 수행하면서 배고픔, 청결도, 행복도, 에너지, 건강 수치를 관리하게 됩니다.

시간이 지나면 상태가 계속 변화하며, 상태에 따라 `alive`, `sick`, `dead`로 구분됩니다.  
단순 CRUD 형태를 넘어서, **시간 경과에 따라 상태가 달라지는 작은 웹 서비스**를 구현하는 데 초점을 두었습니다.

## 현재 구현 기능

- 게스트 사용자 생성
- 펫 생성
- 펫 상태 조회
- `feed / clean / play / sleep` 액션
- 시간 경과에 따른 상태 변화
- 위험 상태(`sick`) 및 사망 상태(`dead`) 반영
- 액션 로그 저장
- Redis 기반 상태 조회 캐시
- Redis 기반 반복 액션 제어(rate limiting)
- `/api/health/live`, `/api/health/ready` 헬스 체크 엔드포인트
- request id 및 요청 처리 시간 로그

## 운영 보강 항목

이 프로젝트에서는 기능 구현 외에도 아래와 같은 운영 보강 요소를 추가했습니다.

- Docker Compose 기반 실행 환경 통일
- WSL Ubuntu 환경에서 컨테이너 기동 및 상태 확인
- 원격 Ubuntu 서버에 실제 배포
- Bash 기반 `healthcheck.sh`
- Bash 기반 `smoke_test.sh`
- Bash 기반 `deploy.sh`
- Bash 기반 `remote_deploy.sh`
- 배포용 `docker-compose.prod.yml` 분리
- Nginx 기반 프론트 정적 서빙 구성
- `RUNBOOK.md`를 통한 실행/점검/장애 대응 절차 정리

## 기술 스택

### Frontend
- React
- Vite

### Backend
- Python
- FastAPI
- SQLAlchemy

### Data
- PostgreSQL
- Redis

### Environment / Tooling
- Docker
- Docker Compose
- Bash
- Nginx
- pytest
- GitHub Actions
- Jira
- WSL Ubuntu
- Ubuntu Server

## 개발하면서 신경 쓴 점

### 1. 시간 경과를 반영하는 상태 모델
버튼을 누를 때만 값이 바뀌는 방식이 아니라, 조회 시점 기준으로 경과 시간을 계산해 `hunger`, `cleanliness`, `happiness`, `energy`, `health`에 반영하도록 만들었습니다.  
작은 게임이지만 상태가 실제로 계속 변하는 서비스 구조를 만드는 데 의미를 두었습니다.

### 2. 조회와 변경을 분리한 API 구조
펫 상태 조회와 액션 수행 API를 분리했습니다.  
조회는 상태 확인, 액션은 상태 변경 역할만 맡도록 나눠 UI와 서버 로직을 각각 다루기 쉽게 구성했습니다.

### 3. Redis 기반 캐시와 반복 액션 제어
상태 조회 API에는 Redis TTL 캐시를 적용하고, 액션 발생 시 캐시를 무효화하도록 구성했습니다.  
또 동일 액션이 짧은 시간 안에 반복 호출될 경우를 제어하기 위해 Redis 기반 rate limiting을 추가했습니다.

### 4. 헬스 체크와 로그 기반 점검 포인트 추가
`/api/health/live`, `/api/health/ready`를 분리하고, `/ready`에서는 DB 및 Redis 상태를 함께 확인할 수 있도록 구성했습니다.  
또 요청마다 request id와 처리 시간을 로그로 남겨, 실행 중인 서비스 상태를 빠르게 점검할 수 있게 했습니다.

### 5. 실행 환경과 검증 흐름 정리
로컬 실행은 Docker Compose로 통일했고, 별도의 Bash 스크립트로 상태 확인과 핵심 기능 검증 흐름을 자동화했습니다.  
단순히 “한 번 실행된다”가 아니라, **기동 → 상태 확인 → 핵심 기능 검증** 흐름을 반복 가능한 형태로 정리하는 데 초점을 두었습니다.

## 아키텍처

```text
[ React Frontend ]
        |
        v
[ FastAPI Backend ]
   |            |
   v            v
[PostgreSQL]  [Redis]
```

- Frontend는 플레이어 입력과 상태 표시를 담당합니다.
- Backend는 펫 상태 계산, 액션 처리, API 응답을 담당합니다.
- PostgreSQL은 사용자, 펫, 액션 로그 같은 상태 데이터를 저장합니다.
- Redis는 상태 조회 캐시와 반복 액션 제어에 사용합니다.

## 배포 구조

production 배포에서는 프론트엔드를 Nginx로 정적 서빙하고, `/api` 요청은 backend 컨테이너로 프록시되도록 구성했습니다.

```text
[ Browser ]
    |
    v
[ Nginx Frontend ]
    |
    +--> /api -> [ FastAPI Backend ] -> [ PostgreSQL ]
                              |
                              +-> [ Redis ]
```

배포용 설정은 아래 파일들을 기준으로 분리했습니다.

- `frontend/Dockerfile.prod`
- `frontend/nginx.conf`
- `docker-compose.prod.yml`
- `.env.prod`
- `scripts/remote_deploy.sh`

## 실행 방법

### 1. 환경 변수 파일 생성
```bash
cp .env.example .env
```

Windows PowerShell에서는 아래 명령을 사용할 수 있습니다.

```powershell
Copy-Item .env.example .env
```

### 2. Docker Compose 실행
```bash
docker compose up --build
```

### 3. 접속 주소
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## 운영 스크립트

프로젝트 루트의 `scripts/` 폴더에 아래 스크립트를 두고 운영 흐름을 보강했습니다.

- `healthcheck.sh`
  - `live / ready` 엔드포인트를 호출해 서비스 상태를 확인
- `smoke_test.sh`
  - guest 생성 → 펫 생성 → 상태 조회 → 액션 수행까지 핵심 흐름 검증
- `deploy.sh`
  - 컨테이너 실행 후 health check, smoke test까지 포함한 배포 흐름 재현
- `remote_deploy.sh`
  - production compose를 기준으로 원격 Ubuntu 서버에서 배포 흐름 실행

실행 예시는 다음과 같습니다.

```bash
chmod +x scripts/*.sh
./scripts/healthcheck.sh
./scripts/smoke_test.sh
./scripts/deploy.sh
```

## Production 배포 방법

### 1. 배포용 환경 변수 파일 생성
```bash
cp .env.prod.example .env.prod
```

### 2. 배포 스크립트 실행
```bash
chmod +x scripts/*.sh
./scripts/remote_deploy.sh
```

### 3. 주요 확인 포인트
- Frontend 접속 확인
- `/api/health/live` 응답 확인
- `/api/health/ready` 응답 확인
- `docker compose -f docker-compose.prod.yml logs` 로 로그 확인

## 검증한 내용

현재까지 아래 항목을 직접 확인했습니다.

- Docker Compose 기반 로컬 실행
- WSL Ubuntu 환경에서 컨테이너 기동
- `/api/health/live`, `/api/health/ready` 응답 확인
- `/ready` 기준 DB / Redis 정상 연결 확인
- `healthcheck.sh` 실행 검증
- `smoke_test.sh`를 통한 핵심 API 흐름 검증
- `deploy.sh`를 통한 배포 흐름 재현
- 원격 Ubuntu 서버에 production 구성으로 실제 배포
- 원격 서버에서 서비스 기동 후 health check 및 로그 확인
- Nginx를 통한 프론트 정적 서빙 및 `/api` 프록시 구성 확인

즉, 단순 구현을 넘어서 **Linux 셸 환경과 원격 Ubuntu 서버에서 서비스 기동과 점검, 배포 흐름을 실제로 검증**한 상태입니다.

## 테스트 및 자동화

- `pytest` 기반 backend 테스트
- GitHub Actions backend CI 초안 구성
- Bash 기반 운영 스크립트 추가

현재는 백엔드 기초 테스트와 운영 스크립트 중심으로 검증 흐름을 만들고 있으며, 이후 배포 자동화와 원격 서버 기준 검증으로 확장하고 있습니다.

## 문서화 및 협업 도구

작업 단위 분리와 스프린트 관리는 Jira로 정리하고 있습니다.  
또 실행 절차, 상태 점검, 장애 대응 포인트는 `RUNBOOK.md`에 기록해두고 있으며, 이후 Confluence 형태 문서화로 확장할 계획입니다.

## 현재 단계와 다음 단계

### 현재까지 완료
- 게임 MVP 구현
- Redis 캐시 / 반복 액션 제어 추가
- health check 및 request logging 추가
- Docker Compose 기반 로컬 실행 정리
- WSL Ubuntu 환경 실행 검증
- healthcheck / smoke test / deploy script 추가
- Runbook 초안 작성
- 원격 Ubuntu 서버 배포 검증

### 다음 단계
- 배포 후 자동 헬스체크 및 롤백 전략 정리
- 운영 로그 및 모니터링 보강
- 운영 문서 보강
- 이후 게임성 확장(이벤트, 성장/진화, UI 개선)
