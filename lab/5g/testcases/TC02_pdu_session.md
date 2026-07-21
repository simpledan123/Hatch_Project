# TC-02 PDU Session Establishment

## 목적

등록된 UE가 `internet` DNN에 대한 IPv4 PDU Session을 생성하고 사용자 평면 주소를 할당받는지 검증한다.

## 절차

1. UE 등록 완료 후 `ip address show uesimtun0`을 실행한다.
2. SMF와 UPF 로그에서 PFCP Session Establishment를 확인한다.
3. Wireshark에서 `nas-5gs || pfcp || gtp` 필터를 적용한다.

## 통과 기준

- UE 컨테이너에 `uesimtun0` 인터페이스가 생성된다.
- `10.45.0.0/16` 범위의 UE 주소가 할당된다.
- SMF와 UPF 사이 PFCP Session이 생성된다.

## 증거

- `ip -brief address show uesimtun0` 출력
- SMF/UPF 원본 로그
- PDU Session 및 PFCP 메시지 PCAP
