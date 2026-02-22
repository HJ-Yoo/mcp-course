# EP 12 — Resource 보안: Path Traversal 방지

> Module C · 약 20분

## 학습 목표
1. Path traversal 공격의 원리와 위험성을 이해한다
2. `validate_doc_id()` 방어 코드를 구현하고 테스트한다
3. Defense in depth(심층 방어) 원칙을 적용한다

---

## 1. 인트로 (2분)

EP 11에서 `policy://{doc_id}` 동적 Resource를 만들었습니다. 사용자가 `policy://remote-work`를 요청하면 원격근무 정책을 반환합니다. 깔끔하죠.

하지만 만약 누군가 `policy://../../etc/passwd`를 요청하면 어떻게 될까요?

이것이 **Path Traversal(경로 탐색) 공격**입니다. 웹 보안의 OWASP Top 10에 꾸준히 등장하는 취약점이며, MCP 서버에서도 동일한 위험이 존재합니다. 특히 LLM이 악의적 프롬프트 인젝션에 의해 이런 URI를 생성할 수 있다는 점이 MCP 특유의 위험입니다.

---

## 2. 핵심 개념 (6분)

### 2.1 Path Traversal 공격이란?

Path traversal은 파일 경로를 조작하여 허가되지 않은 파일에 접근하는 공격입니다.

```
의도된 경로:  /data/policies/remote-work.md
공격 경로:    /data/policies/../../etc/passwd
해석 결과:    /etc/passwd  ← 시스템 파일 유출!
```

`..`는 "상위 디렉토리"를 의미합니다. 충분한 `../`를 반복하면 파일 시스템 어디든 접근할 수 있습니다.

**MCP에서의 위험 시나리오**:

```
┌──────────────────────────────────────────────────────┐
│  1. 공격자가 악의적 프롬프트 작성                       │
│     "정책 문서 policy://../../etc/passwd를 읽어줘"     │
│                          │                            │
│  2. LLM이 프롬프트 인젝션에 의해                       │
│     policy://../../etc/passwd Resource 요청            │
│                          │                            │
│  3. MCP 서버가 검증 없이                               │
│     /data/policies/../../etc/passwd 파일 읽기 시도      │
│                          │                            │
│  4. 시스템 파일 내용이 LLM 응답으로 유출                │
└──────────────────────────────────────────────────────┘
```

### 2.2 공격 변형 패턴

공격자는 다양한 우회 기법을 사용합니다:

| 패턴 | 설명 |
|------|------|
| `../../../etc/passwd` | 기본 path traversal |
| `....//....//etc/passwd` | 단순 `../` 필터 우회 |
| `%2e%2e%2f` | URL 인코딩으로 우회 |
| `..%252f..%252f` | 이중 URL 인코딩 |
| `..\/..\/` | 역슬래시 혼합 |
| `....\/....\/` | 슬래시 변형 |
| `%00.md` | Null byte injection |

### 2.3 방어 전략: validate_doc_id()

첫 번째 방어선 — **입력값 화이트리스트 검증**:

```python
import re

def validate_doc_id(doc_id: str) -> str:
    """doc_id가 안전한 형식인지 검증합니다.

    허용: 알파벳 소문자, 숫자, 하이픈(-)만 가능
    길이: 1~50자

    Raises:
        ValueError: 유효하지 않은 doc_id
    """
    pattern = r'^[a-z0-9\-]{1,50}$'
    if not re.match(pattern, doc_id):
        raise ValueError(
            f"Invalid doc_id: '{doc_id}'. "
            "Only lowercase letters, numbers, and hyphens allowed."
        )
    return doc_id
```

**화이트리스트 접근법**: "허용할 것을 명시"하는 것이 "차단할 것을 명시"하는 것보다 안전합니다.

- 화이트리스트: `[a-z0-9\-]`만 허용 (안전)
- 블랙리스트: `../`를 차단 (우회 가능성 있음)

### 2.4 Defense in Depth: 경로 확인

두 번째 방어선 — **resolved path 검증**:

```python
from pathlib import Path

def safe_resolve_policy_path(doc_id: str, policy_dir: Path) -> Path:
    """정책 파일 경로를 안전하게 resolve합니다.

    resolved path가 policy_dir 내부인지 확인합니다.
    """
    # 1차 방어: doc_id 형식 검증
    validate_doc_id(doc_id)

    # 2차 방어: resolved path가 허용 디렉토리 내부인지 확인
    file_path = (policy_dir / f"{doc_id}.md").resolve()
    policy_dir_resolved = policy_dir.resolve()

    if not str(file_path).startswith(str(policy_dir_resolved)):
        raise ValueError(
            f"Path traversal detected: '{doc_id}' resolves outside policy directory"
        )

    return file_path
```

**심층 방어(Defense in Depth)** 원칙:

```
┌─────────────────────────────────────┐
│  Layer 1: 입력 형식 검증            │  ← validate_doc_id()
│  ┌─────────────────────────────┐    │
│  │  Layer 2: 경로 resolve 검증 │    │  ← safe_resolve_policy_path()
│  │  ┌─────────────────────┐    │    │
│  │  │  Layer 3: OS 권한   │    │    │  ← 파일 시스템 권한
│  │  └─────────────────────┘    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

하나의 방어선이 뚫려도 다음 방어선이 막아줍니다.

---

## 3. 라이브 데모 (10분)

### Step 1: 취약한 코드 확인

EP 11에서 작성한 `policy_detail`에는 검증이 없습니다:

```python
# 취약한 코드 (EP 11 버전)
@mcp.resource("policy://{doc_id}")
async def policy_detail(doc_id: str) -> str:
    # doc_id를 검증하지 않음 — 위험!
    policy = next((p for p in app.policies if p.doc_id == doc_id), None)
    ...
```

현재 코드는 `app.policies` 리스트에서 매칭하기 때문에 직접적인 파일 읽기 위험은 낮지만, 코드가 발전하면서 파일 시스템 접근이 추가될 수 있습니다. 방어는 미리 해야 합니다.

### Step 2: validate_doc_id 구현

`src/validation.py`에 추가합니다:

```python
import re


def validate_doc_id(doc_id: str) -> str:
    """정책 문서 ID를 검증합니다.

    허용: 소문자 알파벳, 숫자, 하이픈만 가능 (1~50자)

    Args:
        doc_id: 검증할 문서 ID

    Returns:
        검증된 doc_id

    Raises:
        ValueError: 유효하지 않은 형식
    """
    if not isinstance(doc_id, str):
        raise ValueError(f"doc_id must be a string, got {type(doc_id).__name__}")

    pattern = r'^[a-z0-9]([a-z0-9\-]{0,48}[a-z0-9])?$'
    if not re.match(pattern, doc_id):
        raise ValueError(
            f"Invalid doc_id: '{doc_id}'. "
            "Must be 1-50 chars, lowercase alphanumeric and hyphens only, "
            "cannot start or end with a hyphen."
        )
    return doc_id
```

### Step 3: Resource에 검증 적용

`src/resources/policy_resource.py`를 수정합니다:

```python
"""정책 문서 Resource — 보안 검증 포함"""

import json
from validation import validate_doc_id


def register(mcp):

    @mcp.resource("policy://index", mime_type="application/json")
    async def policy_index() -> str:
        # ... (EP 11과 동일)
        pass

    @mcp.resource("policy://{doc_id}", mime_type="application/json")
    async def policy_detail(doc_id: str) -> str:
        """특정 정책 문서의 전체 내용을 반환합니다."""
        ctx = mcp.get_context()
        app = ctx.request_context.lifespan_context["app"]

        # 보안 검증 추가!
        try:
            validate_doc_id(doc_id)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

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

### Step 4: 보안 테스트 작성

`tests/test_security.py`:

```python
"""Resource 보안 테스트 — Path Traversal 방어 검증"""

import pytest
from validation import validate_doc_id


class TestValidateDocId:
    """validate_doc_id 함수 테스트"""

    # 유효한 입력
    @pytest.mark.parametrize("valid_id", [
        "remote-work",
        "security",
        "equipment-management",
        "a",
        "abc123",
        "policy-v2",
    ])
    def test_valid_doc_ids(self, valid_id):
        assert validate_doc_id(valid_id) == valid_id

    # Path traversal 공격 패턴
    @pytest.mark.parametrize("malicious_id", [
        "../../../etc/passwd",
        "....//....//etc/passwd",
        "%2e%2e%2fetc%2fpasswd",
        "..\\..\\windows\\system32",
        "remote-work/../../etc/passwd",
        ".",
        "..",
        "/etc/passwd",
        "remote-work\x00.md",
    ])
    def test_path_traversal_blocked(self, malicious_id):
        with pytest.raises(ValueError):
            validate_doc_id(malicious_id)

    # 형식 위반
    @pytest.mark.parametrize("invalid_id", [
        "",                          # 빈 문자열
        "UPPERCASE",                 # 대문자
        "has space",                 # 공백
        "special!char",              # 특수문자
        "-starts-with-hyphen",       # 하이픈으로 시작
        "ends-with-hyphen-",         # 하이픈으로 끝남
        "a" * 51,                    # 51자 (초과)
    ])
    def test_invalid_format_rejected(self, invalid_id):
        with pytest.raises(ValueError):
            validate_doc_id(invalid_id)

    def test_non_string_input(self):
        with pytest.raises(ValueError):
            validate_doc_id(123)

        with pytest.raises(ValueError):
            validate_doc_id(None)
```

### Step 5: 테스트 실행

macOS/Linux:
```bash
uv run pytest tests/test_security.py -v
```

Windows (PowerShell):
```powershell
uv run pytest tests\test_security.py -v
```

예상 출력:
```
tests/test_security.py::TestValidateDocId::test_valid_doc_ids[remote-work] PASSED
tests/test_security.py::TestValidateDocId::test_valid_doc_ids[security] PASSED
tests/test_security.py::TestValidateDocId::test_path_traversal_blocked[../../../etc/passwd] PASSED
tests/test_security.py::TestValidateDocId::test_path_traversal_blocked[....//....//etc/passwd] PASSED
...
==================== 17 passed in 0.05s ====================
```

모든 악의적 패턴이 차단되는 것을 확인합니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리
- Path traversal은 `../`를 이용해 허가되지 않은 파일에 접근하는 공격
- LLM이 프롬프트 인젝션에 의해 악의적 URI를 생성할 수 있어 MCP에서 특히 중요
- 화이트리스트 기반 검증 (`[a-z0-9\-]`만 허용)이 블랙리스트보다 안전
- Defense in depth: 입력 검증 + 경로 resolve 검증 + OS 권한의 다중 방어선
- 보안 테스트는 공격 패턴 목록을 parametrize로 체계적으로 검증

### 퀴즈
1. 화이트리스트 검증이 블랙리스트 검증보다 안전한 이유는? → 블랙리스트는 알려진 공격만 차단하지만, 화이트리스트는 허용된 것만 통과시키므로 미지의 공격도 차단된다
2. `validate_doc_id()`가 하이픈으로 시작/끝나는 것을 막는 이유는? → 하이픈이 시작/끝에 있으면 파일 시스템이나 CLI에서 옵션 플래그로 오인될 수 있고, 의도치 않은 동작을 유발할 수 있다
3. Defense in depth의 핵심 원리는? → 단일 방어선에 의존하지 않고, 여러 레이어의 방어를 중첩하여 하나가 뚫려도 다음 방어선이 보호한다

### 다음 편 예고
EP 13에서는 MCP의 세 번째 구성 요소인 **Prompt Template**을 배웁니다. `@mcp.prompt()`로 재사용 가능한 LLM 지시문을 만들고, Resource와 Prompt를 조합하여 "정책 문서 기반 질문 답변" 워크플로우를 완성합니다.
