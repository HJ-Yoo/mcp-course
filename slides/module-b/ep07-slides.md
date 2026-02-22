---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 07 — 실전 Tool (2) 정책 검색"
---

# EP 07 — 실전 Tool (2) 정책 검색
## Module B: Tools 심화 · MCP 실전 마스터

---

## 학습 목표

1. Markdown 파일 기반 사내 정책 검색 Tool을 구현할 수 있다
2. YAML front-matter를 파싱하여 메타데이터를 활용할 수 있다
3. 키워드 검색과 스니펫 추출 로직을 설계할 수 있다

---

## 정책 문서 구조

```markdown
---
title: VPN 설정 가이드
tags: [vpn, 네트워크, 원격접속]
last_updated: 2026-01-15
author: IT보안팀
---

# VPN 설정 가이드

## 1. 사전 준비
회사 VPN에 접속하려면...
```

YAML front-matter = 구조화된 메타데이터

---

## YAML front-matter 파싱

```python
import re, yaml

def parse_frontmatter(content: str):
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if match:
        meta = yaml.safe_load(match.group(1))
        body = match.group(2)
        return meta, body

    return {}, content
```

→ `meta` = {"title": "VPN ...", "tags": [...]}
→ `body` = Markdown 본문

---

## 가중치 기반 검색 랭킹

| 매칭 위치 | 가중치 | 이유 |
|----------|--------|------|
| title (제목) | x3 | 문서 전체 대표 |
| tags (태그) | x2 | 의도적 분류 |
| body (본문) | x1 | 일반 언급 |

```python
def calculate_relevance(query, meta, body):
    score = 0.0
    if query in meta.get("title", "").lower():
        score += 3.0
    if query in [t.lower() for t in meta.get("tags", [])]:
        score += 2.0
    score += min(body.lower().count(query) * 0.5, 3.0)
    return score
```

---

## 스니펫 추출

```python
def extract_snippet(body, query, context=150):
    idx = body.lower().find(query.lower())
    if idx == -1:
        return body[:300].strip() + "..."

    start = max(0, idx - context)
    end = min(len(body), idx + len(query) + context)
    snippet = body[start:end].strip()

    if start > 0: snippet = "..." + snippet
    if end < len(body): snippet += "..."
    return snippet
```

키워드 주변 텍스트를 잘라 미리보기 제공

---

## search_policy 구현

```python
@mcp.tool()
async def search_policy(query: str, ctx: Context) -> str:
    """사내 정책 문서를 검색합니다.

    Args:
        query: 검색 키워드 (예: "VPN", "재택근무")
    """
    results = []
    for slug, content in app.policies.items():
        meta, body = parse_frontmatter(content)
        score = calculate_relevance(query, meta, body)
        if score > 0:
            results.append({
                "slug": slug,
                "title": meta.get("title", slug),
                "relevance_score": score,
                "snippet": extract_snippet(body, query),
                "resource_uri": f"ops://policies/{slug}",
            })
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return json.dumps({"query": query, "results": results})
```

---

## 결과 예시

```json
{
  "query": "VPN",
  "total_results": 1,
  "results": [{
    "slug": "vpn-setup",
    "title": "VPN 설정 가이드",
    "relevance_score": 5.5,
    "snippet": "...회사 VPN에 접속하려면 다음이 필요합니다...",
    "resource_uri": "ops://policies/vpn-setup"
  }]
}
```

- `resource_uri`: EP10-11에서 Resource로 전체 문서 조회!

---

## 정책 문서 예시 파일

```
data/policies/
├── vpn-setup.md           # VPN 설정 가이드
├── remote-work.md         # 재택근무 정책
├── password-policy.md     # 비밀번호 정책
├── device-request.md      # 장비 신청 절차
└── security-training.md   # 보안 교육 안내
```

각 파일 = YAML front-matter + Markdown 본문

---

## 데모: 검색 테스트

Inspector에서:
1. `query="VPN"` → VPN 가이드 (score 5.0+)
2. `query="재택"` → 재택근무 정책 (score 5.0+)
3. `query="모니터"` → 재택근무 장비 지원 섹션 매칭
4. `query="출장"` → 결과 없음 (빈 배열)

---

## Tool과 Resource의 연결 고리

```
search_policy("VPN")
  → 결과에 resource_uri: "ops://policies/vpn-setup" 포함
    → LLM이 필요하면 Resource로 전체 문서 조회 (EP10-11)
```

**Tool = 검색 (찾기)**
**Resource = 상세 조회 (읽기)**

---

## 핵심 정리

- **YAML front-matter**: 문서 메타데이터 (제목, 태그, 수정일)
- **가중치 랭킹**: title(x3) > tags(x2) > body(x1)
- **스니펫 추출**: 키워드 주변 텍스트 미리보기
- `resource_uri`로 Tool → Resource 연결

---

## 퀴즈

1. YAML front-matter의 역할?
   → 제목, 태그, 수정일 등 메타데이터를 구조화하여 검색/분류에 활용

2. 제목 매칭에 가중치 3배를 주는 이유?
   → 제목은 문서 전체를 대표하므로 가장 관련도가 높음

---

## 다음 편 예고

### EP 08: 입력 검증과 보안

- LLM 입력의 보안 위험성
- Path Traversal, Injection 방어
- validation.py 4가지 핵심 함수
