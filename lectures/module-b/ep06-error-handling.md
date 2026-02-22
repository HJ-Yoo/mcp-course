# EP 06 — 에러 처리와 ToolError 패턴

> Module B: Tools 심화 · 약 20분

## 학습 목표

1. MCP의 에러 처리 메커니즘(프로토콜 에러 vs Tool 에러)을 구분할 수 있다
2. ToolError 구조와 `isError` 필드의 의미를 이해한다
3. 사용자 친화적 에러 메시지를 설계하고 구현할 수 있다

---

## 1. 인트로 (2분)

EP05에서 `lookup_inventory` Tool을 구현했습니다. 잘 동작하는 경우를 다뤘지만, 실전에서는 항상 일이 잘 풀리지만은 않습니다. 파일이 없을 수도 있고, 입력이 잘못될 수도 있고, 서버 내부에서 예외가 발생할 수도 있습니다.

이번 에피소드에서는 MCP에서 에러를 처리하는 두 가지 메커니즘과, LLM에게 에러를 효과적으로 전달하는 방법을 배웁니다.

---

## 2. 핵심 개념 (6분)

### 2.1 두 종류의 에러

MCP에는 두 가지 레벨의 에러가 있습니다:

**프로토콜 에러 (JSON-RPC Error)**: 프로토콜 수준의 문제
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params: unknown tool 'nonexistent'"
  }
}
```
- 존재하지 않는 Tool 호출
- 잘못된 JSON-RPC 포맷
- 서버 내부 크래시

**Tool 에러 (Application Error)**: Tool 실행 중 발생한 비즈니스 로직 에러
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{ "type": "text", "text": "파일을 찾을 수 없습니다: data/inventory.csv" }],
    "isError": true
  }
}
```
- 데이터 파일 미존재
- 잘못된 입력값
- 외부 API 실패

핵심 차이: 프로토콜 에러는 JSON-RPC `error` 필드에, Tool 에러는 `result` 필드에 `isError: true`와 함께 담깁니다.

### 2.2 ErrorCode 종류

JSON-RPC 표준 에러 코드:

| 코드 | 이름 | 의미 |
|------|------|------|
| -32700 | ParseError | JSON 파싱 실패 |
| -32600 | InvalidRequest | 잘못된 JSON-RPC 요청 |
| -32601 | MethodNotFound | 존재하지 않는 메서드 |
| -32602 | InvalidParams | 잘못된 파라미터 |
| -32603 | InternalError | 서버 내부 에러 |

### 2.3 isError 필드의 의미

`isError: true`가 설정된 결과를 클라이언트(LLM)가 받으면:
- LLM은 이것이 **에러 상황**임을 인지합니다
- 에러 메시지를 기반으로 **사용자에게 설명**하거나 **재시도**를 결정합니다
- Tool 호출이 **실패했지만 프로토콜은 정상**이라는 것을 구분합니다

### 2.4 에러 vs 빈 결과: 언제 무엇을?

| 상황 | 처리 방법 | 이유 |
|------|----------|------|
| 검색 결과 없음 | 빈 배열 반환 | 정상 동작, 데이터만 없음 |
| 필수 파라미터 누락 | isError: true | 입력 오류, 수정 필요 |
| 데이터 파일 없음 | isError: true | 시스템 문제 |
| 권한 없음 | isError: true | 접근 제한 |
| 외부 API 타임아웃 | isError: true | 일시적 문제, 재시도 가능 |

원칙: **"데이터가 없는 것"과 "시스템이 고장난 것"을 구분**하라.

### 2.5 사용자 친화적 에러 메시지

나쁜 예:
```
Error: KeyError at line 42 in inventory.py
```

좋은 예:
```
재고 데이터를 불러올 수 없습니다. 데이터 파일(data/inventory.csv)이 존재하는지 확인해주세요.
```

에러 메시지 원칙:
1. **무엇이** 잘못되었는지 (현상)
2. **왜** 잘못되었는지 (원인)
3. **어떻게** 해결할 수 있는지 (제안) — 가능한 경우

---

## 3. 라이브 데모 (10분)

### Step 1: 에러 처리 유틸리티 작성

```python
# src/errors.py
import json
from enum import Enum


class ToolErrorCode(str, Enum):
    """Tool 에러 코드 정의."""
    INVALID_INPUT = "INVALID_INPUT"
    NOT_FOUND = "NOT_FOUND"
    DATA_ERROR = "DATA_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def make_error(
    code: ToolErrorCode,
    message: str,
    suggestion: str = "",
) -> str:
    """일관된 에러 응답을 생성합니다.

    반환값은 MCP Tool에서 return하면 됩니다.
    isError 처리는 raise로 합니다.
    """
    error = {
        "error": {
            "code": code.value,
            "message": message,
        }
    }
    if suggestion:
        error["error"]["suggestion"] = suggestion
    return json.dumps(error, ensure_ascii=False, indent=2)
```

### Step 2: lookup_inventory에 에러 처리 추가

EP05에서 만든 `lookup_inventory`를 개선합니다:

```python
# src/tools/inventory.py 수정
from mcp.server.fastmcp import Context
from errors import ToolErrorCode, make_error


def register_inventory_tools(mcp):

    @mcp.tool()
    async def lookup_inventory(
        query: str,
        category: str = "",
        ctx: Context = None,
    ) -> str:
        """사내 재고를 검색합니다.

        Args:
            query: 검색 키워드 (예: "맥북", "키보드")
            category: 카테고리 필터 (예: "laptop", "keyboard")
        """
        # 1. 입력 검증
        if not query or not query.strip():
            raise ValueError(
                make_error(
                    ToolErrorCode.INVALID_INPUT,
                    "검색어가 비어있습니다.",
                    "검색할 품목명이나 카테고리를 입력해주세요. 예: '맥북', '모니터'",
                )
            )

        if len(query) > 100:
            raise ValueError(
                make_error(
                    ToolErrorCode.INVALID_INPUT,
                    "검색어가 너무 깁니다 (최대 100자).",
                    "더 짧은 검색어를 사용해주세요.",
                )
            )

        # 2. 데이터 접근
        app = ctx.request_context.lifespan_context["app"]

        if not app.inventory:
            raise RuntimeError(
                make_error(
                    ToolErrorCode.DATA_ERROR,
                    "재고 데이터를 불러올 수 없습니다.",
                    "data/inventory.csv 파일이 존재하는지 확인해주세요.",
                )
            )

        # 3. 카테고리 검증
        valid_categories = {item["category"] for item in app.inventory}
        if category and category.lower() not in {c.lower() for c in valid_categories}:
            raise ValueError(
                make_error(
                    ToolErrorCode.INVALID_INPUT,
                    f"알 수 없는 카테고리: '{category}'",
                    f"사용 가능한 카테고리: {', '.join(sorted(valid_categories))}",
                )
            )

        # 4. 정상 검색 로직
        await ctx.info(f"재고 검색: query='{query}'")
        results = search_inventory(app.inventory, query, category or None)

        # ... (결과 포맷팅 — EP05와 동일)
```

### Step 3: 의도적 에러 테스트

Inspector에서 다양한 에러 시나리오를 테스트합니다:

macOS/Linux:
```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

Windows (PowerShell):
```powershell
npx @modelcontextprotocol/inspector uv run python src\server.py
```

테스트 케이스:
1. `query=""` (빈 문자열) → INVALID_INPUT 에러
2. `query="a" * 200` (긴 문자열) → INVALID_INPUT 에러
3. `category="printer"` (없는 카테고리) → INVALID_INPUT + 사용 가능한 카테고리 목록
4. `query="프린터"` (결과 없음) → 정상 응답, 빈 배열 (에러 아님)

### Step 4: 에러 응답 구조 확인

Inspector의 Response 패널에서 에러 응답의 구조를 확인합니다:

```json
{
  "content": [
    {
      "type": "text",
      "text": "..."
    }
  ],
  "isError": true
}
```

`isError: true`가 설정되어 있고, `content`에 에러 메시지가 포함되어 있음을 확인합니다.

### Step 5: Claude Desktop에서 에러 확인

Claude Desktop에서 에러 상황을 유도하고 Claude가 어떻게 반응하는지 관찰합니다:
- "빈 문자열로 재고 검색해줘" → Claude가 에러를 인지하고 다시 질문
- "프린터 재고 알려줘" → 결과 없음을 자연스럽게 안내

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- MCP에는 **프로토콜 에러**(JSON-RPC Error)와 **Tool 에러**(isError)가 있다
- `isError: true`는 Tool 실행은 됐지만 결과가 에러임을 의미한다
- **빈 결과 =/= 에러**: "데이터 없음"과 "시스템 오류"를 구분하라
- 에러 메시지는 **현상 + 원인 + 제안**을 포함해야 한다
- 일관된 에러 구조(`ToolErrorCode`, `make_error`)로 관리하라

### 퀴즈

1. **프로토콜 에러와 Tool 에러의 차이는?**
   → 프로토콜 에러는 JSON-RPC error 필드에, Tool 에러는 result 필드에 isError: true와 함께 담긴다.

2. **검색 결과가 0건일 때 isError를 true로 설정해야 하나?**
   → 아니다. 결과 없음은 정상 동작이므로 빈 배열을 반환한다. isError는 시스템 문제일 때만 사용.

### 다음 편 예고

EP07에서는 두 번째 실전 Tool `search_policy`를 만듭니다. Markdown 파일을 파싱하고, 키워드로 사내 정책을 검색하는 기능을 구현합니다.
