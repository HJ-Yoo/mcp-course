# EP 07 — 실전 Tool (2) 정책 검색 (search_policy)

> Module B: Tools 심화 · 약 20분

## 학습 목표

1. Markdown 파일 기반 사내 정책 검색 Tool을 구현할 수 있다
2. YAML front-matter를 파싱하여 메타데이터를 활용할 수 있다
3. 키워드 검색과 스니펫 추출 로직을 설계할 수 있다

---

## 1. 인트로 (2분)

EP05에서 재고 조회를, EP06에서 에러 처리를 배웠습니다. 이번에는 Internal Ops Assistant의 두 번째 핵심 기능 — **사내 정책 검색**을 구현합니다.

"VPN 설정 방법이 뭐야?", "재택근무 정책이 어떻게 되지?", "비밀번호 변경 주기가 며칠이야?" 이런 질문에 답하려면 사내 정책 문서를 검색할 수 있어야 합니다. Markdown으로 작성된 정책 문서를 파싱하고, 키워드로 검색하고, 관련 스니펫을 추출하는 `search_policy` Tool을 만들어봅시다.

---

## 2. 핵심 개념 (6분)

### 2.1 정책 문서 구조

사내 정책은 Markdown 파일로 관리합니다. YAML front-matter로 메타데이터를 포함합니다:

```markdown
---
title: VPN 설정 가이드
tags: [vpn, 네트워크, 원격접속]
last_updated: 2026-01-15
author: IT보안팀
---

# VPN 설정 가이드

## 1. 사전 준비
회사 VPN에 접속하려면 다음이 필요합니다:
- 회사 이메일 계정
- 2FA 인증 앱 (Google Authenticator)
- VPN 클라이언트 (GlobalProtect)

## 2. 설치 방법
### macOS
1. Self Service에서 GlobalProtect 설치
2. 서버 주소: vpn.company.com
...
```

### 2.2 YAML front-matter 파싱

Python에서 YAML front-matter를 파싱하는 방법:

```python
import re
import yaml

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """YAML front-matter와 본문을 분리합니다."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if match:
        meta = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
        return meta, body

    return {}, content
```

### 2.3 검색 전략: 가중치 기반 랭킹

검색 결과의 관련도를 높이기 위해 가중치 기반 랭킹을 적용합니다:

| 매칭 위치 | 가중치 | 이유 |
|----------|--------|------|
| title(제목) | x3 | 문서 전체를 대표하는 키워드 |
| tags(태그) | x2 | 의도적으로 지정된 분류 |
| body(본문) | x1 | 일반적인 언급 |

```python
def calculate_relevance(query: str, meta: dict, body: str) -> float:
    query_lower = query.lower()
    score = 0.0

    # 제목 매칭 (가중치 3)
    if query_lower in meta.get("title", "").lower():
        score += 3.0

    # 태그 매칭 (가중치 2)
    tags = [t.lower() for t in meta.get("tags", [])]
    if query_lower in tags:
        score += 2.0

    # 본문 매칭 (출현 횟수 기반)
    occurrences = body.lower().count(query_lower)
    score += min(occurrences * 0.5, 3.0)  # 최대 3점

    return score
```

### 2.4 스니펫 추출

검색 키워드 주변의 텍스트를 스니펫으로 추출합니다:

```python
def extract_snippet(body: str, query: str, context_chars: int = 150) -> str:
    """키워드 주변 텍스트를 스니펫으로 추출합니다."""
    idx = body.lower().find(query.lower())
    if idx == -1:
        # 키워드가 본문에 없으면 첫 부분 반환
        return body[:context_chars * 2].strip() + "..."

    start = max(0, idx - context_chars)
    end = min(len(body), idx + len(query) + context_chars)

    snippet = body[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(body):
        snippet = snippet + "..."

    return snippet
```

---

## 3. 라이브 데모 (10분)

### Step 1: 정책 문서 생성

macOS/Linux:
```bash
mkdir -p data/policies
```

Windows (PowerShell):
```powershell
mkdir -Force data\policies
```

`data/policies/vpn-setup.md`:
```markdown
---
title: VPN 설정 가이드
tags: [vpn, 네트워크, 원격접속, 보안]
last_updated: 2026-01-15
author: IT보안팀
---

# VPN 설정 가이드

## 1. 사전 준비
회사 VPN에 접속하려면 다음이 필요합니다:
- 회사 이메일 계정
- 2FA 인증 앱 (Google Authenticator)
- VPN 클라이언트 (GlobalProtect)

## 2. macOS 설치 방법
1. Self Service 앱에서 GlobalProtect를 검색하여 설치
2. 서버 주소: vpn.company.com 입력
3. 회사 이메일과 비밀번호로 로그인
4. 2FA 코드 입력

## 3. Windows 설치 방법
1. IT 포털에서 GlobalProtect 다운로드
2. 설치 후 서버 주소: vpn.company.com 입력
3. 회사 이메일과 비밀번호로 로그인
4. 2FA 코드 입력

## 4. 문제 해결
- 연결 안 됨: 인터넷 연결 확인 후 재시도
- 인증 실패: 비밀번호 확인, 2FA 앱 시간 동기화
- 속도 느림: IT 헬프데스크에 연락 (내선 1234)
```

`data/policies/remote-work.md`:
```markdown
---
title: 재택근무 정책
tags: [재택근무, 근무제도, 복리후생]
last_updated: 2026-02-01
author: 인사팀
---

# 재택근무 정책

## 1. 대상
- 정규직 전 직원 (수습 기간 제외)
- 부서장 승인 필요

## 2. 근무 규칙
- 주 3일 출근 / 2일 재택 (하이브리드)
- 코어 타임: 10:00 - 16:00 온라인 필수
- 재택 시 VPN 연결 필수

## 3. 장비 지원
- 모니터 1대 (회사 제공)
- 키보드/마우스 세트 (회사 제공)
- 인터넷 비용 월 5만원 지원
```

### Step 2: search_policy 구현

```python
# src/tools/policy.py
import json
import re
from pathlib import Path

import yaml
from mcp.server.fastmcp import Context

from errors import ToolErrorCode, make_error


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """YAML front-matter와 본문을 분리합니다."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if match:
        meta = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
        return meta, body
    return {}, content


def calculate_relevance(query: str, meta: dict, body: str) -> float:
    """검색 관련도 점수를 계산합니다."""
    q = query.lower()
    score = 0.0
    if q in meta.get("title", "").lower():
        score += 3.0
    tags = [t.lower() for t in meta.get("tags", [])]
    if q in tags:
        score += 2.0
    occurrences = body.lower().count(q)
    score += min(occurrences * 0.5, 3.0)
    return score


def extract_snippet(body: str, query: str, context_chars: int = 150) -> str:
    """키워드 주변 텍스트를 스니펫으로 추출합니다."""
    idx = body.lower().find(query.lower())
    if idx == -1:
        return body[:context_chars * 2].strip() + "..."
    start = max(0, idx - context_chars)
    end = min(len(body), idx + len(query) + context_chars)
    snippet = body[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(body):
        snippet = snippet + "..."
    return snippet


def register_policy_tools(mcp):
    """정책 검색 Tool을 등록합니다."""

    @mcp.tool()
    async def search_policy(
        query: str,
        ctx: Context = None,
    ) -> str:
        """사내 정책 문서를 검색합니다.

        키워드를 기반으로 관련 정책 문서를 찾아 스니펫을 반환합니다.
        제목, 태그, 본문을 모두 검색하며, 관련도 순으로 정렬됩니다.

        Args:
            query: 검색 키워드 (예: "VPN", "재택근무", "비밀번호")
        """
        if not query or not query.strip():
            raise ValueError(
                make_error(
                    ToolErrorCode.INVALID_INPUT,
                    "검색어가 비어있습니다.",
                    "정책 관련 키워드를 입력해주세요. 예: 'VPN', '재택근무'",
                )
            )

        app = ctx.request_context.lifespan_context["app"]
        await ctx.info(f"정책 검색: query='{query}'")

        results = []
        for slug, content in app.policies.items():
            meta, body = parse_frontmatter(content)
            score = calculate_relevance(query, meta, body)

            if score > 0:
                results.append({
                    "slug": slug,
                    "title": meta.get("title", slug),
                    "tags": meta.get("tags", []),
                    "last_updated": meta.get("last_updated", ""),
                    "relevance_score": round(score, 1),
                    "snippet": extract_snippet(body, query),
                    "resource_uri": f"ops://policies/{slug}",
                })

        # 관련도 순 정렬
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        response = {
            "query": query,
            "total_results": len(results),
            "results": results,
        }

        if not results:
            response["suggestion"] = (
                "검색 결과가 없습니다. 다른 키워드를 시도해보세요."
            )

        await ctx.info(f"검색 완료: {len(results)}건")
        return json.dumps(response, ensure_ascii=False, indent=2)
```

### Step 3: server.py에 등록

```python
# src/server.py에 추가
from tools.policy import register_policy_tools

register_policy_tools(mcp)
```

### Step 4: 테스트

macOS/Linux:
```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

Windows (PowerShell):
```powershell
npx @modelcontextprotocol/inspector uv run python src\server.py
```

테스트:
1. `query="VPN"` → VPN 가이드 (score 5.0 이상)
2. `query="재택"` → 재택근무 정책 (score 5.0 이상)
3. `query="모니터"` → 재택근무 정책에서 장비 지원 섹션 매칭

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- Markdown + YAML front-matter로 구조화된 정책 문서를 관리한다
- **가중치 기반 랭킹**: 제목(x3) > 태그(x2) > 본문(x1)으로 관련도를 계산한다
- **스니펫 추출**: 키워드 주변 텍스트를 잘라 미리보기를 제공한다
- `resource_uri`를 포함하여 EP10-11에서 만들 Resource와 연결할 수 있다

### 퀴즈

1. **YAML front-matter의 역할은?**
   → 문서의 메타데이터(제목, 태그, 수정일, 작성자)를 구조화하여 검색과 분류에 활용.

2. **제목 매칭에 가중치를 3배로 주는 이유는?**
   → 제목은 문서 전체를 대표하므로, 제목에 키워드가 있으면 가장 관련도가 높을 가능성이 크다.

### 다음 편 예고

EP08에서는 입력 검증과 보안을 다룹니다. LLM이 생성하는 예측 불가능한 입력으로부터 서버를 보호하는 `validation.py`를 구현합니다.
