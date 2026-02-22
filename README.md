# MCP 실전 마스터: 프로토콜 이해부터 운영까지

> MCP(Model Context Protocol)를 활용한 실전 온라인 강의

## 과정 개요

- **분량**: 21편 Core + 6편 Advanced = 총 27편
- **시간**: Core 7시간 + Advanced 2시간 = 총 9시간
- **편당**: 20분 (2분 인트로 + 6분 개념 + 10분 데모 + 2분 퀴즈/요약)
- **캡스톤 프로젝트**: Internal Ops Assistant (사내 IT 운영 도우미)

## 사전 요구사항

- Python 3.11+
- uv (패키지 매니저)
- Claude Desktop 또는 MCP 호환 클라이언트
- Git, VS Code (권장)

## 빠른 시작

### 1. uv 설치

macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 프로젝트 설정

macOS/Linux:
```bash
cd project
uv sync
cp .env.example .env
```

Windows (PowerShell):
```powershell
cd project
uv sync
copy .env.example .env
```

### 3. 서버 실행

macOS/Linux:
```bash
uv run python src/server.py --transport stdio
```

Windows (PowerShell):
```powershell
uv run python src\server.py --transport stdio
```

### 4. 테스트

```bash
uv run pytest
```

## 프로젝트 구조

```
mcp-course/
├── README.md                    # 이 파일
├── curriculum.md                # 전체 커리큘럼 (27편)
├── lectures/                    # 에피소드별 강의 노트
│   ├── module-a/                # Module A: MCP 기초
│   │   ├── ep01-what-is-mcp.md
│   │   ├── ep02-architecture.md
│   │   └── ep03-first-server.md
│   └── module-b/                # Module B: Tools 심화
│       ├── ep04-tool-basics.md
│       ├── ep05-inventory-tool.md
│       ├── ep06-error-handling.md
│       ├── ep07-policy-tool.md
│       ├── ep08-validation.md
│       └── ep09-ticket-tool.md
├── slides/                      # 에피소드별 슬라이드 (Marp)
│   ├── module-a/
│   │   ├── ep01-slides.md
│   │   ├── ep02-slides.md
│   │   └── ep03-slides.md
│   └── module-b/
│       ├── ep04-slides.md
│       ├── ep05-slides.md
│       ├── ep06-slides.md
│       ├── ep07-slides.md
│       ├── ep08-slides.md
│       └── ep09-slides.md
├── project/                     # 캡스톤 완성본
│   ├── pyproject.toml
│   ├── .env.example
│   ├── src/
│   │   ├── server.py            # MCP 서버 엔트리포인트
│   │   ├── models.py            # AppContext, 데이터 모델
│   │   ├── tools/
│   │   │   ├── inventory.py     # lookup_inventory
│   │   │   ├── policy.py        # search_policy
│   │   │   └── ticket.py        # create_ticket
│   │   ├── resources/
│   │   │   ├── policy_index.py  # 정책 인덱스 Resource
│   │   │   └── policy_detail.py # 정책 상세 Resource
│   │   ├── prompts/
│   │   │   └── templates.py     # Prompt Templates
│   │   ├── validation.py        # 입력 검증
│   │   └── audit.py             # 감사 로깅
│   ├── data/
│   │   ├── inventory.csv        # 재고 데이터 (샘플)
│   │   ├── policies/            # 사내 정책 Markdown 파일
│   │   └── tickets/             # 티켓 JSONL 저장소
│   └── tests/
│       ├── test_tools.py
│       ├── test_resources.py
│       └── test_integration.py
└── starter-kit/                 # 수강생용 시작 템플릿
    ├── pyproject.toml
    ├── .env.example
    ├── src/
    │   ├── server.py            # 뼈대만 있는 서버
    │   ├── models.py            # TODO 주석 포함
    │   ├── tools/
    │   ├── resources/
    │   ├── prompts/
    │   ├── validation.py
    │   └── audit.py
    ├── data/
    └── tests/
```

## 커리큘럼 요약

전체 커리큘럼은 [curriculum.md](./curriculum.md)를 참조하세요.

| 모듈 | 편수 | 시간 | 주제 |
|------|------|------|------|
| **Module A** | EP 01-03 | 1시간 | MCP 기초 — 개념, 아키텍처, 첫 서버 |
| **Module B** | EP 04-09 | 2시간 | Tools 심화 — 재고, 정책, 티켓, 보안 |
| **Module C** | EP 10-16 | 2시간 20분 | Resources & Prompts — 데이터 노출, 템플릿, 테스트 |
| **Module D** | EP 17-21 | 1시간 40분 | 통합 & 테스트 — Transport, 클라이언트 연동, 캡스톤 |
| **Module E** | EP 22-27 | 2시간 | Advanced — 인증, Docker, 모니터링, 프로덕션 |

## 스타터킷 사용법

수강생은 `starter-kit/` 디렉토리를 복사하여 시작합니다.

macOS/Linux:
```bash
cp -r starter-kit/ my-ops-assistant/
cd my-ops-assistant
uv sync
```

Windows (PowerShell):
```powershell
Copy-Item -Recurse starter-kit\ my-ops-assistant\
cd my-ops-assistant
uv sync
```

각 에피소드의 강의 노트에서 `# TODO` 주석을 찾아 코드를 채워나가는 방식으로 실습합니다. 완성본은 `project/` 디렉토리에서 확인할 수 있습니다.

## 라이선스

MIT
