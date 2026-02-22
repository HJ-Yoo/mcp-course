---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 11 — 실전 Resource: 정책 인덱스와 상세"
---

# EP 11 — 실전 Resource: 정책 인덱스와 상세
## Module C · MCP 실전 마스터

---

## 학습 목표

1. 정적 Resource (`policy://index`)와 동적 Resource (`policy://{doc_id}`) 구현
2. Resource에서 AppContext에 접근하는 패턴
3. Resource 데이터를 LLM이 컨텍스트로 활용하는 시나리오

---

## 정적 vs 동적 Resource

| 구분 | 정적 Resource | 동적 Resource |
|------|--------------|--------------|
| URI | 고정 (`policy://index`) | 변수 포함 (`policy://{doc_id}`) |
| 데이터 | 항상 같은 구조 | 요청에 따라 다름 |
| 용도 | 목록, 요약, 상태 | 상세 조회 |
| 예시 | 전체 정책 목록 | 특정 정책 본문 |

---

## AppContext 접근 패턴

```python
@mcp.resource("policy://index")
async def policy_index() -> str:
    # 1. 현재 컨텍스트 가져오기
    ctx = mcp.get_context()

    # 2. lifespan에서 설정한 AppContext 접근
    app = ctx.request_context.lifespan_context["app"]

    # 3. 데이터 사용
    return json.dumps([...for p in app.policies])
```

**lifespan → AppContext → Resource 함수** 의 데이터 흐름

---

## 정적 Resource: policy://index

```python
@mcp.resource("policy://index", mime_type="application/json")
async def policy_index() -> str:
    ctx = mcp.get_context()
    app = ctx.request_context.lifespan_context["app"]

    index = [
        {
            "doc_id": p.doc_id,
            "title": p.title,
            "tags": p.tags,
        }
        for p in app.policies
    ]
    return json.dumps(index, ensure_ascii=False, indent=2)
```

핵심 메타데이터만 포함 (본문 제외 → 토큰 절약)

---

## 동적 Resource: policy://{doc_id}

```python
@mcp.resource("policy://{doc_id}", mime_type="application/json")
async def policy_detail(doc_id: str) -> str:
    ctx = mcp.get_context()
    app = ctx.request_context.lifespan_context["app"]

    policy = next(
        (p for p in app.policies if p.doc_id == doc_id),
        None,
    )
    if policy is None:
        return json.dumps({"error": f"'{doc_id}' not found"})

    return json.dumps({
        "doc_id": policy.doc_id,
        "title": policy.title,
        "content": policy.content,  # 전체 본문 포함
    }, ensure_ascii=False, indent=2)
```

---

## JSON 직렬화 전략

**목록 (index)** — 핵심 정보만:
```json
[
  {"doc_id": "remote-work", "title": "원격근무 정책",
   "tags": ["remote", "wfh"]}
]
```

**상세 (detail)** — 전체 내용:
```json
{
  "doc_id": "remote-work",
  "title": "원격근무 정책",
  "content": "# 원격근무 정책\n\n## 1. 적용 범위\n...",
  "last_updated": "2026-01-15"
}
```

---

## Resource의 LLM 활용 흐름

```
사용자: "원격근무 정책에서 해외 근무가 가능한지 알려줘"

LLM 동작:
  1. policy://index → "remote-work" doc_id 확인
  2. policy://remote-work → 전체 정책 내용 로드
  3. 정책 내용을 컨텍스트로 참고하여 답변 생성
```

Resource = LLM의 "참고 자료"

---

## 데모: Inspector에서 테스트

```bash
uv run mcp dev src/server.py
```

1. **Resources** → `policy://index` → 5개 정책 목록 확인
2. `policy://remote-work` 입력 → 정책 전체 내용 확인
3. `policy://nonexistent` → 에러 JSON 확인

---

## 데모: Claude Desktop 시나리오

**시나리오 1:**
"우리 회사에 어떤 정책 문서가 있어?"
→ `policy://index` 참조

**시나리오 2:**
"원격근무 정책 내용을 보고 요약해줘"
→ `policy://remote-work` 컨텍스트 로드

**시나리오 3:**
"보안 정책에 따르면 개인 USB를 사용해도 되나요?"
→ `policy://security` 참고하여 정확한 답변

---

## Tool + Resource 시너지

```
"원격근무 정책을 확인하고, 관련 장비가 재고에 있는지 검색해줘"

LLM 동작:
  1. policy://remote-work → 정책 내용 확인
  2. 정책에서 필요 장비 파악 (노트북, 모니터)
  3. lookup_inventory Tool → 해당 장비 재고 검색
  4. 종합 답변 생성
```

**Resource와 Tool의 유기적 협업**

---

## 핵심 정리

- 정적 Resource: 고정 URI, 목록/요약 데이터
- 동적 Resource: URI 템플릿, 상세 데이터
- AppContext 접근: `mcp.get_context().request_context.lifespan_context["app"]`
- Resource = LLM의 컨텍스트 → 정확한 답변
- Tool + Resource 조합 → 강력한 워크플로우

---

## 다음 편 예고

### EP 12: Resource 보안 — Path Traversal 방지

- `policy://../../etc/passwd` 공격 방어
- `validate_doc_id()` 구현
- Defense in depth 원칙
