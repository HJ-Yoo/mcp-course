---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 04 — Tool 기초: 함수를 도구로"
---

# EP 04 — Tool 기초: 함수를 도구로
## Module B: Tools 심화 · MCP 실전 마스터

---

## 학습 목표

1. `@mcp.tool()` 데코레이터로 함수를 MCP Tool로 변환할 수 있다
2. 타입 힌트와 docstring이 JSON Schema로 변환되는 과정을 이해한다
3. Context 객체를 활용하여 진행 상황 보고와 로깅을 할 수 있다

---

## @mcp.tool() 데코레이터

```python
@mcp.tool()
def echo(message: str) -> str:
    """입력받은 메시지를 그대로 반환합니다."""
    return message
```

데코레이터가 하는 일:
1. 함수 이름 → **Tool 이름** (`echo`)
2. docstring → **Tool 설명**
3. 타입 힌트 → **JSON Schema**
4. 반환값 → **결과 포맷팅**

---

## 타입 힌트 → JSON Schema

```python
@mcp.tool()
def search(
    query: str,              # required
    category: str = "all",   # optional (기본값 있음)
    limit: int = 10,         # optional
) -> str:
```

```json
{
  "properties": {
    "query": { "type": "string" },
    "category": { "type": "string", "default": "all" },
    "limit": { "type": "integer", "default": 10 }
  },
  "required": ["query"]
}
```

---

## docstring → 파라미터 설명

```python
def search(query: str, category: str = "all") -> str:
    """재고를 검색합니다.

    Args:
        query: 검색 키워드
        category: 카테고리 필터 (기본: all)
    """
```

`Args` 섹션이 각 파라미터의 `description`으로 변환!

---

## Tool 결과 포맷

```python
# 문자열 반환
return "MacBook Pro - 재고: 23대"
# → { "content": [{ "type": "text", "text": "..." }] }

# dict 반환
return {"item": "MacBook Pro", "stock": 23}
# → { "content": [{ "type": "text", "text": "{...}" }] }
```

반환값이 자동으로 `content` 배열로 래핑됨

---

## Context 객체

```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def search(query: str, ctx: Context) -> str:
    """검색합니다."""
    await ctx.info("검색 시작...")

    for i, item in enumerate(items):
        await ctx.report_progress(i + 1, total)

    await ctx.info("검색 완료!")
    return results
```

- `ctx.info()` / `ctx.warning()` / `ctx.error()` — 로깅
- `ctx.report_progress(current, total)` — 진행률

---

## Context에서 AppContext 접근

```python
@mcp.tool()
async def count_items(category: str, ctx: Context) -> str:
    """카테고리별 아이템을 셉니다."""

    # Lifespan에서 전달한 데이터에 접근
    app = ctx.request_context.lifespan_context["app"]

    count = sum(
        1 for item in app.inventory
        if item["category"] == category
    )
    return f"{category}: {count}건"
```

EP03의 Lifespan → 여기서 활용!

---

## 동기 vs 비동기

```python
# 동기 — 간단한 계산
@mcp.tool()
def add(a: int, b: int) -> str:
    return str(a + b)

# 비동기 — I/O 작업, Context 사용
@mcp.tool()
async def fetch(url: str, ctx: Context) -> str:
    await ctx.info(f"Fetching {url}...")
    return result
```

Context 사용 시 `async` 권장

---

## 데모: Inspector에서 테스트

```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

1. Tools 탭 → 등록된 Tool 목록 확인
2. echo 선택 → `message` 입력 → 실행
3. 자동 생성된 `inputSchema` 확인
4. Context 로그 메시지 확인

---

## 핵심 정리

- `@mcp.tool()` = Python 함수 → MCP Tool 변환
- **타입 힌트** → JSON Schema, **docstring** → 설명
- 기본값 있음 → optional, 없음 → required
- **Context**: 로깅, 진행률, Lifespan 데이터 접근
- I/O 작업 시 `async` 권장

---

## 퀴즈

1. 파라미터가 required/optional인 기준은?
   → 기본값 없으면 required, 있으면 optional

2. Context 객체 사용법은?
   → 파라미터에 `ctx: Context` 추가하면 자동 주입

---

## 다음 편 예고

### EP 05: 실전 Tool (1) — 재고 조회

- CSV 데이터 로딩
- fuzzy 검색 구현
- Claude Desktop에서 "노트북 재고 알려줘" 테스트
