# EP 11 — 실전 Resource: 정책 인덱스와 상세

> Module C · 약 20분

## 학습 목표
1. 정적 Resource (`policy://index`)와 동적 Resource (`policy://{doc_id}`)를 구현한다
2. Resource에서 AppContext에 접근하는 패턴을 익힌다
3. Resource 데이터를 LLM이 컨텍스트로 활용하는 실전 시나리오를 경험한다

---

## 1. 인트로 (2분)

EP 10에서 Resource의 개념과 `@mcp.resource()` 데코레이터를 배웠습니다. 이제 실전입니다.

Acme Corp의 Internal Ops Assistant에는 5개의 정책 문서가 있습니다 — 원격근무, 보안, 장비 관리, 휴가, 비용 처리 정책. 지금까지는 `search_policy` Tool로만 검색할 수 있었지만, 이번 편에서는 **Resource**로 정책 데이터를 직접 노출합니다.

Resource로 노출하면 LLM이 정책 문서 전체를 컨텍스트에 포함시켜 "이 정책을 읽고 질문에 답해줘"가 가능해집니다. Tool 검색은 키워드 매칭이지만, Resource는 전문(full text) 제공입니다.

---

## 2. 핵심 개념 (6분)

### 2.1 정적 Resource vs 동적 Resource

```
정적 Resource                     동적 Resource
─────────────                     ─────────────
URI가 고정됨                       URI에 변수가 있음
policy://index                    policy://{doc_id}
항상 같은 구조의 데이터 반환        요청 파라미터에 따라 다른 데이터
목록, 요약, 상태 정보에 적합        상세 조회에 적합
```

**정적 Resource** — `policy://index`:
- 모든 정책 문서의 목록을 반환
- doc_id, title, tags 정보를 JSON 배열로 제공
- LLM이 "어떤 정책이 있는지" 파악하는 데 사용

**동적 Resource** — `policy://{doc_id}`:
- 특정 정책 문서의 전체 내용을 반환
- URI에서 `doc_id`를 추출하여 해당 문서를 찾음
- LLM이 "이 정책의 내용"을 읽는 데 사용

### 2.2 AppContext 접근 패턴

Resource 함수 내에서 서버의 공유 상태(AppContext)에 접근해야 합니다. EP 5~6에서 설정한 lifespan 패턴을 기억하세요:

```python
# lifespan에서 AppContext 생성 → lifespan_context에 저장
@asynccontextmanager
async def app_lifespan(server):
    app = AppContext(...)
    yield {"app": app}

# Resource에서 AppContext 접근
@mcp.resource("policy://index")
async def policy_index() -> str:
    ctx = mcp.get_context()
    app = ctx.request_context.lifespan_context["app"]
    # app.policies 사용
```

`mcp.get_context()`는 현재 요청의 컨텍스트를 반환합니다. 여기서 `lifespan_context`를 통해 서버 시작 시 초기화된 AppContext에 접근합니다.

### 2.3 JSON 직렬화 전략

Resource가 반환하는 데이터 형식은 용도에 따라 다릅니다:

**목록 (index)** — 핵심 정보만 포함:
```json
[
  {"doc_id": "remote-work", "title": "원격근무 정책", "tags": ["remote", "wfh"]},
  {"doc_id": "security", "title": "보안 정책", "tags": ["security", "compliance"]}
]
```

**상세 (detail)** — 전체 내용 포함:
```json
{
  "doc_id": "remote-work",
  "title": "원격근무 정책",
  "tags": ["remote", "wfh"],
  "content": "# 원격근무 정책\n\n## 1. 적용 범위\n...",
  "last_updated": "2026-01-15"
}
```

### 2.4 Resource 결과의 LLM 활용

Resource가 진정한 가치를 발휘하는 순간은 LLM이 이를 **컨텍스트**로 사용할 때입니다:

```
사용자: "원격근무 정책에서 해외 근무가 가능한지 알려줘"

LLM의 동작:
1. policy://index에서 "remote-work" doc_id 확인
2. policy://remote-work에서 전체 정책 내용 로드
3. 정책 내용을 컨텍스트로 참고하여 답변 생성
```

이 패턴은 RAG(Retrieval-Augmented Generation)와 유사하지만, MCP Resource를 통해 표준화된 방식으로 구현됩니다.

---

## 3. 라이브 데모 (10분)

### Step 1: Resource 모듈 생성

`src/resources/policy_resource.py` 파일을 생성합니다:

```python
"""정책 문서 Resource — policy://index, policy://{doc_id}"""

import json


def register(mcp):
    """MCP 서버에 정책 Resource를 등록합니다."""

    @mcp.resource("policy://index", mime_type="application/json")
    async def policy_index() -> str:
        """모든 정책 문서의 목록을 반환합니다.

        각 정책의 doc_id, title, tags를 JSON 배열로 제공합니다.
        LLM이 사용 가능한 정책 문서를 파악하는 데 활용됩니다.
        """
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

    @mcp.resource("policy://{doc_id}", mime_type="application/json")
    async def policy_detail(doc_id: str) -> str:
        """특정 정책 문서의 전체 내용을 반환합니다.

        Args:
            doc_id: 정책 문서 식별자 (예: remote-work, security)
        """
        ctx = mcp.get_context()
        app = ctx.request_context.lifespan_context["app"]

        # EP 12에서 validate_doc_id()를 추가할 예정
        policy = next((p for p in app.policies if p.doc_id == doc_id), None)

        if policy is None:
            return json.dumps(
                {"error": f"Policy '{doc_id}' not found"},
                ensure_ascii=False,
            )

        detail = {
            "doc_id": policy.doc_id,
            "title": policy.title,
            "tags": policy.tags,
            "content": policy.content,
            "last_updated": policy.last_updated,
        }
        return json.dumps(detail, ensure_ascii=False, indent=2)
```

### Step 2: 서버에 등록

`src/server.py`에 Resource 모듈을 추가합니다:

```python
from resources import policy_resource

# ... 기존 tool 등록 코드 아래에 추가 ...
policy_resource.register(mcp)
```

### Step 3: MCP Inspector에서 테스트

macOS/Linux:
```bash
uv run mcp dev src/server.py
```

Windows (PowerShell):
```powershell
uv run mcp dev src\server.py
```

Inspector에서 확인할 것:
1. **Resources** 탭 → `policy://index` 클릭 → 5개 정책 목록이 JSON으로 표시
2. 목록에서 `doc_id` 확인 (예: `remote-work`)
3. **Resources** 탭 → URI 입력란에 `policy://remote-work` 입력 → 정책 전체 내용 표시
4. 존재하지 않는 ID 테스트: `policy://nonexistent` → 에러 JSON 반환

### Step 4: Claude Desktop에서 실전 테스트

Claude Desktop을 재시작하고 다음 시나리오를 테스트합니다:

**시나리오 1: 정책 목록 확인**
```
"우리 회사에 어떤 정책 문서가 있어?"
```
→ LLM이 `policy://index` Resource를 참조하여 목록 제공

**시나리오 2: 정책 내용 기반 질문 답변**
```
"원격근무 정책 내용을 보고 요약해줘"
```
→ LLM이 `policy://remote-work` Resource를 컨텍스트로 로드 후 요약

**시나리오 3: 정책 기반 판단**
```
"보안 정책에 따르면 개인 USB를 사용해도 되나요?"
```
→ LLM이 `policy://security` Resource를 참고하여 정확한 답변

### Step 5: Tool과 Resource의 협업 확인

Resource와 Tool을 함께 사용하는 복합 시나리오:

```
"원격근무 정책을 확인하고, 관련 장비가 재고에 있는지 검색해줘"
```

LLM의 동작:
1. `policy://remote-work` Resource로 정책 내용 확인
2. 정책에서 필요 장비 파악 (노트북, 모니터 등)
3. `lookup_inventory` Tool로 해당 장비 재고 검색
4. 종합 답변 생성

이것이 Resource와 Tool의 시너지입니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- 정적 Resource (`policy://index`)는 고정 URI로 목록/요약 데이터를 제공
- 동적 Resource (`policy://{doc_id}`)는 URI 템플릿으로 상세 데이터를 제공
- AppContext 접근: `mcp.get_context().request_context.lifespan_context["app"]`
- Resource는 LLM의 컨텍스트로 활용되어 정확한 답변 생성에 기여
- Tool과 Resource를 함께 사용하면 더 강력한 워크플로우 구성 가능

### 퀴즈
1. `policy://index`가 반환하는 데이터에 정책 본문(content)을 포함하지 않는 이유는? → 목록 Resource는 핵심 메타데이터만 제공하여 토큰을 절약하고, 본문은 상세 Resource에서 필요할 때만 로드한다
2. Resource에서 AppContext에 접근하는 코드를 작성하시오 → `ctx = mcp.get_context(); app = ctx.request_context.lifespan_context["app"]`
3. 존재하지 않는 doc_id가 요청되면 어떻게 처리해야 하는가? → 에러 JSON을 반환하여 클라이언트가 상황을 파악할 수 있게 한다

### 다음 편 예고
EP 12에서는 Resource의 **보안**을 다룹니다. `policy://{doc_id}`의 `doc_id` 파라미터에 `../../../etc/passwd` 같은 악의적 입력이 들어올 수 있습니다. Path traversal 공격을 이해하고 방어 코드를 구현합니다.
