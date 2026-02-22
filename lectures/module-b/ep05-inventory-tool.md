# EP 05 — 실전 Tool (1) 재고 조회 (lookup_inventory)

> Module B: Tools 심화 · 약 20분

## 학습 목표

1. CSV 데이터를 기반으로 재고 조회 Tool을 구현할 수 있다
2. fuzzy 검색(키워드 매칭, 부분 일치)을 구현할 수 있다
3. LLM이 이해하기 쉬운 JSON 결과 포맷을 설계할 수 있다

---

## 1. 인트로 (2분)

EP04에서 Tool의 기초를 배웠습니다. 이제 캡스톤 프로젝트 Internal Ops Assistant의 첫 번째 실전 Tool을 만들 차례입니다.

사내 IT 운영팀의 가장 흔한 질문 중 하나: **"XX 장비 재고가 몇 개야?"** 이 질문에 답하는 `lookup_inventory` Tool을 구현합니다. CSV 파일에서 데이터를 읽고, 키워드로 검색하고, 깔끔한 결과를 반환하는 전체 과정을 다룹니다.

---

## 2. 핵심 개념 (6분)

### 2.1 데이터 소스: inventory.csv

재고 데이터는 CSV 파일로 관리합니다:

```csv
id,name,category,stock,location,unit_price
IT-001,MacBook Pro 14",laptop,23,본사 3층,2890000
IT-002,MacBook Air 15",laptop,15,본사 3층,1990000
IT-003,Dell U2723QE 모니터,monitor,42,본사 2층,850000
IT-004,로지텍 MX Keys,keyboard,67,물류센터,159000
IT-005,로지텍 MX Master 3S,mouse,54,물류센터,139000
IT-006,삼성 870 EVO 1TB,storage,31,본사 2층,129000
IT-007,AirPods Pro,audio,18,본사 3층,359000
IT-008,USB-C 허브 7포트,accessory,89,물류센터,69000
```

EP03에서 만든 `AppContext.load()`가 이 CSV를 서버 시작 시 메모리에 로딩합니다.

### 2.2 fuzzy 검색 구현

사용자가 정확한 상품명을 모를 수 있습니다. "맥북"이라고 검색해도 "MacBook Pro 14\""를 찾아야 합니다. 이를 위해 fuzzy 검색을 구현합니다:

**전략 1: 부분 문자열 매칭**
```python
query.lower() in item["name"].lower()
```

**전략 2: 다중 필드 검색**
- name 필드
- category 필드
- location 필드

**전략 3: 한영 매칭 (보너스)**
- "키보드" → "keyboard" 카테고리 매칭

### 2.3 결과 포맷팅: LLM 친화적 JSON

LLM에게 결과를 전달할 때 포맷이 중요합니다:

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
    },
    {
      "id": "IT-002",
      "name": "MacBook Air 15\"",
      "category": "laptop",
      "stock": 15,
      "location": "본사 3층",
      "unit_price": "1,990,000원"
    }
  ]
}
```

포맷팅 원칙:
- 검색 쿼리를 결과에 포함 (맥락 유지)
- 총 결과 수 명시
- 가격은 사람이 읽기 좋은 형태로 포맷
- 재고 수량은 숫자로 유지 (LLM이 비교/계산에 사용)

### 2.4 검색 결과가 없을 때

결과가 없을 때 에러를 던지지 않고 빈 결과를 반환합니다:

```json
{
  "query": "프린터",
  "total_results": 0,
  "items": [],
  "suggestion": "검색어를 변경해보세요. 예: laptop, monitor, keyboard"
}
```

에러는 시스템 문제일 때, 빈 결과는 데이터가 없을 때 사용합니다 (EP06에서 상세히 다룸).

---

## 3. 라이브 데모 (10분)

### Step 1: inventory.csv 생성

macOS/Linux:
```bash
mkdir -p data
cat > data/inventory.csv << 'EOF'
id,name,category,stock,location,unit_price
IT-001,MacBook Pro 14",laptop,23,본사 3층,2890000
IT-002,MacBook Air 15",laptop,15,본사 3층,1990000
IT-003,Dell U2723QE 모니터,monitor,42,본사 2층,850000
IT-004,로지텍 MX Keys,keyboard,67,물류센터,159000
IT-005,로지텍 MX Master 3S,mouse,54,물류센터,139000
IT-006,삼성 870 EVO 1TB,storage,31,본사 2층,129000
IT-007,AirPods Pro,audio,18,본사 3층,359000
IT-008,USB-C 허브 7포트,accessory,89,물류센터,69000
EOF
```

Windows (PowerShell):
```powershell
mkdir -Force data
@"
id,name,category,stock,location,unit_price
IT-001,MacBook Pro 14",laptop,23,본사 3층,2890000
IT-002,MacBook Air 15",laptop,15,본사 3층,1990000
IT-003,Dell U2723QE 모니터,monitor,42,본사 2층,850000
IT-004,로지텍 MX Keys,keyboard,67,물류센터,159000
IT-005,로지텍 MX Master 3S,mouse,54,물류센터,139000
IT-006,삼성 870 EVO 1TB,storage,31,본사 2층,129000
IT-007,AirPods Pro,audio,18,본사 3층,359000
IT-008,USB-C 허브 7포트,accessory,89,물류센터,69000
"@ | Out-File -Encoding utf8 data\inventory.csv
```

### Step 2: lookup_inventory 구현

```python
# src/tools/inventory.py
import json
from mcp.server.fastmcp import Context


# 카테고리 한영 매핑
CATEGORY_MAP = {
    "노트북": "laptop",
    "랩탑": "laptop",
    "모니터": "monitor",
    "키보드": "keyboard",
    "마우스": "mouse",
    "저장장치": "storage",
    "오디오": "audio",
    "액세서리": "accessory",
}


def format_price(price: int) -> str:
    """가격을 한국 원화 형식으로 포맷합니다."""
    return f"{price:,}원"


def search_inventory(
    inventory: list[dict],
    query: str,
    category: str | None = None,
) -> list[dict]:
    """재고 목록에서 검색합니다."""
    query_lower = query.lower()
    # 한영 매핑 적용
    mapped_category = CATEGORY_MAP.get(query_lower, query_lower)

    results = []
    for item in inventory:
        name_match = query_lower in item["name"].lower()
        category_match = (
            mapped_category == item["category"].lower()
            or query_lower in item["category"].lower()
        )
        location_match = query_lower in item.get("location", "").lower()

        if name_match or category_match or location_match:
            # 카테고리 필터 적용
            if category and item["category"].lower() != category.lower():
                continue
            results.append(item)

    return results


def register_inventory_tools(mcp):
    """재고 관련 Tool을 등록합니다."""

    @mcp.tool()
    async def lookup_inventory(
        query: str,
        category: str = "",
        ctx: Context = None,
    ) -> str:
        """사내 재고를 검색합니다.

        품목명, 카테고리, 위치 등으로 재고를 조회할 수 있습니다.
        한국어 카테고리(노트북, 키보드 등)도 지원합니다.

        Args:
            query: 검색 키워드 (예: "맥북", "키보드", "본사 3층")
            category: 카테고리 필터 (예: "laptop", "keyboard"). 비우면 전체 검색
        """
        app = ctx.request_context.lifespan_context["app"]

        await ctx.info(f"재고 검색: query='{query}', category='{category}'")

        cat_filter = category if category else None
        results = search_inventory(app.inventory, query, cat_filter)

        formatted_items = []
        for item in results:
            formatted_items.append({
                "id": item["id"],
                "name": item["name"],
                "category": item["category"],
                "stock": int(item["stock"]),
                "location": item["location"],
                "unit_price": format_price(int(item["unit_price"])),
            })

        response = {
            "query": query,
            "total_results": len(formatted_items),
            "items": formatted_items,
        }

        if not formatted_items:
            response["suggestion"] = (
                "검색 결과가 없습니다. 다른 키워드를 시도해보세요. "
                "예: laptop, monitor, keyboard, mouse"
            )

        await ctx.info(f"검색 완료: {len(formatted_items)}건")
        return json.dumps(response, ensure_ascii=False, indent=2)
```

### Step 3: server.py에 등록

```python
# src/server.py에 추가
from tools.inventory import register_inventory_tools

# mcp 초기화 후
register_inventory_tools(mcp)
```

### Step 4: Inspector에서 테스트

macOS/Linux:
```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

Windows (PowerShell):
```powershell
npx @modelcontextprotocol/inspector uv run python src\server.py
```

테스트 시나리오:
1. `query="맥북"` → MacBook Pro와 MacBook Air 반환
2. `query="노트북"` → 한영 매핑으로 laptop 카테고리 검색
3. `query="프린터"` → 빈 결과 + suggestion 반환
4. `query="본사"` → 위치 기반 검색

### Step 5: Claude Desktop에서 자연어 테스트

Claude Desktop에서 자연어로 테스트합니다:
- "노트북 재고 알려줘"
- "모니터 몇 대 남았어?"
- "물류센터에 있는 장비 뭐 있어?"

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- CSV 데이터를 AppContext에 로딩하여 Tool에서 활용한다
- **fuzzy 검색**: 부분 일치, 다중 필드, 한영 매핑으로 검색 정확도를 높인다
- 결과 포맷은 **LLM 친화적**으로 설계한다 (쿼리 포함, 총 건수, 구조화된 데이터)
- 검색 결과가 없을 때는 **에러가 아닌 빈 결과 + suggestion**을 반환한다

### 퀴즈

1. **검색 결과가 없을 때 에러를 던지는 대신 빈 배열을 반환하는 이유는?**
   → "결과 없음"은 정상적인 상황이지 시스템 오류가 아니다. LLM이 이를 기반으로 대안을 제시할 수 있다.

2. **한영 매핑(CATEGORY_MAP)의 역할은?**
   → 사용자가 한국어로 "노트북"이라고 입력해도 "laptop" 카테고리와 매칭되도록 한다.

### 다음 편 예고

EP06에서는 에러 처리를 다룹니다. 시스템 문제가 발생했을 때 어떻게 LLM에게 알리는지, `ToolError`는 무엇이고, `isError` 필드는 어떻게 활용하는지 배웁니다.
