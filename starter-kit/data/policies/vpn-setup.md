---
title: VPN 설정 가이드
tags: [vpn, 네트워크, 원격접속, 보안]
last_updated: 2026-01-15
author: IT보안팀
---

# VPN 설정 가이드

**최종 수정일:** 2026년 1월 15일
**담당팀:** IT보안팀
**지원 채널:** Slack #vpn-지원 또는 security@metacode.co.kr

---

## 1. 개요

메타코드 임직원은 사내 네트워크 외부에서 내부 시스템에 접속할 때 반드시 회사 VPN에 연결해야 합니다. 회사 VPN에 접속하려면 다음이 필요합니다:

- 메타코드 Okta 계정 (입사 시 발급)
- MFA 인증 수단 (Okta Verify 앱 또는 하드웨어 키)
- 회사에서 제공하는 VPN 설정 파일
- 승인된 VPN 클라이언트 (아래 참조)

VPN을 통해 Jira, Confluence, 내부 대시보드, 스테이징 환경, 사내 인트라넷 등 내부 리소스에 안전하게 접근할 수 있습니다.

---

## 2. 지원 VPN 클라이언트

| 우선순위 | 클라이언트 | 지원 플랫폼 | 비고 |
|---|---|---|---|
| **권장** | WireGuard | macOS, Windows, Linux, iOS, Android | 최고 성능, 배터리 소모 최소 |
| **대체** | OpenVPN (Tunnelblick/OpenVPN Connect) | macOS, Windows, Linux, iOS, Android | ISP에서 WireGuard 차단 시 사용 |

**중요:** 반드시 메타코드에서 제공하는 설정 파일만 사용하세요. 개인 VPN 서비스로 사내 시스템에 접속하는 것은 금지됩니다.

---

## 3. 설치 방법

### 3.1. macOS (WireGuard - 권장)

1. Mac App Store 또는 Homebrew를 통해 WireGuard를 설치합니다:
   ```
   brew install wireguard-tools
   ```
2. IT 셀프서비스 포탈(https://itportal.metacode.co.kr/vpn)에서 개인 설정 파일을 다운로드합니다.
   - Okta 계정으로 로그인
   - **VPN > 설정 파일 다운로드 > WireGuard** 선택
   - 파일명: `metacode-wg-{사번}.conf`
3. WireGuard를 실행하고 **Import Tunnel(s) from File**을 클릭합니다.
4. 다운로드한 `.conf` 파일을 선택합니다.
5. 터널을 **ON**으로 전환하여 연결합니다.
6. https://intranet.metacode.co.kr 에 접속하여 인트라넷 메인 페이지가 표시되는지 확인합니다.

### 3.2. macOS (OpenVPN - 대체)

1. Tunnelblick을 https://tunnelblick.net 또는 Homebrew를 통해 설치합니다:
   ```
   brew install --cask tunnelblick
   ```
2. IT 셀프서비스 포탈에서 OpenVPN 설정 파일을 다운로드합니다.
   - **VPN > 설정 파일 다운로드 > OpenVPN** 선택
   - 파일명: `metacode-ovpn-{사번}.ovpn`
3. `.ovpn` 파일을 더블클릭하여 Tunnelblick에 가져옵니다.
4. 메뉴 바의 Tunnelblick 아이콘을 클릭하고 **Connect metacode-ovpn**을 선택합니다.
5. Okta 자격증명을 입력하고 MFA 푸시 알림을 승인합니다.

### 3.3. Windows

1. https://www.wireguard.com/install/ 에서 WireGuard를 다운로드하여 설치합니다.
2. IT 셀프서비스 포탈에서 설정 파일을 다운로드합니다.
3. WireGuard를 실행하고 **Add Tunnel**을 클릭한 후 `.conf` 파일을 선택합니다.
4. **Activate**를 클릭하여 연결합니다.
5. https://intranet.metacode.co.kr 에 접속하여 연결을 확인합니다.

OpenVPN 대체 방법:
1. https://openvpn.net/client/ 에서 OpenVPN Connect를 다운로드합니다.
2. `.ovpn` 파일을 가져온 후 Okta 자격증명 + MFA로 연결합니다.

### 3.4. Linux

1. WireGuard를 설치합니다:
   ```
   # Ubuntu/Debian
   sudo apt install wireguard

   # Fedora
   sudo dnf install wireguard-tools

   # Arch
   sudo pacman -S wireguard-tools
   ```
2. 설정 파일을 `/etc/wireguard/metacode-wg0.conf`에 복사합니다.
3. 터널을 시작합니다:
   ```
   sudo wg-quick up metacode-wg0
   ```
4. 부팅 시 자동 시작 설정:
   ```
   sudo systemctl enable wg-quick@metacode-wg0
   ```
5. `curl -s https://intranet.metacode.co.kr | head -5`로 연결을 확인합니다.

### 3.5. iOS

1. App Store에서 WireGuard를 설치합니다.
2. iPhone/iPad에서 Safari를 열고 IT 셀프서비스 포탈에 접속합니다.
3. WireGuard 설정 파일을 다운로드합니다. iOS가 WireGuard 앱으로 열기를 자동으로 제안합니다.
4. VPN 구성 설치를 승인합니다.
5. WireGuard 앱 또는 설정 > VPN에서 터널을 활성화합니다.

### 3.6. Android

1. Google Play Store에서 WireGuard를 설치합니다.
2. IT 셀프서비스 포탈에서 설정 파일을 다운로드합니다.
3. WireGuard를 열고 **+**를 탭한 후 **파일 또는 아카이브에서 가져오기**를 선택합니다.
4. 다운로드한 파일을 선택하고 터널을 활성화합니다.

---

## 4. 스플릿 터널링 정책

4.1. **기본 설정:** 메타코드 VPN은 기본적으로 **스플릿 터널링**을 사용합니다:
   - 메타코드 내부 네트워크(10.0.0.0/8, 172.16.0.0/12)로 향하는 트래픽만 VPN을 통해 라우팅됩니다.
   - 그 외 인터넷 트래픽(웹 브라우징, 스트리밍, 개인 앱)은 로컬 인터넷 연결을 직접 사용합니다.

4.2. **풀 터널 모드:** 기밀 또는 제한 등급 데이터를 다루는 임직원은 풀 터널 모드를 사용해야 합니다. IT보안팀에 연락하여 풀 터널 설정 파일을 발급받으세요.

4.3. **DNS:** DNS 유출 방지 및 내부 호스트명(*.metacode.internal) 접근을 위해 모든 DNS 쿼리는 VPN을 통해 라우팅됩니다.

---

## 5. 자동 연결 규칙

5.1. **온디맨드 연결:** 내부 도메인 접속 시 자동으로 VPN에 연결되도록 클라이언트를 설정하세요. WireGuard는 온디맨드 활성화 규칙을 지원합니다.

5.2. **신뢰 네트워크:** 메타코드 사무실 Wi-Fi(SSID: `MetaCode-Secure` 또는 `MetaCode-Dev`)에 연결된 경우 VPN이 필요하지 않습니다. 신뢰 네트워크에서는 VPN 클라이언트가 자동으로 연결을 해제하도록 설정하세요.

5.3. **비신뢰 네트워크:** 신뢰 목록에 없는 네트워크에 접속하면 VPN이 자동으로 연결되어야 합니다. 호텔, 공항, 카페 Wi-Fi 사용 시 특히 중요합니다.

---

## 6. 문제 해결

### 6.1. 연결 불가

- **자격증명 확인:** Okta 계정이 잠기지 않았는지 확인합니다. https://metacode.okta.com 에서 로그인을 시도하세요.
- **MFA 확인:** MFA 인증 장치가 사용 가능하고 배터리가 충분한지 확인합니다.
- **클라이언트 재시작:** WireGuard 또는 Tunnelblick을 완전히 종료하고 다시 실행합니다.
- **인터넷 연결 확인:** VPN 없이 인터넷 연결이 정상인지 확인합니다.
- **방화벽/ISP 차단:** 일부 네트워크에서 WireGuard(UDP 51820)를 차단합니다. OpenVPN(TCP 443)으로 대체 접속을 시도하세요.

### 6.2. 연결이 자주 끊김

- **프로토콜 전환:** WireGuard가 불안정하면 OpenVPN TCP 모드를 사용해보세요.
- **Wi-Fi 간섭:** 공유기에 가까이 이동하거나 유선(이더넷) 연결로 전환하세요.
- **MTU 문제:** WireGuard 설정에서 MTU를 낮춰보세요:
  ```
  [Interface]
  MTU = 1280
  ```
- **절전 모드:** OS의 Wi-Fi 절전 기능을 비활성화하세요. macOS에서는 시스템 설정 > Wi-Fi에서 해당 네트워크의 "저데이터 모드"를 해제합니다.
- **Keep-alive:** 설정 파일에 PersistentKeepalive가 설정되어 있는지 확인합니다 (기본값: 25초).

### 6.3. 속도 저하

- **라우팅 확인:** 스플릿 터널링이 활성화되어 있는지 확인합니다. 풀 터널 모드는 모든 트래픽을 VPN으로 라우팅하여 속도가 느려집니다.
- **서버 선택:** VPN은 자동으로 가장 가까운 서버를 선택합니다. 성능이 저하되면 IT보안팀에 서버 부하 확인을 요청하세요.
- **대역폭 측정:** https://speedtest.metacode.co.kr 에서 VPN 사용 시와 미사용 시 속도를 각각 측정합니다. VPN 속도가 기본 속도의 50% 미만이면 IT보안팀에 결과를 보고하세요.

### 6.4. 내부 사이트 접속 불가

- **DNS 캐시 초기화:**
  ```
  # macOS
  sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder

  # Windows
  ipconfig /flushdns

  # Linux
  sudo systemd-resolve --flush-caches
  ```
- **VPN 상태 확인:** VPN 터널이 활성화되어 있고 할당된 IP(10.x.x.x 대역)가 있는지 확인합니다.
- **브라우저 캐시:** 시크릿/프라이빗 윈도우에서 사이트 접속을 시도합니다.

---

## 7. 알려진 이슈

| 이슈 | 상태 | 임시 해결 방법 |
|---|---|---|
| macOS Sequoia에서 절전 모드 복귀 후 WireGuard 연결 해제 | 조사 중 | 절전 복귀 후 터널을 껐다 다시 켜기 |
| Windows 11 24H2에서 OpenVPN 속도 저하 | 패치 예정 | WireGuard 사용 권장 |
| iOS 셀룰러 환경에서 WireGuard 배터리 소모 증가 | 설계상 동작 | 내부 리소스 미사용 시 VPN 연결 해제 |
| 일부 Linux 배포판에서 스플릿 터널 DNS 유출 | 문서화 완료 | `resolvconf` 또는 `systemd-resolved` 연동 사용 |

---

## 8. 긴급 접속

8.1. **VPN 전면 장애 시:** VPN 인프라 장애 발생 시 IT보안팀이 긴급 접속 게이트웨이(https://emergency.metacode.co.kr)를 활성화합니다. VPN 없이 브라우저를 통해 핵심 시스템(이메일, Slack, Jira)에 접근할 수 있습니다.

8.2. **장애 공지:** VPN 장애는 다음 채널을 통해 안내됩니다:
   - 전 직원 SMS 알림 (PagerDuty 경유)
   - 전사 이메일: all-staff@metacode.co.kr
   - 상태 페이지: https://status.metacode.co.kr

8.3. **당직 연락:** 인프라 당직팀이 24시간 VPN 긴급 상황에 대응합니다. PagerDuty 또는 전화(02-1234-5678)로 연락하세요.

---

## 9. 보안 유의사항

- VPN 설정 파일을 절대 타인과 공유하지 마세요.
- VPN 보안 침해가 의심되면 즉시 security@metacode.co.kr 로 신고하세요.
- 개인 VPN 서비스(NordVPN, ExpressVPN 등)를 회사 VPN과 동시에 사용하지 마세요.
- VPN 클라이언트를 항상 최신 버전으로 유지하세요.
- VPN은 보안 감사를 위해 연결 시각과 데이터 전송량을 기록합니다. 트래픽 내용은 검사하지 않습니다.

---

## 10. 연락처 및 지원

- **VPN 문제:** Slack #vpn-지원
- **IT 헬프데스크:** security@metacode.co.kr 또는 Slack #it-헬프데스크
- **긴급 연락 (24시간):** 02-1234-5678
- **셀프서비스 포탈:** https://itportal.metacode.co.kr/vpn
- **VPN 상태 페이지:** https://status.metacode.co.kr

---

*설정 파일은 90일마다 갱신됩니다. 현재 설정 파일 만료 14일 전에 이메일로 안내드립니다.*
