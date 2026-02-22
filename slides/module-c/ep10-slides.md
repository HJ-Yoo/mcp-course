---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 10 — Resource 기초: 데이터를 노출하라"
---

# EP 10 — Resource 기초: 데이터를 노출하라
## Module C · MCP 실전 마스터

---

## 학습 목표

1. Resource와 Tool의 근본적 차이를 이해한다
2. URI 스킴을 설계하고 `@mcp.resource()` 사용법을 익힌다
3. Resource의 MIME type과 반환 형식을 지정할 수 있다

---

## Tool vs Resource

| 구분 | Tool | Resource |
|------|------|----------|
| 역할 | **동작** 수행 | **데이터** 노출 |
| 비유 | 동사 (검색하다, 생성하다) | 명사 (정책 문서, 재고 현황) |
| 부작용 | 있을 수 있음 | 없음 (읽기 전용) |
| LLM 활용 | "이걸 실행해" | "이걸 참고해" |
| 예시 | `lookup_inventory` | `policy://index` |

---

## URI 스킴 설계

```
policy://index              → 모든 정책 문서 목록
policy://{doc_id}           → 특정 정책 문서 상세
inventory://status          → 재고 현황 요약
config://server             → 서버 설정 정보
```

**설계 원칙:**
- 직관적인 스킴명 (도메인 반영)
- 정적 URI: 고정 문자열 (`policy://index`)
- 동적 URI: 템플릿 변수 (`policy://{doc_id}`)

---

## @mcp.resource() 데코레이터

```python
@mcp.resource("time://now")
async def get_current_time() -> str:
    """현재 서버 시간을 반환합니다."""
    return datetime.now().isoformat()

@mcp.resource("server://info", mime_type="application/json")
async def server_info() -> str:
    """서버 정보를 JSON으로 반환합니다."""
    return json.dumps({"name": "Acme Ops", "version": "1.0"})
```

---

## MIME Type 지정

| MIME Type | 용도 | 예시 |
|-----------|------|------|
| `text/plain` | 기본값, 일반 텍스트 | 설정 정보 |
| `application/json` | JSON 데이터 | 정책 목록, API 응답 |
| `text/markdown` | 마크다운 문서 | README, 정책 문서 |

```python
@mcp.resource("policy://index", mime_type="application/json")
async def policy_index() -> str:
    return json.dumps(policies_list)
```

---

## Resource vs Tool 선택 플로우

```
              데이터를 변경하는가?
               /            \
             Yes              No
              │                │
          → Tool          파라미터가 복잡한가?
                            /        \
                          Yes         No
                           │           │
                       → Tool      → Resource
```

---

## 데모: 간단한 Resource 등록

```python
def register(mcp):
    @mcp.resource("time://now")
    async def get_current_time() -> str:
        return datetime.now().isoformat()

    @mcp.resource("server://info", mime_type="application/json")
    async def server_info() -> str:
        info = {
            "name": "Acme Internal Ops Assistant",
            "version": "1.0.0",
            "tools": ["lookup_inventory", "search_policy",
                      "create_ticket"],
        }
        return json.dumps(info, indent=2)
```

---

## MCP Inspector에서 확인

```bash
# macOS/Linux
uv run mcp dev src/server.py

# Windows
uv run mcp dev src\server.py
```

1. **Resources** 탭 클릭
2. `time://now` 선택 → 현재 시간 확인
3. `server://info` 선택 → JSON 정보 확인

---

## Claude Desktop에서 Resource 활용

1. 대화창에서 클립 아이콘 클릭
2. MCP 서버의 Resource 목록 표시
3. `server://info` 선택 → 컨텍스트에 추가
4. "이 서버에서 사용할 수 있는 도구를 설명해줘"

**LLM이 Resource 데이터를 참고하여 정확한 답변 생성**

---

## 동적 URI 템플릿 미리보기

```python
@mcp.resource("policy://{doc_id}")
async def policy_detail(doc_id: str) -> str:
    """특정 정책 문서의 내용을 반환합니다."""
    policy = find_policy(doc_id)
    return policy.content
```

`policy://remote-work` 요청 시:
- `{doc_id}` → `"remote-work"` 자동 추출
- 해당 정책 문서 반환

---

## 핵심 정리

- **Resource** = 읽기 전용 데이터를 URI로 노출
- **Tool** = 동작(동사), **Resource** = 데이터(명사)
- `@mcp.resource("uri://scheme")` 데코레이터로 등록
- 정적 URI vs 동적 URI 템플릿
- MIME type으로 반환 형식 명시

---

## 퀴즈

1. **Tool과 Resource의 가장 큰 차이는?**
   → Tool은 동작을 수행 (부작용 가능), Resource는 읽기 전용 데이터 제공

2. **`policy://{doc_id}`에서 `{doc_id}`의 역할은?**
   → URI 템플릿 변수, 요청 시 실제 값으로 치환

---

## 다음 편 예고

### EP 11: 실전 Resource — 정책 인덱스와 상세

- `policy://index` — 전체 정책 목록
- `policy://{doc_id}` — 개별 정책 상세
- AppContext 접근 패턴
