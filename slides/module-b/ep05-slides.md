---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 05 — 실전 Tool (1) 재고 조회"
---

# EP 05 — 실전 Tool (1) 재고 조회
## Module B: Tools 심화 · MCP 실전 마스터

---

## 학습 목표

1. CSV 데이터 기반 재고 조회 Tool을 구현할 수 있다
2. fuzzy 검색(키워드 매칭, 부분 일치)을 구현할 수 있다
3. LLM이 이해하기 쉬운 JSON 결과 포맷을 설계할 수 있다

---

## 데이터 소스: inventory.csv

```csv
id,name,category,stock,location,unit_price
IT-001,MacBook Pro 14",laptop,23,본사 3층,2890000
IT-002,MacBook Air 15",laptop,15,본사 3층,1990000
IT-003,Dell U2723QE 모니터,monitor,42,본사 2층,850000
IT-004,로지텍 MX Keys,keyboard,67,물류센터,159000
...
```

AppContext.load()에서 서버 시작 시 메모리에 로딩 (EP03)

---

## fuzzy 검색 전략

| 전략 | 설명 | 예시 |
|------|------|------|
| 부분 문자열 | query in name | "맥북" → "MacBook Pro" |
| 다중 필드 | name, category, location | "본사" → location 매칭 |
| 한영 매핑 | 한국어 → 영어 카테고리 | "노트북" → "laptop" |

```python
CATEGORY_MAP = {
    "노트북": "laptop",
    "모니터": "monitor",
    "키보드": "keyboard",
}
```

---

## 검색 구현

```python
def search_inventory(inventory, query, category=None):
    query_lower = query.lower()
    mapped = CATEGORY_MAP.get(query_lower, query_lower)

    results = []
    for item in inventory:
        name_match = query_lower in item["name"].lower()
        cat_match = mapped == item["category"].lower()
        loc_match = query_lower in item["location"].lower()

        if name_match or cat_match or loc_match:
            if category and item["category"] != category:
                continue
            results.append(item)
    return results
```

---

## LLM 친화적 결과 포맷

```json
{
  "query": "노트북",
  "total_results": 2,
  "items": [
    {
      "id": "IT-001",
      "name": "MacBook Pro 14\"",
      "category": "laptop",
      "stock": 23,
      "location": "본사 3층",
      "unit_price": "2,890,000원"
    }
  ]
}
```

- 쿼리 포함 (맥락 유지)
- 총 건수 명시
- 가격 포맷팅 (사람이 읽기 좋게)

---

## 결과 없음 처리

```json
{
  "query": "프린터",
  "total_results": 0,
  "items": [],
  "suggestion": "검색 결과가 없습니다. 다른 키워드를 시도해보세요."
}
```

- **에러가 아님** → 빈 배열 반환
- suggestion으로 대안 제시
- LLM이 자연스럽게 안내 가능

---

## lookup_inventory Tool

```python
@mcp.tool()
async def lookup_inventory(
    query: str,
    category: str = "",
    ctx: Context = None,
) -> str:
    """사내 재고를 검색합니다.

    Args:
        query: 검색 키워드
        category: 카테고리 필터 (비우면 전체)
    """
    app = ctx.request_context.lifespan_context["app"]
    results = search_inventory(app.inventory, query)
    return json.dumps(response, ensure_ascii=False)
```

---

## 데모: Claude Desktop 테스트

- "노트북 재고 알려줘" → MacBook Pro + MacBook Air
- "모니터 몇 대 남았어?" → Dell U2723QE: 42대
- "물류센터에 있는 장비?" → 키보드, 마우스, USB-C 허브

Claude가 JSON 결과를 자연어로 변환!

---

## 실습 과제

1. `inventory.csv`에 5개 품목 추가
2. `category` 파라미터로 필터링 기능 구현
3. 검색 결과 정렬 (재고 수량 순)
4. 재고 부족 경고 추가 (stock < 10이면 알림)

---

## 핵심 정리

- CSV → AppContext로 메모리 로딩
- **fuzzy 검색**: 부분 일치 + 다중 필드 + 한영 매핑
- **LLM 친화적 포맷**: 쿼리 포함, 총 건수, 구조화된 JSON
- **빈 결과 =/= 에러**: suggestion으로 대안 제시

---

## 퀴즈

1. 결과가 없을 때 에러 대신 빈 배열을 반환하는 이유?
   → "결과 없음"은 정상 상황. LLM이 대안을 제시할 수 있게 함.

2. CATEGORY_MAP의 역할은?
   → 한국어 키워드를 영어 카테고리로 매핑 ("노트북" → "laptop")

---

## 다음 편 예고

### EP 06: 에러 처리와 ToolError 패턴

- 프로토콜 에러 vs Tool 에러
- `isError` 필드의 의미
- 사용자 친화적 에러 메시지 설계
