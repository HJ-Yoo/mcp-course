# EP 09 — 실전 Tool (3) 티켓 생성 (create_ticket)

> Module B: Tools 심화 · 약 20분

## 학습 목표

1. 확인 게이트(confirm 패턴)가 포함된 Tool을 설계할 수 있다
2. Idempotency Key를 활용하여 중복 생성을 방지할 수 있다
3. JSONL 파일 기반 영속성을 구현할 수 있다

---

## 1. 인트로 (2분)

EP05에서 재고 조회(읽기), EP07에서 정책 검색(읽기)을 구현했습니다. 이번에는 성격이 다른 Tool을 만듭니다 — **데이터를 생성하는 Tool**입니다.

IT 지원 티켓을 생성하는 `create_ticket`은 단순 조회와 달리 **되돌릴 수 없는 부수 효과(side effect)**를 가집니다. 한 번 생성된 티켓은 취소해야 하고, 중복 생성이 되면 안 됩니다. 그래서 "정말 생성할까요?" 확인 단계가 필요합니다.

이번 에피소드에서는 이런 **상태 변경 Tool**을 안전하게 설계하는 패턴을 배웁니다.

---

## 2. 핵심 개념 (6분)

### 2.1 확인 게이트 패턴

부수 효과가 있는 Tool에는 확인 게이트를 추가합니다:

```
Step 1: confirm=False → 프리뷰만 반환 (데이터 변경 없음)
Step 2: confirm=True  → 실제 생성 수행
```

LLM의 일반적 사용 흐름:
1. 사용자: "키보드 고장, 수리 접수해줘"
2. LLM: `create_ticket(title="키보드 고장", ..., confirm=False)` 호출
3. 서버: 프리뷰 반환 (이렇게 생성됩니다)
4. LLM: 사용자에게 프리뷰 보여주기
5. 사용자: "네, 접수해줘"
6. LLM: `create_ticket(title="키보드 고장", ..., confirm=True)` 호출
7. 서버: 티켓 생성, ID 반환

### 2.2 Idempotency Key

네트워크 문제나 LLM 재시도로 동일한 요청이 두 번 올 수 있습니다. Idempotency Key로 중복을 방지합니다:

```python
import hashlib

def generate_idempotency_key(title: str, description: str) -> str:
    """동일한 입력에 대해 동일한 키를 생성합니다."""
    content = f"{title}:{description}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

같은 제목 + 설명이면 같은 key가 생성되므로, key가 이미 존재하면 기존 티켓을 반환합니다.

### 2.3 JSONL 저장

티켓은 JSONL(JSON Lines) 파일에 저장합니다. 각 줄이 하나의 JSON 객체입니다:

```jsonl
{"id":"TK-001","title":"키보드 고장","description":"로지텍 MX Keys 'A'키 불량","priority":"medium","status":"open","created_at":"2026-02-21T10:30:00","idempotency_key":"a1b2c3d4e5f6g7h8"}
{"id":"TK-002","title":"모니터 깜빡임","description":"Dell 모니터 화면 깜빡임 현상","priority":"high","status":"open","created_at":"2026-02-21T11:15:00","idempotency_key":"i9j0k1l2m3n4o5p6"}
```

JSONL의 장점:
- 라인 단위 append (파일 전체를 읽지 않아도 됨)
- 스트리밍 파싱 가능 (메모리 효율적)
- 사람이 읽기 쉬움 (디버깅 용이)

### 2.4 티켓 ID 생성 전략

```python
def generate_ticket_id(existing_count: int) -> str:
    """순차적 티켓 ID를 생성합니다."""
    return f"TK-{existing_count + 1:04d}"
```

UUID를 사용할 수도 있지만, 사람이 다루기 쉬운 순차 ID를 선택했습니다. 프로덕션에서는 동시성을 고려해야 하지만, 이 프로젝트에서는 단일 서버이므로 순차 ID로 충분합니다.

### 2.5 상태 기반 도구 설계

티켓 관련 Tool들은 상태 기계(State Machine)를 형성합니다:

```
create_ticket(confirm=False) → PREVIEW
create_ticket(confirm=True)  → CREATED (status: open)
update_ticket_status          → UPDATED (status: in_progress/resolved/closed)
```

---

## 3. 라이브 데모 (10분)

### Step 1: 디렉토리 준비

macOS/Linux:
```bash
mkdir -p data/tickets
```

Windows (PowerShell):
```powershell
mkdir -Force data\tickets
```

### Step 2: create_ticket 구현

```python
# src/tools/ticket.py
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import Context

from errors import ToolErrorCode, make_error
from validation import validate_ticket_input


TICKETS_FILE = "data/tickets/tickets.jsonl"


def generate_idempotency_key(title: str, description: str) -> str:
    """동일한 입력에 대해 동일한 키를 생성합니다."""
    content = f"{title}:{description}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def load_tickets(filepath: str) -> list[dict]:
    """JSONL 파일에서 모든 티켓을 로딩합니다."""
    tickets = []
    path = Path(filepath)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tickets.append(json.loads(line))
    return tickets


def save_ticket(filepath: str, ticket: dict) -> None:
    """JSONL 파일에 티켓 하나를 추가합니다."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ticket, ensure_ascii=False) + "\n")


def generate_ticket_id(existing_count: int) -> str:
    """순차적 티켓 ID를 생성합니다."""
    return f"TK-{existing_count + 1:04d}"


def register_ticket_tools(mcp):
    """티켓 관련 Tool을 등록합니다."""

    @mcp.tool()
    async def create_ticket(
        title: str,
        description: str,
        priority: str = "medium",
        confirm: bool = False,
        ctx: Context = None,
    ) -> str:
        """IT 지원 티켓을 생성합니다.

        confirm=False로 호출하면 프리뷰만 반환합니다.
        confirm=True로 호출하면 실제로 티켓을 생성합니다.
        동일한 제목+설명으로 중복 생성은 방지됩니다.

        Args:
            title: 티켓 제목 (5자 이상)
            description: 문제 상세 설명 (10자 이상)
            priority: 우선순위 — low, medium, high, critical (기본: medium)
            confirm: True이면 실제 생성, False이면 프리뷰만
        """
        # 1. 입력 검증
        validated = validate_ticket_input(title, description, priority)
        title = validated["title"]
        description = validated["description"]
        priority = validated["priority"]

        # 2. Idempotency Key 생성
        idem_key = generate_idempotency_key(title, description)

        # 3. 기존 티켓 확인 (중복 방지)
        existing_tickets = load_tickets(TICKETS_FILE)
        duplicate = next(
            (t for t in existing_tickets if t.get("idempotency_key") == idem_key),
            None,
        )

        if duplicate:
            return json.dumps({
                "status": "duplicate",
                "message": "동일한 티켓이 이미 존재합니다.",
                "existing_ticket": duplicate,
            }, ensure_ascii=False, indent=2)

        # 4. 프리뷰 모드
        if not confirm:
            preview = {
                "status": "preview",
                "message": "아래 내용으로 티켓이 생성됩니다. confirm=True로 다시 호출하면 생성됩니다.",
                "ticket_preview": {
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "estimated_id": generate_ticket_id(len(existing_tickets)),
                },
            }
            await ctx.info(f"티켓 프리뷰 생성: '{title}'")
            return json.dumps(preview, ensure_ascii=False, indent=2)

        # 5. 실제 생성
        ticket_id = generate_ticket_id(len(existing_tickets))
        now = datetime.now(timezone.utc).isoformat()

        ticket = {
            "id": ticket_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "open",
            "created_at": now,
            "idempotency_key": idem_key,
        }

        save_ticket(TICKETS_FILE, ticket)

        await ctx.info(f"티켓 생성 완료: {ticket_id} - '{title}'")

        return json.dumps({
            "status": "created",
            "message": f"티켓이 성공적으로 생성되었습니다.",
            "ticket": ticket,
        }, ensure_ascii=False, indent=2)

    @mcp.tool()
    async def list_tickets(
        status: str = "",
        limit: int = 10,
        ctx: Context = None,
    ) -> str:
        """생성된 티켓 목록을 조회합니다.

        Args:
            status: 필터할 상태 (open, in_progress, resolved, closed). 비우면 전체
            limit: 반환할 최대 티켓 수 (기본: 10)
        """
        tickets = load_tickets(TICKETS_FILE)

        if status:
            tickets = [t for t in tickets if t.get("status") == status.lower()]

        # 최신순 정렬
        tickets.sort(key=lambda t: t.get("created_at", ""), reverse=True)
        tickets = tickets[:limit]

        return json.dumps({
            "total": len(tickets),
            "tickets": tickets,
        }, ensure_ascii=False, indent=2)
```

### Step 3: server.py에 등록

```python
# src/server.py에 추가
from tools.ticket import register_ticket_tools

register_ticket_tools(mcp)
```

### Step 4: 전체 플로우 테스트

macOS/Linux:
```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

Windows (PowerShell):
```powershell
npx @modelcontextprotocol/inspector uv run python src\server.py
```

**테스트 시나리오: 티켓 생성 전체 플로우**

1. **프리뷰** — `create_ticket(title="키보드 A키 고장", description="로지텍 MX Keys의 A키가 눌리지 않습니다", priority="medium", confirm=false)`
   - 응답: `status: "preview"`, estimated_id, 프리뷰 내용

2. **확인 생성** — `create_ticket(title="키보드 A키 고장", description="로지텍 MX Keys의 A키가 눌리지 않습니다", priority="medium", confirm=true)`
   - 응답: `status: "created"`, ticket_id: "TK-0001"

3. **중복 시도** — 같은 내용으로 다시 `confirm=true` 호출
   - 응답: `status: "duplicate"`, 기존 티켓 정보

4. **목록 조회** — `list_tickets(status="open")`
   - 응답: 생성된 티켓 목록

### Step 5: JSONL 파일 확인

macOS/Linux:
```bash
cat data/tickets/tickets.jsonl
```

Windows (PowerShell):
```powershell
type data\tickets\tickets.jsonl
```

생성된 티켓이 JSONL 형식으로 저장되어 있음을 확인합니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- **확인 게이트**: `confirm=False`(프리뷰) → `confirm=True`(실행)로 부수 효과를 안전하게 관리
- **Idempotency Key**: 동일 입력에 동일 키 → 중복 생성 방지
- **JSONL 저장**: 라인 단위 append로 효율적인 영속성
- **상태 기반 설계**: 프리뷰 → 생성 → 상태 변경의 명확한 흐름
- EP05의 `lookup_inventory`, EP07의 `search_policy`와 함께 캡스톤의 3대 Tool이 완성됨

### 퀴즈

1. **확인 게이트(confirm 패턴)가 필요한 이유는?**
   → 티켓 생성은 되돌릴 수 없는 부수 효과가 있으므로, 사용자 확인 없이 바로 실행하면 위험하다.

2. **Idempotency Key는 어떻게 생성되나?**
   → 제목과 설명을 합친 문자열의 SHA-256 해시 앞 16자리. 같은 입력이면 같은 키.

### 다음 편 예고

EP10에서는 Tool에서 Resource로 전환합니다. **MCP Resource**란 무엇이고, Tool과 어떻게 다르며, 정적/동적 Resource를 어떻게 구현하는지 배웁니다. EP07에서 만든 `search_policy`의 결과에 포함된 `resource_uri`를 실제로 구현할 예정입니다.
