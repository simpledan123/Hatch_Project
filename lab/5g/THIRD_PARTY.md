# Third-party Components

이 Lab은 다음 오픈소스 프로젝트와 컨테이너 이미지를 실행 시점에 사용한다. 소스 코드는 이 디렉터리에 복제하지 않았다.

| 구성요소 | 용도 | 위치 |
|---|---|---|
| Open5GS | 5G Core Network Functions | https://github.com/open5gs/open5gs |
| UERANSIM | 가상 5G UE 및 gNB | https://github.com/aligungr/UERANSIM |
| Borjis131 Docker images | Open5GS/UERANSIM 컨테이너 패키징 | https://github.com/Borjis131/docker-open5gs |
| MongoDB Community | Open5GS 가입자 DB | https://www.mongodb.com/try/download/community |
| Netshoot | 격리된 네트워크 네임스페이스 패킷 캡처 | https://github.com/nicolaka/netshoot |
| curl container | UE 인터페이스 바인딩 HTTP 시험 | https://github.com/curl/curl-container |

각 구성요소의 저작권과 라이선스는 해당 프로젝트에 귀속된다. 이미지 버전은 `.env.example`과 `docker-compose.5g.yml`에 고정했다.
