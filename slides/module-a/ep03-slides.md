---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 03 — 첫 번째 MCP 서버 만들기"
---

# EP 03 — 첫 번째 MCP 서버 만들기
## Module A: MCP 기초 · MCP 실전 마스터

---

## 학습 목표

1. FastMCP 라이브러리로 MCP 서버를 초기화할 수 있다
2. Lifespan 패턴으로 서버 시작 시 데이터를 로딩할 수 있다
3. Claude Desktop에 서버를 등록하고 연결할 수 있다

---

## FastMCP란?

- Python MCP SDK의 **high-level API**
- **데코레이터 기반** — `@mcp.tool()`, `@mcp.resource()`
- 복잡한 프로토콜을 감추고 간결한 코드로 서버 구현

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ops-assistant")

@mcp.tool()
def hello(name: str) -> str:
    """인사를 합니다."""
    return f"안녕하세요, {name}님!"
```

---

## 서버 초기화

```python
mcp = FastMCP(
    "ops-assistant",
    instructions=(
        "사내 IT 운영을 돕는 어시스턴트입니다. "
        "재고 조회, 정책 검색, 티켓 생성 기능을 제공합니다."
    ),
)
```

- `"ops-assistant"` → 서버 이름 (클라이언트에 표시)
- `instructions` → LLM에게 전달되는 서버 설명

---

## Lifespan 패턴

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    # --- 서버 시작 시 실행 ---
    ctx = AppContext.load(data_dir="data")
    try:
        yield {"app": ctx}  # Tool/Resource에서 접근 가능
    finally:
        # --- 서버 종료 시 실행 ---
        pass

mcp = FastMCP("ops-assistant", lifespan=app_lifespan)
```

`yield` 전 = 초기화 / `yield` 후 = 정리

---

## AppContext 패턴

```python
@dataclass
class AppContext:
    inventory: list[dict] = field(default_factory=list)
    policies: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, data_dir: str = "data") -> "AppContext":
        ctx = cls()
        ctx.inventory = load_csv(f"{data_dir}/inventory.csv")
        ctx.policies = load_policies(f"{data_dir}/policies/")
        return ctx
```

장점: 한 곳에 집중 / Mock 교체 가능 / 한 번만 로딩

---

## Transport 선택

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport",
        choices=["stdio", "streamable-http"],
        default="stdio")
    args = parser.parse_args()

    mcp.run(transport=args.transport)
```

- `stdio` → Claude Desktop, 로컬 개발
- `streamable-http` → 원격 배포, API 서버

---

## 프로젝트 구조

```
project/
├── pyproject.toml      # 의존성 정의
├── src/
│   ├── server.py       # 엔트리포인트
│   ├── models.py       # AppContext
│   ├── tools/          # Tool 구현 (EP04-09)
│   ├── resources/      # Resource 구현 (EP10-12)
│   ├── prompts/        # Prompt 구현 (EP13)
│   ├── validation.py   # 입력 검증 (EP08)
│   └── audit.py        # 감사 로깅 (EP14)
├── data/               # CSV, Markdown, JSONL
└── tests/              # pytest (EP15-16)
```

---

## 데모: 의존성 설치

```bash
# pyproject.toml
[project]
name = "ops-assistant"
version = "0.1.0"
dependencies = [
    "mcp[cli]>=1.0.0",
    "python-dotenv>=1.0.0",
]
```

```bash
uv sync --all-extras
```

---

## 데모: 서버 실행

macOS/Linux:
```bash
uv run python src/server.py --transport stdio
```

Windows (PowerShell):
```powershell
uv run python src\server.py --transport stdio
```

Inspector로 테스트:
```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

---

## Claude Desktop 설정

```json
{
  "mcpServers": {
    "ops-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/absolute/path/to/project"
    }
  }
}
```

macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%\Claude\claude_desktop_config.json`

---

## 핵심 정리

- **FastMCP**: 데코레이터 기반 서버 구현
- **Lifespan**: 서버 시작/종료 시 초기화/정리
- **AppContext**: 데이터 로딩 캡슐화
- **Transport**: stdio(로컬) vs streamable-http(원격)
- `claude_desktop_config.json`에 서버 등록

---

## 퀴즈

1. FastMCP의 lifespan이 필요한 이유?
   → 서버 시작 시 데이터 로딩, 종료 시 리소스 정리

2. AppContext 패턴의 장점?
   → 한 곳 집중, Mock 교체 가능, 요청마다 파일 읽지 않음

---

## 다음 편 예고

### EP 04: Tool 기초 — 함수를 도구로

- `@mcp.tool()` 데코레이터 심화
- 타입 힌트 → JSON Schema 자동 변환
- Context 객체 활용
