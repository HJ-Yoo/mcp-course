# EP 10 — Resource 기초: 데이터를 노출하라

> Module C · 약 20분

## 학습 목표
1. Resource와 Tool의 근본적 차이를 이해한다
2. URI 스킴을 설계하고 `@mcp.resource()` 데코레이터를 사용할 수 있다
3. Resource의 MIME type과 반환 형식을 올바르게 지정할 수 있다

---

## 1. 인트로 (2분)

EP 1~9에서 우리는 Tool 중심으로 MCP 서버를 구축했습니다. `lookup_inventory`, `search_policy`, `create_ticket` — 모두 **동작(action)** 을 수행하는 도구였죠.

하지만 LLM에게 필요한 것은 동작만이 아닙니다. **데이터 그 자체**가 필요할 때가 있습니다. "이 정책 문서를 읽고 질문에 답해줘"처럼, LLM이 참고할 컨텍스트를 직접 제공해야 하는 경우입니다.

이번 편에서는 MCP의 두 번째 축인 **Resource**를 배웁니다. Resource는 읽기 전용 데이터를 URI 기반으로 노출하는 메커니즘입니다.

---

## 2. 핵심 개념 (6분)

### 2.1 Tool vs Resource: 근본적 차이

Tool과 Resource는 목적이 완전히 다릅니다.

```
┌─────────────────────────────────────────────────────┐
│              MCP 서버 구성 요소                       │
├─────────────┬───────────────────────────────────────┤
│   Tool      │  동작(Action)을 수행                   │
│             │  - 검색, 생성, 수정, 삭제              │
│             │  - LLM이 "호출"하여 결과를 받음         │
│             │  - 부작용(side effect) 가능             │
├─────────────┼───────────────────────────────────────┤
│   Resource  │  데이터(Data)를 노출                   │
│             │  - 읽기 전용, 부작용 없음              │
│             │  - LLM이 "컨텍스트"로 활용             │
│             │  - URI로 식별                          │
└─────────────┴───────────────────────────────────────┘
```

핵심 비유: Tool은 **동사**(검색하다, 생성하다), Resource는 **명사**(정책 문서, 재고 현황)입니다.

### 2.2 URI 스킴 설계

Resource는 URI(Uniform Resource Identifier)로 식별됩니다. MCP에서는 커스텀 URI 스킴을 자유롭게 설계할 수 있습니다.

```
policy://index              → 모든 정책 문서 목록
policy://{doc_id}           → 특정 정책 문서 상세
inventory://status          → 재고 현황 요약
inventory://{item_id}       → 특정 재고 아이템 상세
config://server             → 서버 설정 정보
```

**URI 설계 원칙**:
- 직관적인 스킴명 사용 (도메인을 반영)
- 정적 URI는 고정 문자열 (`policy://index`)
- 동적 URI는 템플릿 변수 사용 (`policy://{doc_id}`)
- 계층 구조를 반영 (`inventory://category/{cat}/items`)

### 2.3 @mcp.resource() 데코레이터

FastMCP에서 Resource를 등록하는 방법은 간단합니다:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.resource("time://now")
async def get_current_time() -> str:
    """현재 서버 시간을 반환합니다."""
    from datetime import datetime
    return datetime.now().isoformat()
```

데코레이터에 URI를 지정하면 MCP 클라이언트가 해당 URI로 데이터를 요청할 수 있습니다.

### 2.4 MIME Type 지정

Resource는 다양한 형식의 데이터를 반환할 수 있습니다:

```python
@mcp.resource("policy://index", mime_type="application/json")
async def policy_index() -> str:
    return json.dumps(policies_list)

@mcp.resource("docs://readme", mime_type="text/markdown")
async def readme() -> str:
    return "# 프로젝트 README\n..."

@mcp.resource("config://server", mime_type="text/plain")
async def server_config() -> str:
    return "version=1.0\nport=8000"
```

### 2.5 Resource vs Tool 선택 기준

언제 Resource를 쓰고, 언제 Tool을 써야 할까요?

```
                    시작
                      │
              데이터를 변경하는가?
                   /       \
                 Yes        No
                  │          │
              → Tool     파라미터가 복잡한가?
                          /        \
                        Yes         No
                         │           │
                     → Tool      데이터가 정적인가?
                                  /        \
                                Yes         No
                                 │           │
                           → Resource    → Resource
                             (정적)       (동적 템플릿)
```

**Resource를 선택하는 경우**:
- 읽기 전용 데이터
- LLM이 컨텍스트로 참고해야 하는 문서
- 설정, 상태 정보
- 목록, 인덱스 정보

**Tool을 선택하는 경우**:
- 데이터 변경 (생성, 수정, 삭제)
- 복잡한 검색 파라미터
- 외부 API 호출
- 부작용이 있는 동작

---

## 3. 라이브 데모 (10분)

### Step 1: 간단한 Resource 서버 만들기

프로젝트 디렉토리에서 작업합니다.

macOS/Linux:
```bash
cd ~/mcp-course/acme-ops-assistant
```

Windows (PowerShell):
```powershell
cd $HOME\mcp-course\acme-ops-assistant
```

`src/resources/demo_resource.py` 파일을 생성합니다:

```python
"""데모용 Resource 모듈 — Resource의 기본 동작을 확인합니다."""

import json
from datetime import datetime


def register(mcp):
    """MCP 서버에 데모 Resource를 등록합니다."""

    @mcp.resource("time://now")
    async def get_current_time() -> str:
        """현재 서버 시간을 ISO 형식으로 반환합니다."""
        return datetime.now().isoformat()

    @mcp.resource("server://info", mime_type="application/json")
    async def server_info() -> str:
        """서버 기본 정보를 JSON으로 반환합니다."""
        info = {
            "name": "Acme Internal Ops Assistant",
            "version": "1.0.0",
            "tools": ["lookup_inventory", "search_policy", "create_ticket"],
            "resources": ["time://now", "server://info"],
        }
        return json.dumps(info, indent=2)
```

### Step 2: 서버에 Resource 등록

`src/server.py`에서 Resource 모듈을 import합니다:

```python
from resources import demo_resource

# ... lifespan 등 기존 코드 ...

demo_resource.register(mcp)
```

### Step 3: MCP Inspector에서 확인

macOS/Linux:
```bash
uv run mcp dev src/server.py
```

Windows (PowerShell):
```powershell
uv run mcp dev src\server.py
```

Inspector가 열리면:
1. 좌측 메뉴에서 **Resources** 탭 클릭
2. `time://now` 선택 → 현재 시간이 반환되는지 확인
3. `server://info` 선택 → JSON 정보가 표시되는지 확인

### Step 4: Claude Desktop에서 Resource 활용

Claude Desktop에서는 Resource를 **첨부(attach)** 하여 대화 컨텍스트에 포함시킬 수 있습니다.

1. Claude Desktop 대화창에서 클립 아이콘 (또는 `/`) 클릭
2. MCP 서버의 Resource 목록이 표시됨
3. `server://info` 선택 → 서버 정보가 컨텍스트에 추가됨
4. "이 서버에서 사용할 수 있는 도구를 설명해줘"라고 입력

LLM은 Resource 데이터를 참고하여 정확한 답변을 생성합니다.

### Step 5: 동적 URI 템플릿 미리보기

다음 편(EP 11)에서 구현할 동적 Resource의 미리보기입니다:

```python
@mcp.resource("policy://{doc_id}")
async def policy_detail(doc_id: str) -> str:
    """특정 정책 문서의 내용을 반환합니다."""
    # doc_id가 URI에서 자동으로 추출됩니다
    policy = find_policy(doc_id)
    return policy.content
```

URI 템플릿의 `{doc_id}` 부분은 클라이언트가 요청할 때 실제 값으로 치환됩니다. 예: `policy://remote-work` → `doc_id = "remote-work"`

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- Resource는 읽기 전용 데이터를 URI로 노출하는 MCP 구성 요소
- Tool은 동작(동사), Resource는 데이터(명사)
- `@mcp.resource("uri://scheme")` 데코레이터로 등록
- 정적 URI (`policy://index`)와 동적 URI 템플릿 (`policy://{doc_id}`)이 있음
- MIME type으로 반환 형식을 명시할 수 있음

### 퀴즈
1. Tool과 Resource의 가장 큰 차이는? → Tool은 동작을 수행하고 부작용이 있을 수 있지만, Resource는 읽기 전용 데이터를 제공하며 부작용이 없다
2. `policy://{doc_id}`에서 `{doc_id}`는 어떤 역할? → URI 템플릿 변수로, 클라이언트 요청 시 실제 값으로 치환되어 함수 파라미터로 전달된다
3. Resource의 MIME type을 지정하지 않으면 기본값은? → `text/plain`

### 다음 편 예고
EP 11에서는 Acme Corp 프로젝트에 **실전 Resource**를 구현합니다. `policy://index`로 전체 정책 목록을, `policy://{doc_id}`로 개별 정책 상세를 노출하여 LLM이 정책 문서를 컨텍스트로 활용할 수 있게 만듭니다.
