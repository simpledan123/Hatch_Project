# TC-04 Subscriber Authentication Failure

## 목적

UE와 가입자 DB의 인증 키가 불일치할 때 등록 실패가 재현되고, 실패 지점을 NAS 및 로그에서 식별할 수 있는지 검증한다.

## 안전한 수행 방법

1. 정상 PCAP과 시험 결과를 먼저 보관한다.
2. `config/ueransim/ue.yaml`의 실습용 `key` 마지막 한 바이트만 임시 변경한다.
3. `docker compose ... restart ue`로 UE만 재시작한다.
4. AMF/AUSF/UDM/UE 로그와 `nas-5gs` 패킷을 수집한다.
5. 시험 후 원래 키로 복구하고 TC-01을 다시 실행한다.

## 통과 기준

- UE 등록이 성공하지 않아야 한다.
- 인증 실패에 대응하는 NAS 메시지와 코어 로그가 같은 시각대에 존재해야 한다.
- 설정 복구 후 정상 등록이 다시 성공해야 한다.

## 주의

실제 운영 가입자 정보나 USIM 키를 사용하지 않는다. 이 Lab의 값은 공개 가능한 실습 전용 값이다.
