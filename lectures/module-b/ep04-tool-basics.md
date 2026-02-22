# EP 04 — Tool 기초: 함수를 도구로

> Module B: Tools 심화 · 약 20분

## 학습 목표

1. `@mcp.tool()` 데코레이터로 Python 함수를 MCP Tool로 변환할 수 있다
2. 타입 힌트와 docstring이 JSON Schema로 자동 변환되는 과정을 이해한다
3. Context 객체를 활용하여 진행 상황 보고와 로깅을 할 수 있다

---

## 1. 인트로 (2분)

EP03에서 FastMCP로 서버의 뼈대를 만들고 간단한 `hello` Tool을 구현했습니다. 이번 에피소드에서는 Tool의 동작 원리를 깊이 파고듭니다.

MCP에서 Tool은 **LLM이 호출할 수 있는 함수**입니다. 여러분이 작성한 Python 함수가 어떻게 LLM이 이해하는 도구로 변환되는지, 파라미터는 어떻게 전달되는지, 결과는 어떤 포맷으로 반환되는지 배워보겠습니다.

---

## 2. 핵심 개념 (6분)

### 2.1 @mcp.tool() 데코레이터

Python 함수에 `@mcp.tool()` 데코레이터를 붙이면 MCP Tool이 됩니다:

```python
@mcp.tool()
def echo(message: str) -> str:
    """입력받은 메시지를 그대로 반환합니다."""
    return message
```

데코레이터가 하는 일:
1. 함수 이름 → Tool 이름 (`echo`)
2. docstring → Tool 설명
3. 타입 힌트 → JSON Schema (inputSchema)
4. 반환값 → Tool 결과 포맷팅

### 2.2 타입 힌트와 JSON Schema 자동 변환

Python 타입 힌트는 자동으로 JSON Schema로 변환됩니다:

```python
@mcp.tool()
def search(
    query: str,
    category: str = "all",
    limit: int = 10,
) -> str:
    """재고를 검색합니다.

    Args:
        query: 검색 키워드
        category: 카테고리 필터 (기본: all)
        limit: 결과 개수 제한 (기본: 10)
    """
    ...
```

이 함수는 다음 JSON Schema를 생성합니다:

```json
{
  "name": "search",
  "description": "재고를 검색합니다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "검색 키워드"
      },
      "category": {
        "type": "string",
        "description": "카테고리 필터 (기본: all)",
        "default": "all"
      },
      "limit": {
        "type": "integer",
        "description": "결과 개수 제한 (기본: 10)",
        "default": 10
      }
    },
    "required": ["query"]
  }
}
```

기본값이 있는 파라미터는 `required`에서 제외됩니다. LLM은 이 스키마를 보고 어떤 파라미터를 전달할지 결정합니다.

### 2.3 Tool 결과 포맷

Tool의 반환값은 `content` 배열로 변환됩니다:

**문자열 반환**: 텍스트 콘텐츠로 변환
```python
return "MacBook Pro - 재고: 23대"
# → { "content": [{ "type": "text", "text": "MacBook Pro - 재고: 23대" }] }
```

**dict/list 반환**: JSON 문자열로 변환
```python
return {"item": "MacBook Pro", "stock": 23}
# → { "content": [{ "type": "text", "text": '{"item":"MacBook Pro","stock":23}' }] }
```

**에러 상황**: `isError: true` 설정 (EP06에서 상세 다룸)
```python
return {"error": "Not found", "isError": True}
```

### 2.4 Context 객체 활용

Tool 함수에 `Context` 타입 파라미터를 추가하면 MCP 런타임 정보에 접근할 수 있습니다:

```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def long_search(query: str, ctx: Context) -> str:
    """시간이 오래 걸리는 검색을 수행합니다."""
    await ctx.info(f"'{query}' 검색 시작...")

    results = []
    total = len(database)
    for i, item in enumerate(database):
        if query in item["name"]:
            results.append(item)
        # 진행률 보고
        await ctx.report_progress(i + 1, total)

    await ctx.info(f"검색 완료: {len(results)}건")
    return json.dumps(results, ensure_ascii=False)
```

Context가 제공하는 주요 기능:
- `ctx.info(message)`: 정보 로깅
- `ctx.warning(message)`: 경고 로깅
- `ctx.error(message)`: 에러 로깅
- `ctx.report_progress(current, total)`: 진행률 보고
- `ctx.request_context.lifespan_context`: Lifespan에서 전달한 데이터 접근

### 2.5 동기 vs 비동기 Tool

FastMCP는 동기와 비동기 함수 모두 지원합니다:

```python
# 동기 — 간단한 작업에 적합
@mcp.tool()
def add(a: int, b: int) -> str:
    """두 수를 더합니다."""
    return str(a + b)

# 비동기 — I/O 작업, Context 사용 시
@mcp.tool()
async def fetch_data(url: str, ctx: Context) -> str:
    """외부 데이터를 가져옵니다."""
    await ctx.info(f"Fetching {url}...")
    # async 작업 수행
    return result
```

Context를 사용하거나 I/O 작업이 포함된 경우 `async`를 권장합니다.

---

## 3. 라이브 데모 (10분)

### Step 1: echo Tool 작성

EP03에서 만든 `server.py`에 새로운 Tool을 추가합니다:

```python
# src/server.py에 추가

@mcp.tool()
def echo(message: str) -> str:
    """입력받은 메시지를 그대로 반환합니다.

    Args:
        message: 반환할 메시지
    """
    return f"Echo: {message}"
```

### Step 2: 복합 파라미터 Tool 작성

```python
import json

@mcp.tool()
def calculate(
    operation: str,
    a: float,
    b: float,
    precision: int = 2,
) -> str:
    """사칙연산을 수행합니다.

    Args:
        operation: 연산 종류 (add, subtract, multiply, divide)
        a: 첫 번째 숫자
        b: 두 번째 숫자
        precision: 소수점 자릿수 (기본: 2)
    """
    ops = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else None,
    }

    result = ops.get(operation)
    if result is None:
        return json.dumps({"error": f"Unknown operation: {operation}"})

    return json.dumps({
        "operation": operation,
        "a": a,
        "b": b,
        "result": round(result, precision),
    })
```

### Step 3: Context 활용 Tool 작성

```python
@mcp.tool()
async def count_items(category: str, ctx: Context) -> str:
    """카테고리별 아이템 수를 셉니다.

    Args:
        category: 조회할 카테고리
    """
    app: AppContext = ctx.request_context.lifespan_context["app"]

    await ctx.info(f"카테고리 '{category}' 조회 중...")

    count = sum(
        1 for item in app.inventory
        if item.get("category", "").lower() == category.lower()
    )

    await ctx.info(f"조회 완료: {count}건")
    return f"카테고리 '{category}'의 아이템 수: {count}건"
```

### Step 4: MCP Inspector에서 테스트

macOS/Linux:
```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

Windows (PowerShell):
```powershell
npx @modelcontextprotocol/inspector uv run python src\server.py
```

Inspector에서:
1. Tools 탭에서 `echo`, `calculate`, `count_items` 3개 Tool 확인
2. `echo` 호출: `message`에 "Hello MCP!" 입력
3. `calculate` 호출: `operation`="multiply", `a`=3.14, `b`=2 입력
4. `count_items` 호출: `category`에 "laptop" 입력

### Step 5: JSON Schema 확인

Inspector의 Tool 상세 화면에서 자동 생성된 `inputSchema`를 확인합니다. Python 타입 힌트, docstring의 Args 섹션, 기본값이 정확하게 반영되어 있는지 비교합니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- `@mcp.tool()` 데코레이터로 Python 함수를 MCP Tool로 변환한다
- **타입 힌트** → JSON Schema, **docstring** → Tool 설명으로 자동 변환된다
- 기본값이 있는 파라미터는 **optional**, 없으면 **required**가 된다
- **Context** 객체로 로깅, 진행률 보고, Lifespan 데이터 접근이 가능하다
- 동기/비동기 함수 모두 지원되지만, I/O 작업 시 `async`를 권장한다

### 퀴즈

1. **Tool의 파라미터가 required인지 optional인지 어떻게 결정되나?**
   → 기본값이 없으면 required, 기본값이 있으면 optional.

2. **Context 객체를 사용하려면 어떻게 해야 하나?**
   → 함수 파라미터에 `ctx: Context` 타입 힌트를 추가하면 FastMCP가 자동으로 주입한다.

### 다음 편 예고

EP05에서는 첫 번째 실전 Tool을 만듭니다. CSV 파일에서 재고를 조회하는 `lookup_inventory` — 캡스톤 프로젝트의 핵심 기능 중 하나입니다.
