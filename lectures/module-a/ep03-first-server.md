# EP 03 — 첫 번째 MCP 서버 만들기

> Module A: MCP 기초 · 약 20분

## 학습 목표

1. FastMCP 라이브러리로 MCP 서버를 초기화할 수 있다
2. Lifespan 패턴을 이용해 서버 시작 시 데이터를 로딩할 수 있다
3. Claude Desktop에 MCP 서버를 등록하고 연결을 확인할 수 있다

---

## 1. 인트로 (2분)

EP01에서 MCP의 개념을, EP02에서 아키텍처를 배웠습니다. 이론은 충분합니다. 이제 직접 코드를 작성할 시간입니다.

이번 에피소드에서는 **FastMCP**라는 Python 라이브러리를 사용해 첫 번째 MCP 서버를 만들어봅니다. FastMCP는 MCP Python SDK의 high-level API로, 복잡한 프로토콜 세부사항을 감추고 간결한 코드로 서버를 구현할 수 있게 해줍니다.

우리의 캡스톤 프로젝트 Internal Ops Assistant의 뼈대를 이 에피소드에서 완성합니다.

---

## 2. 핵심 개념 (6분)

### 2.1 FastMCP 소개

FastMCP는 MCP Python SDK에 포함된 high-level API입니다. 데코레이터 기반으로 Tool, Resource, Prompt를 간결하게 정의할 수 있습니다.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ops-assistant")

@mcp.tool()
def hello(name: str) -> str:
    """인사를 합니다."""
    return f"안녕하세요, {name}님!"
```

이것만으로 `hello`라는 MCP Tool이 정의됩니다. 타입 힌트(`name: str`)는 자동으로 JSON Schema로 변환되고, docstring은 Tool 설명이 됩니다.

### 2.2 서버 초기화

`FastMCP`를 초기화할 때 서버 이름과 설정을 지정합니다:

```python
mcp = FastMCP(
    "ops-assistant",
    instructions="사내 IT 운영을 돕는 어시스턴트입니다. "
                 "재고 조회, 정책 검색, 티켓 생성 기능을 제공합니다.",
)
```

`instructions`는 LLM에게 이 서버의 용도를 알려주는 문자열입니다. 클라이언트가 `initialize` 응답에서 이 정보를 받아 LLM의 시스템 프롬프트에 포함시킵니다.

### 2.3 Lifespan 패턴

서버가 시작될 때 데이터 파일을 로딩하거나, 데이터베이스 연결을 설정하거나, 설정 파일을 읽어야 할 때가 있습니다. 이럴 때 **Lifespan** 패턴을 사용합니다.

```python
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """서버 시작 시 실행되는 초기화 로직."""
    ctx = AppContext.load(data_dir="data")
    try:
        yield {"app": ctx}
    finally:
        # 정리 작업 (파일 닫기, 연결 해제 등)
        pass

mcp = FastMCP("ops-assistant", lifespan=app_lifespan)
```

`yield` 앞은 시작 시 실행, `yield` 뒤(`finally` 블록)는 종료 시 실행됩니다. `yield`에 전달하는 딕셔너리는 Tool/Resource 핸들러에서 `ctx.request_context.lifespan_context["app"]`으로 접근할 수 있습니다.

### 2.4 AppContext 패턴

데이터 로딩과 상태 관리를 `AppContext` 클래스로 캡슐화합니다:

```python
from dataclasses import dataclass, field

@dataclass
class AppContext:
    inventory: list[dict] = field(default_factory=list)
    policies: dict[str, str] = field(default_factory=dict)
    data_dir: str = "data"

    @classmethod
    def load(cls, data_dir: str = "data") -> "AppContext":
        ctx = cls(data_dir=data_dir)
        ctx.inventory = load_csv(f"{data_dir}/inventory.csv")
        ctx.policies = load_policies(f"{data_dir}/policies/")
        return ctx
```

이 패턴의 장점:
- 데이터 로딩 로직이 한 곳에 집중
- 테스트 시 Mock AppContext 교체 가능
- 서버 시작 시 한 번만 로딩 (매 요청마다 파일 읽지 않음)

### 2.5 Transport 선택과 실행

서버 실행 시 Transport를 선택할 수 있습니다:

```python
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", port=args.port)
```

### 2.6 프로젝트 구조

Internal Ops Assistant의 디렉토리 구조:

```
project/
├── pyproject.toml          # 프로젝트 메타데이터, 의존성
├── .env.example            # 환경 변수 템플릿
├── src/
│   ├── server.py           # 엔트리포인트 (FastMCP 초기화)
│   ├── models.py           # AppContext, 데이터 모델
│   ├── tools/              # Tool 구현 (EP04-09)
│   ├── resources/          # Resource 구현 (EP10-12)
│   ├── prompts/            # Prompt 구현 (EP13)
│   ├── validation.py       # 입력 검증 (EP08)
│   └── audit.py            # 감사 로깅 (EP14)
├── data/
│   ├── inventory.csv       # 재고 데이터
│   ├── policies/           # 사내 정책 Markdown
│   └── tickets/            # 티켓 JSONL 저장소
└── tests/                  # 테스트 (EP15-16)
```

---

## 3. 라이브 데모 (10분)

### Step 1: starter-kit 열기

macOS/Linux:
```bash
cd starter-kit
ls -la
```

Windows (PowerShell):
```powershell
cd starter-kit
dir
```

`pyproject.toml`을 확인합니다:

```toml
[project]
name = "ops-assistant"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]
```

### Step 2: 의존성 설치

macOS/Linux:
```bash
uv sync --all-extras
```

Windows (PowerShell):
```powershell
uv sync --all-extras
```

`--all-extras`는 dev 의존성(pytest 등)도 함께 설치합니다.

### Step 3: models.py 작성

```python
# src/models.py
import csv
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppContext:
    """서버 전체에서 공유되는 애플리케이션 상태."""

    inventory: list[dict] = field(default_factory=list)
    policies: dict[str, str] = field(default_factory=dict)
    data_dir: str = "data"

    @classmethod
    def load(cls, data_dir: str = "data") -> "AppContext":
        """데이터 파일을 로딩하여 AppContext를 생성합니다."""
        ctx = cls(data_dir=data_dir)

        # 재고 데이터 로딩
        inventory_path = Path(data_dir) / "inventory.csv"
        if inventory_path.exists():
            with open(inventory_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                ctx.inventory = list(reader)

        # 정책 문서 로딩
        policies_dir = Path(data_dir) / "policies"
        if policies_dir.exists():
            for md_file in policies_dir.glob("*.md"):
                slug = md_file.stem
                ctx.policies[slug] = md_file.read_text(encoding="utf-8")

        return ctx
```

### Step 4: server.py 작성

```python
# src/server.py
import argparse
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from models import AppContext


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """서버 시작 시 데이터를 로딩합니다."""
    ctx = AppContext.load(data_dir="data")
    print(f"[ops-assistant] 재고 {len(ctx.inventory)}건, "
          f"정책 {len(ctx.policies)}건 로딩 완료")
    try:
        yield {"app": ctx}
    finally:
        print("[ops-assistant] 서버를 종료합니다.")


mcp = FastMCP(
    "ops-assistant",
    instructions=(
        "사내 IT 운영을 돕는 어시스턴트입니다. "
        "재고 조회, 정책 검색, 티켓 생성 기능을 제공합니다."
    ),
    lifespan=app_lifespan,
)


@mcp.tool()
def hello(name: str) -> str:
    """간단한 인사 도구 — 서버 동작 확인용입니다."""
    return f"안녕하세요, {name}님! Internal Ops Assistant입니다."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Internal Ops Assistant MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport 방식 (기본: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP Transport 포트 (기본: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", port=args.port)
```

### Step 5: 실행 확인

macOS/Linux:
```bash
uv run python src/server.py --transport stdio
```

Windows (PowerShell):
```powershell
uv run python src\server.py --transport stdio
```

서버가 시작되면 "재고 X건, 정책 Y건 로딩 완료" 메시지가 출력됩니다.

### Step 6: MCP Inspector로 테스트

새 터미널을 열고:

macOS/Linux:
```bash
npx @modelcontextprotocol/inspector uv run python src/server.py
```

Windows (PowerShell):
```powershell
npx @modelcontextprotocol/inspector uv run python src\server.py
```

Inspector에서 Tools 탭을 열면 `hello` 도구가 보입니다. `name` 파라미터에 "Logan"을 입력하고 실행하면 "안녕하세요, Logan님! Internal Ops Assistant입니다." 응답을 확인할 수 있습니다.

### Step 7: Claude Desktop 설정

macOS에서 `claude_desktop_config.json`을 편집합니다:

macOS:
```bash
# 설정 파일 위치
# ~/Library/Application Support/Claude/claude_desktop_config.json
```

Windows:
```powershell
# 설정 파일 위치
# %APPDATA%\Claude\claude_desktop_config.json
```

설정 내용:

```json
{
  "mcpServers": {
    "ops-assistant": {
      "command": "uv",
      "args": ["run", "python", "src/server.py"],
      "cwd": "/absolute/path/to/project",
      "env": {}
    }
  }
}
```

`cwd`에는 프로젝트의 절대 경로를 입력합니다. Claude Desktop을 재시작하면 MCP 서버가 자동으로 연결됩니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- **FastMCP**는 Python MCP SDK의 high-level API로 데코레이터 기반 서버 구현을 지원한다
- **Lifespan 패턴**으로 서버 시작/종료 시 초기화/정리 로직을 실행한다
- **AppContext 패턴**으로 데이터 로딩과 상태 관리를 캡슐화한다
- `claude_desktop_config.json`에 서버를 등록하여 Claude Desktop과 연결한다
- `uv sync`와 `uv run`으로 의존성 관리와 실행을 처리한다

### 퀴즈

1. **FastMCP의 lifespan이 필요한 이유는?**
   → 서버 시작 시 데이터 파일 로딩, DB 연결 등 초기화 작업을 수행하고, 종료 시 리소스를 정리하기 위해.

2. **AppContext 패턴의 장점은?**
   → 데이터 로딩이 한 곳에 집중되고, 테스트 시 Mock으로 교체 가능하며, 요청마다 파일을 읽지 않아 성능이 좋다.

3. **Claude Desktop 설정에서 `cwd` 필드의 역할은?**
   → 서버 프로세스의 작업 디렉토리를 지정. 상대 경로로 지정된 데이터 파일을 올바르게 찾기 위해 필요.

### 다음 편 예고

EP04에서는 `@mcp.tool()` 데코레이터를 본격적으로 다룹니다. Python 함수를 MCP Tool로 변환하는 과정, 파라미터 타입이 자동으로 JSON Schema가 되는 원리, Context 객체 활용법을 배웁니다.
