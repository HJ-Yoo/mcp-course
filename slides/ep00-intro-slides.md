---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 00 — 인트로: 5분 만에 보는 MCP의 힘"
---

# EP 00 — 인트로
## 5분 만에 보는 MCP의 힘

> 샘플 강의 · 과정 소개 + 라이브 데모

---

## 이 대화, 뭔가 다릅니다

```
사용자: "노트북 재고가 몇 대 남았어?"

AI: MacBook Pro 14인치 M3 Pro 45대,
    Dell Latitude 5540 30대,
    Lenovo ThinkPad X1 Carbon 12대가
    재고에 있습니다.
```

평범한 챗봇 같죠?
**오른쪽 패널을 보세요.**

---

## MCP 로그 패널

```
✅ Call 1: lookup_inventory (23ms)
   Args: {"query": "노트북"}
   Result: [
     {"name": "MacBook Pro 14\" M3 Pro", "quantity": 45, ...},
     {"name": "Dell Latitude 5540", "quantity": 30, ...},
     {"name": "Lenovo ThinkPad X1 Carbon", "quantity": 12, ...}
   ]
```

AI가 **스스로 판단**해서 도구를 호출했습니다.
대답을 지어낸 게 아니라, **실제 데이터**를 조회한 겁니다.

**이게 바로 MCP입니다.**

---

## LLM의 한계 — 말만 하는 AI

> "뇌는 있는데 **손과 눈이 없는** 상태"

| 질문 | 문제 |
|------|------|
| "재고가 몇 개야?" | DB에 접근할 수 없음 |
| "티켓 만들어줘" | 시스템에 쓰기 권한 없음 |
| "보안 정책이 뭐야?" | 회사 문서를 읽을 수 없음 |

---

## N x M 문제

```
ChatGPT용 Slack 플러그인    Claude용 Slack 플러그인
ChatGPT용 GitHub 플러그인   Claude용 GitHub 플러그인
ChatGPT용 Jira 플러그인     Claude용 Jira 플러그인
...                         ...

    5개 LLM × 20개 서비스 = 100개 커스텀 통합 😱
```

각 회사마다 각 LLM마다 **커스텀 플러그인**을 만들어야 합니다.
이건 **유지보수 지옥**입니다.

---

## MCP = AI 세계의 USB-C

스마트폰 충전기를 기억하세요?
Lightning, Micro USB, 전용 충전기...

**USB-C가 모든 걸 통일했습니다.**

```
LLM들 ──→ [MCP 표준] ←── 외부 서비스들

5 + 20 = 25개 구현이면 전부 연결! ✅
```

서버 하나 만들면, **Claude에서도, Cursor에서도, VS Code에서도** 그대로 작동합니다.

---

## MCP 서버의 3대 구성요소

| 구성요소 | 역할 | 비유 |
|---------|------|------|
| **Tools** | AI가 실행하는 함수 | 🤲 손 |
| **Resources** | AI가 읽는 데이터 | 👁️ 눈 |
| **Prompts** | 재사용 가능한 지시문 | 📋 대본 |

이 세 가지면 AI에게 **손과 눈과 대본**을 줄 수 있습니다.

---

## 라이브 데모: Acme Corp Internal Ops Assistant

<!-- 데모 화면: Gradio UI -->

### 데모 1: 재고 조회 (Tool)
```
사용자: "헤드셋 재고 알려줘"
→ AI가 lookup_inventory 호출
→ Jabra Evolve2 75 (40개), Poly Voyager Focus 2 (20개)
```

AI가 "헤드셋"이라는 자연어를 이해하고
스스로 검색 쿼리를 구성해서 도구를 호출

---

## 데모 2: 정책 문서 검색 (Tool + Resource)

```
사용자: "원격근무할 때 인터넷 비용 지원이 되나요?"

→ AI가 search_policy Tool로 관련 정책을 찾고
→ policy://remote-work Resource로 전문을 읽은 후
→ "월 $75까지 인터넷 비용이 지원됩니다 (Section 5.2)"
```

지어낸 게 아닙니다.
실제 정책 문서의 **특정 섹션을 인용**하고 있습니다.

---

## 데모 3: 티켓 생성 (Tool — 확인 게이트)

```
사용자: "모니터가 깜빡거려서 수리 티켓 만들어줘"

AI: "Preview: 'Monitor flickering issue'
     (priority: medium). 생성할까요?"

사용자: "응, 만들어줘"

→ AI가 confirm=True로 다시 호출
→ TKT-006번 티켓이 JSONL 파일에 저장됨
```

위험한 동작(데이터 변경)은 반드시 **사용자 확인을 거칩니다.**

---

## MCP 로그 — 전체 기록

```
✅ Call 1: lookup_inventory   (23ms)  Args: {"query": "헤드셋"}
✅ Call 2: search_policy      (15ms)  Args: {"query": "인터넷 비용"}
✅ Call 3: create_ticket      (8ms)   Args: {"confirm": false, ...}
✅ Call 4: create_ticket      (12ms)  Args: {"confirm": true, ...}
```

AI가 이 대화에서 총 **4번의 MCP 도구 호출**.
각 호출의 입력값, 결과, 응답 시간이 모두 기록됩니다.

**이 전체 시스템을 이 과정에서 처음부터 끝까지 만듭니다.**

---

## 이 과정에서 만들 것

```
Module A (EP 01-03)  MCP 기초 — 프로토콜 이해, 첫 서버
Module B (EP 04-09)  Tools — 재고 조회, 정책 검색, 티켓 생성
Module C (EP 10-16)  Resources & Prompts + 테스트
Module D (EP 17-21)  클라이언트 연동 — Claude Desktop, Cursor, VS Code
Module E (EP 22-27)  Advanced — 인증, Docker, 모니터링, 프로덕션
```

- 총 **27편, 9시간** · 편당 20분 · 매 편 직접 코드 작성
- 사전 지식: **Python 중급**이면 충분
- 환경 세팅부터 프로덕션 배포까지 전부

---

## 한 번 만들면 어디서든 쓴다.

MCP를 배우면, 여러분이 만든 AI 도구가
**Claude에서도, Cursor에서도, 어떤 LLM에서도** 그대로 동작합니다.

> **That's the power of MCP.**

그럼 **EP 01**에서 만나겠습니다. 감사합니다.
