---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 06 — 에러 처리와 ToolError 패턴"
---

# EP 06 — 에러 처리와 ToolError 패턴
## Module B: Tools 심화 · MCP 실전 마스터

---

## 학습 목표

1. MCP의 에러 처리 메커니즘(프로토콜 에러 vs Tool 에러)을 구분할 수 있다
2. ToolError 구조와 `isError` 필드의 의미를 이해한다
3. 사용자 친화적 에러 메시지를 설계하고 구현할 수 있다

---

## 두 종류의 에러

### 프로토콜 에러 (JSON-RPC Error)
```json
{
  "error": {
    "code": -32602,
    "message": "Invalid params: unknown tool"
  }
}
```
→ 프로토콜 수준 문제 (존재하지 않는 Tool 등)

### Tool 에러 (Application Error)
```json
{
  "result": {
    "content": [{ "type": "text", "text": "파일을 찾을 수 없습니다" }],
    "isError": true
  }
}
```
→ 비즈니스 로직 문제 (파일 없음, 잘못된 입력 등)

---

## JSON-RPC 에러 코드

| 코드 | 이름 | 의미 |
|------|------|------|
| -32700 | ParseError | JSON 파싱 실패 |
| -32600 | InvalidRequest | 잘못된 요청 |
| -32601 | MethodNotFound | 메서드 없음 |
| -32602 | InvalidParams | 잘못된 파라미터 |
| -32603 | InternalError | 서버 내부 에러 |

---

## isError 플래그

`isError: true`를 받은 LLM은:
- 이것이 **에러 상황**임을 인지
- 에러 메시지 기반으로 **사용자에게 설명** 또는 **재시도**
- Tool 호출이 **실패했지만 프로토콜은 정상**임을 구분

---

## 에러 vs 빈 결과

| 상황 | 처리 | 이유 |
|------|------|------|
| 검색 결과 없음 | 빈 배열 | 정상 동작 |
| 필수 파라미터 누락 | `isError: true` | 입력 오류 |
| 데이터 파일 없음 | `isError: true` | 시스템 문제 |
| 권한 없음 | `isError: true` | 접근 제한 |
| 외부 API 타임아웃 | `isError: true` | 일시적 문제 |

원칙: **"데이터 없음"과 "시스템 고장"을 구분!**

---

## 에러 코드 체계

```python
class ToolErrorCode(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    NOT_FOUND = "NOT_FOUND"
    DATA_ERROR = "DATA_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
```

일관된 코드 체계로 에러 분류

---

## 사용자 친화적 에러 메시지

```python
# 나쁜 예
"Error: KeyError at line 42 in inventory.py"

# 좋은 예
"재고 데이터를 불러올 수 없습니다. "
"data/inventory.csv 파일이 존재하는지 확인해주세요."
```

원칙:
1. **무엇이** 잘못되었는지 (현상)
2. **왜** 잘못되었는지 (원인)
3. **어떻게** 해결하는지 (제안)

---

## make_error 유틸리티

```python
def make_error(code, message, suggestion=""):
    error = {
        "error": {
            "code": code.value,
            "message": message,
        }
    }
    if suggestion:
        error["error"]["suggestion"] = suggestion
    return json.dumps(error, ensure_ascii=False)
```

모든 Tool에서 일관된 에러 포맷 사용

---

## 에러 처리 적용 예시

```python
@mcp.tool()
async def lookup_inventory(query: str, ctx: Context) -> str:
    if not query.strip():
        raise ValueError(make_error(
            ToolErrorCode.INVALID_INPUT,
            "검색어가 비어있습니다.",
            "품목명이나 카테고리를 입력해주세요.",
        ))

    if not app.inventory:
        raise RuntimeError(make_error(
            ToolErrorCode.DATA_ERROR,
            "재고 데이터를 불러올 수 없습니다.",
        ))
```

---

## 데모: 에러 시나리오 테스트

Inspector에서:
1. `query=""` → INVALID_INPUT 에러
2. `query="a" * 200` → INVALID_INPUT (길이 초과)
3. `category="printer"` → 유효하지 않은 카테고리
4. `query="프린터"` → **정상 응답** (빈 배열, 에러 아님!)

---

## 핵심 정리

- **프로토콜 에러**: JSON-RPC error 필드 (시스템 수준)
- **Tool 에러**: result + `isError: true` (비즈니스 수준)
- **빈 결과 =/= 에러**: 데이터 없음은 정상 응답
- 에러 메시지: **현상 + 원인 + 제안**
- `ToolErrorCode` + `make_error`로 일관성 유지

---

## 퀴즈

1. 프로토콜 에러와 Tool 에러의 차이?
   → 프로토콜 에러는 error 필드, Tool 에러는 result + isError: true

2. 검색 결과 0건일 때 isError: true?
   → 아니다. 빈 배열 반환. isError는 시스템 문제에만 사용.

---

## 다음 편 예고

### EP 07: 실전 Tool (2) — 정책 검색

- Markdown 파일 파싱
- YAML front-matter 활용
- 가중치 기반 검색 랭킹
