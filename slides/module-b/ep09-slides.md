---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 09 — 실전 Tool (3) 티켓 생성"
---

# EP 09 — 실전 Tool (3) 티켓 생성
## Module B: Tools 심화 · MCP 실전 마스터

---

## 학습 목표

1. 확인 게이트(confirm 패턴)가 포함된 Tool을 설계할 수 있다
2. Idempotency Key를 활용하여 중복 생성을 방지할 수 있다
3. JSONL 파일 기반 영속성을 구현할 수 있다

---

## 읽기 Tool vs 쓰기 Tool

| | 읽기 Tool | 쓰기 Tool |
|---|----------|----------|
| EP05 | lookup_inventory | |
| EP07 | search_policy | |
| EP09 | | **create_ticket** |
| 부수 효과 | 없음 (안전) | **있음 (되돌릴 수 없음)** |
| 검증 필요도 | 중간 | **높음** |

쓰기 Tool에는 **추가 안전장치**가 필요!

---

## 확인 게이트 패턴

```
Step 1: confirm=False → 프리뷰만 반환 (변경 없음)
Step 2: confirm=True  → 실제 생성
```

```
사용자: "키보드 수리 접수해줘"
LLM: create_ticket(..., confirm=False)
서버: 프리뷰 반환
LLM: "이렇게 생성할까요?" (사용자에게 확인)
사용자: "네"
LLM: create_ticket(..., confirm=True)
서버: 티켓 생성 완료!
```

---

## Idempotency Key

동일한 요청이 두 번 와도 **한 번만 생성**

```python
def generate_idempotency_key(title, description):
    content = f"{title}:{description}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

- 같은 제목 + 설명 → 같은 키
- 키가 이미 존재 → 기존 티켓 반환 (새로 생성 안 함)
- 네트워크 재시도, LLM 중복 호출 방지

---

## JSONL 저장

```jsonl
{"id":"TK-001","title":"키보드 고장","priority":"medium",...}
{"id":"TK-002","title":"모니터 깜빡임","priority":"high",...}
```

장점:
- 라인 단위 **append** (파일 전체를 읽지 않아도 됨)
- **스트리밍 파싱** 가능 (메모리 효율)
- 사람이 읽기 쉬움 (디버깅 용이)

---

## create_ticket 핵심 흐름

```python
@mcp.tool()
async def create_ticket(
    title: str,
    description: str,
    priority: str = "medium",
    confirm: bool = False,
    ctx: Context = None,
) -> str:
    # 1. 입력 검증 (validation.py)
    validated = validate_ticket_input(title, description, priority)

    # 2. 중복 확인 (Idempotency Key)
    idem_key = generate_idempotency_key(title, description)
    if exists(idem_key): return "duplicate"

    # 3. 프리뷰 vs 생성
    if not confirm: return preview
    else: save_ticket(); return "created"
```

---

## 프리뷰 응답

```json
{
  "status": "preview",
  "message": "아래 내용으로 티켓이 생성됩니다.",
  "ticket_preview": {
    "title": "키보드 A키 고장",
    "description": "로지텍 MX Keys의 A키가 눌리지 않습니다",
    "priority": "medium",
    "estimated_id": "TK-0001"
  }
}
```

데이터 변경 없이 미리보기만 제공

---

## 생성 응답

```json
{
  "status": "created",
  "message": "티켓이 성공적으로 생성되었습니다.",
  "ticket": {
    "id": "TK-0001",
    "title": "키보드 A키 고장",
    "status": "open",
    "created_at": "2026-02-21T10:30:00+00:00",
    "idempotency_key": "a1b2c3d4e5f6g7h8"
  }
}
```

---

## 중복 응답

```json
{
  "status": "duplicate",
  "message": "동일한 티켓이 이미 존재합니다.",
  "existing_ticket": {
    "id": "TK-0001",
    ...
  }
}
```

Idempotency Key로 중복 감지 → 기존 티켓 반환

---

## list_tickets 보조 Tool

```python
@mcp.tool()
async def list_tickets(
    status: str = "",      # open, in_progress, resolved
    limit: int = 10,
    ctx: Context = None,
) -> str:
    """생성된 티켓 목록을 조회합니다."""
    tickets = load_tickets(TICKETS_FILE)
    if status:
        tickets = [t for t in tickets if t["status"] == status]
    return json.dumps({"total": len(tickets), "tickets": tickets})
```

---

## 데모: 전체 플로우 테스트

```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

1. **프리뷰**: `confirm=false` → status: "preview"
2. **생성**: `confirm=true` → status: "created", id: TK-0001
3. **중복**: 같은 내용 재호출 → status: "duplicate"
4. **조회**: `list_tickets(status="open")` → 목록

---

## 상태 기반 설계

```
create_ticket(confirm=false) → PREVIEW
create_ticket(confirm=true)  → CREATED (status: open)
update_ticket_status          → open → in_progress → resolved → closed
```

EP09 이후 실습: `update_ticket_status` Tool 추가

---

## Module B 완성!

| EP | Tool | 역할 |
|----|------|------|
| 05 | `lookup_inventory` | 재고 조회 (읽기) |
| 07 | `search_policy` | 정책 검색 (읽기) |
| 09 | `create_ticket` | 티켓 생성 (쓰기) |

+ EP06: 에러 처리 / EP08: 입력 검증

---

## 핵심 정리

- **확인 게이트**: confirm=false(프리뷰) → true(실행)
- **Idempotency Key**: SHA-256 해시로 중복 방지
- **JSONL**: 라인 단위 append, 효율적 영속성
- 3대 Tool 완성: 재고 + 정책 + 티켓

---

## 퀴즈

1. 확인 게이트가 필요한 이유?
   → 되돌릴 수 없는 부수 효과. 사용자 확인 없이 실행하면 위험.

2. Idempotency Key 생성 방법?
   → 제목+설명의 SHA-256 해시 앞 16자. 같은 입력 = 같은 키.

---

## 다음 편 예고

### EP 10: Resource 기초 — 데이터를 노출하라

- Tool vs Resource의 차이
- 정적 Resource와 동적 Resource Template
- `ops://` 커스텀 URI 스키마
