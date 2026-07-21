# TC-01 UE Registration

## 목적

UERANSIM gNB가 AMF와 NGAP 연결을 수립하고, 시험용 UE가 5G Core에 정상 등록되는지 검증한다.

## 사전 조건

- MCC/MNC: `001/01`
- TAC: `1`
- SUPI: `imsi-001011234567891`
- MongoDB에 동일 IMSI와 인증 키가 등록되어 있어야 한다.

## 절차

1. `scripts/start_lab.sh`를 실행한다.
2. AMF, gNB, UE 로그를 수집한다.
3. Wireshark에서 `sctp || ngap || nas-5gs` 표시 필터를 적용한다.
4. Registration Request와 Registration Accept 흐름을 확인한다.

## 통과 기준

- gNB와 AMF 사이 SCTP 연결이 성립한다.
- UE가 Registration Accept를 수신한다.
- AMF 로그에 동일 SUPI의 등록 성공 정보가 존재한다.

## 증거

- AMF/gNB/UE 원본 로그
- 등록 구간 PCAP
- 메시지 번호와 시각을 표시한 Wireshark 화면
