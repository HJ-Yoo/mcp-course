# MCP 실전 마스터: 프로토콜 이해부터 운영까지

> MCP(Model Context Protocol)를 활용한 실전 온라인 강의


## 수강생 필독! starter-kit 사용법

수강생은 우측 상단에 `use this template` > `Create a new repository`를 선택하셔서 각자 계정 하에 repo를 만드시고, 
이후 `starter-kit/` 디렉토리에서 작업을 진행하시면됩니다. 
각 에피소드의 강의 노트에서 `# TODO` 주석을 찾아 코드를 채워나가는 방식으로 실습합니다. 완성본은 `project/` 디렉토리에서 확인할 수 있습니다.

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
│   ├── chapter-1/               # Chapter 1: MCP 기초
│   │   ├── ep01-what-is-mcp.md
│   │   ├── ep02-architecture.md
│   │   └── ep03-first-server.md
│   └── chapter-2/               # Chapter 2: Tools 심화
│       ├── ep04-tool-basics.md
│       ├── ep05-inventory-tool.md
│       ├── ep06-error-handling.md
│       ├── ep07-policy-tool.md
│       ├── ep08-ticket-tool.md
│       └── ep09-validation.md
├── slides/                      # 에피소드별 슬라이드 (Marp)
│   ├── chapter-1/
│   │   ├── ep01-slides.md
│   │   ├── ep02-slides.md
│   │   └── ep03-slides.md
│   └── chapter-2/
│       ├── ep04-slides.md
│       ├── ep05-slides.md
│       ├── ep06-slides.md
│       ├── ep07-slides.md
│       ├── ep08-slides.md
│       └── ep09-slides.md
├── project/                     # 프로젝트 완성본
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

| 모듈 | 편수 | 시간 | 주제 |
|------|------|------|------|
| **Chapter 1** | EP 01-03 | 1시간 | MCP 기초 — 개념, 아키텍처, 첫 서버 |
| **Chapter 2** | EP 04-09 | 2시간 | Tools 심화 — 재고, 정책, 티켓, 보안 |
| **Chapter 3** | EP 10-16 | 2시간 20분 | Resources & Prompts — 데이터 노출, 템플릿, 테스트 |
| **Chapter 4** | EP 17-21 | 1시간 40분 | 통합 & 테스트 — Transport, 클라이언트 연동, 캡스톤 |
| **Chapter 5** | EP 22-27 | 2시간 | Advanced — 인증, Docker, 모니터링, 프로덕션 |

## 라이선스

MIT
