# EP 01 — MCP란 무엇인가?

> Module A: MCP 기초 · 약 20분

## 학습 목표

1. MCP(Model Context Protocol)의 탄생 배경과 해결하려는 문제를 설명할 수 있다
2. 기존 LLM 통합 방식(커스텀 플러그인)과 MCP의 차이점을 비교할 수 있다
3. MCP의 3대 프리미티브(Tools, Resources, Prompts)를 구분할 수 있다

---

## 1. 인트로 (2분)

AI 에이전트의 시대가 열렸습니다. ChatGPT, Claude, Gemini 같은 LLM(대규모 언어 모델)이 우리의 일상과 업무에 깊숙이 들어왔죠. 그런데 한 가지 문제가 있습니다.

> "LLM은 똑똑하지만, 혼자서는 아무것도 할 수 없습니다."

이메일을 보내려면 이메일 API가 필요하고, 데이터를 조회하려면 데이터베이스 연결이 필요하고, 파일을 읽으려면 파일 시스템 접근이 필요합니다. LLM이 외부 세계와 소통하는 방법이 필요한데, 지금까지는 통일된 표준이 없었습니다.

이번 에피소드에서는 바로 이 문제를 해결하기 위해 탄생한 **MCP(Model Context Protocol)**가 무엇인지 알아보겠습니다.

---

## 2. 핵심 개념 (6분)

### 2.1 기존 방식의 한계: N x M 문제

LLM이 외부 시스템과 연결되는 기존 방식을 생각해봅시다.

- ChatGPT에 Slack을 연결하려면? → OpenAI 전용 플러그인 개발
- Claude에 Slack을 연결하려면? → Anthropic 전용 플러그인 개발
- Gemini에 Slack을 연결하려면? → Google 전용 플러그인 개발

이걸 모든 서비스에 대해 반복한다면?

```
N개의 LLM  x  M개의 외부 서비스  =  N x M개의 커스텀 통합
```

LLM이 5개이고 연결할 서비스가 20개라면, 최대 **100개의 커스텀 통합 코드**가 필요합니다. 새로운 LLM이 추가될 때마다, 새로운 서비스가 추가될 때마다 이 숫자는 계속 늘어납니다.

### 2.2 MCP의 해답: 1 x (N+M)

MCP는 이 문제를 **표준 프로토콜**로 해결합니다.

```
LLM들 → [MCP 프로토콜] ← 외부 서비스들

통합 비용: N + M (각각 한 번씩만 MCP 지원하면 됨)
```

모든 LLM은 MCP 클라이언트를 한 번만 구현하면 되고, 모든 외부 서비스는 MCP 서버를 한 번만 구현하면 됩니다. LLM 5개 + 서비스 20개 = **25개의 구현**이면 전부 연결됩니다.

### 2.3 USB-C 비유

가장 직관적인 비유는 USB-C입니다.

과거에는 기기마다 다른 충전기가 필요했습니다. iPhone은 Lightning, Android는 Micro USB, 노트북은 각각 다른 전용 충전기... MCP 없는 LLM 생태계가 바로 이 상태입니다.

USB-C가 등장하면서 하나의 케이블로 모든 기기를 충전할 수 있게 되었습니다. MCP는 LLM 생태계의 USB-C입니다. **하나의 프로토콜로 모든 연결을 표준화**합니다.

### 2.4 MCP의 3대 프리미티브

MCP는 세 가지 기본 요소(프리미티브)로 구성됩니다:

| 프리미티브 | 역할 | 비유 | 예시 |
|-----------|------|------|------|
| **Tools** | LLM이 실행할 수 있는 함수 | "손" | 티켓 생성, 이메일 전송 |
| **Resources** | LLM이 읽을 수 있는 데이터 | "눈" | 정책 문서, 재고 현황 |
| **Prompts** | 미리 정의된 대화 템플릿 | "대본" | 티켓 분류 템플릿 |

**Tools**는 LLM이 외부 세계에 **영향을 미치는** 행동입니다. 데이터를 변경하거나, 외부 API를 호출하거나, 파일을 생성합니다.

**Resources**는 LLM이 외부 세계를 **읽는** 방법입니다. 데이터베이스 조회, 파일 읽기, API 상태 확인 같은 읽기 전용 작업입니다.

**Prompts**는 서버가 미리 정의해 놓은 **대화 템플릿**입니다. 반복되는 작업의 품질을 높이고 일관성을 유지합니다.

### 2.5 MCP vs REST API vs GraphQL

"이미 REST API가 있는데 왜 MCP가 필요한가요?"

핵심적인 차이는 **관점의 전환**입니다:

| 기준 | REST API | GraphQL | MCP |
|------|----------|---------|-----|
| 대상 | 사람(개발자) | 사람(개발자) | **LLM(AI)** |
| 스키마 | OpenAPI (선택) | 필수 | **자동 생성** |
| 탐색 | 문서 읽기 | Introspection | **Capability Negotiation** |
| 실행 주체 | 개발자가 코드 작성 | 개발자가 쿼리 작성 | **LLM이 자율 판단** |

REST API와 GraphQL은 개발자가 직접 호출 코드를 작성합니다. MCP는 LLM이 **스스로 어떤 도구를 사용할지 판단하고 호출**합니다. 서버는 자신이 제공하는 기능을 선언하고, 클라이언트(LLM)는 그 선언을 보고 상황에 맞게 활용합니다.

---

## 3. 라이브 데모 (10분)

### Step 1: uv 설치

이 과정에서는 Python 패키지 매니저로 `uv`를 사용합니다. pip보다 10-100배 빠르고, 가상 환경 관리가 훨씬 간편합니다.

macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 확인:
```bash
uv --version
```

### Step 2: 프로젝트 클론 및 세팅

macOS/Linux:
```bash
git clone https://github.com/HJ-Yoo/mcp-course.git
cd mcp-course/starter-kit
uv sync
```

Windows (PowerShell):
```powershell
git clone https://github.com/HJ-Yoo/mcp-course.git
cd mcp-course\starter-kit
uv sync
```

`uv sync`을 실행하면 `pyproject.toml`에 정의된 의존성이 자동으로 설치됩니다. 가상 환경도 자동 생성됩니다.

### Step 3: MCP가 해결하는 실제 시나리오 3가지

이 과정의 캡스톤 프로젝트 **Internal Ops Assistant**가 해결하는 3가지 시나리오를 살펴봅시다:

**시나리오 1: "노트북 재고가 몇 대 남았지?"**
→ 사내 재고 시스템에서 데이터를 조회하는 **Tool** (`lookup_inventory`)

**시나리오 2: "VPN 설정 방법 알려줘"**
→ 사내 정책 문서에서 관련 내용을 찾는 **Tool** (`search_policy`)과 상세 정보를 제공하는 **Resource** (`ops://policies/{slug}`)

**시나리오 3: "노트북 키보드 고장, 수리 접수해줘"**
→ IT 지원 티켓을 생성하는 **Tool** (`create_ticket`)과 일관된 분류를 위한 **Prompt** (`triage-ticket`)

MCP 없이 이 세 가지를 구현하려면? Claude 전용 플러그인, Cursor 전용 확장, VS Code 전용 확장... 각각 따로 만들어야 합니다. MCP로 구현하면? **서버 하나로 어디서든 사용** 가능합니다.

### Step 4: Claude Desktop에서 MCP 서버 확인

Claude Desktop을 열고 설정에서 MCP 서버 목록을 확인합니다.

macOS에서 설정 파일 위치:
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Windows에서 설정 파일 위치:
```powershell
type "$env:APPDATA\Claude\claude_desktop_config.json"
```

아직 서버를 등록하지 않았으므로 빈 설정이 보일 것입니다. EP03에서 직접 서버를 만들어 여기에 등록할 예정입니다.

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- MCP(Model Context Protocol)는 LLM과 외부 시스템을 연결하는 **표준 프로토콜**이다
- 기존 N x M 문제를 1 x (N+M) 문제로 변환하여 통합 비용을 획기적으로 줄인다
- MCP의 3대 프리미티브는 **Tools**(행동), **Resources**(데이터), **Prompts**(템플릿)이다
- MCP는 REST API와 달리 **LLM이 자율적으로 활용**하도록 설계되었다

### 퀴즈

1. **MCP가 해결하는 N x M 문제란?**
   → N개의 LLM과 M개의 서비스를 각각 통합해야 하는 문제. MCP는 이를 N+M으로 줄인다.

2. **MCP의 3가지 프리미티브를 나열하고 각각의 역할은?**
   → Tools(행동 실행), Resources(데이터 읽기), Prompts(대화 템플릿)

3. **MCP와 REST API의 가장 큰 차이는?**
   → REST API는 개발자가 호출 코드를 작성하지만, MCP는 LLM이 자율적으로 도구를 선택하고 호출한다.

### 다음 편 예고

EP02에서는 MCP가 **내부적으로 어떻게 동작하는지** — Host/Client/Server의 3-tier 아키텍처와 JSON-RPC 메시지 흐름을 살펴봅니다. 메시지가 오고 가는 과정을 직접 눈으로 확인해보겠습니다.
