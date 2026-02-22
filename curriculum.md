# 커리큘럼: MCP 실전 마스터

> 프로토콜 이해부터 운영까지 — 총 27편, 9시간

---

## Module A: MCP 기초 (3편, 1시간)

### EP 01 — MCP란 무엇인가?

- **학습 목표**: MCP의 탄생 배경과 핵심 가치를 이해하고, 기존 방식과의 차이점을 설명할 수 있다
- **핵심 개념**:
  - LLM과 외부 시스템 연결의 N x M 문제
  - MCP가 이를 1 x (N+M)으로 변환하는 원리
  - USB-C 비유: 충전기 통일처럼 프로토콜 통일
  - MCP 3대 프리미티브: Tools, Resources, Prompts
  - MCP vs REST API vs GraphQL — 관점의 차이
- **데모**: uv 설치, 프로젝트 클론, Claude Desktop에서 MCP 서버 목록 확인
- **실습 과제**: uv 환경을 세팅하고 `uv run python --version`으로 확인

### EP 02 — MCP 아키텍처 한눈에 보기

- **학습 목표**: Host/Client/Server 3-tier 구조를 이해하고 JSON-RPC 메시지 흐름을 설명할 수 있다
- **핵심 개념**:
  - 3-tier 구조: Host(Claude Desktop) → Client(프로토콜 계층) → Server(우리 코드)
  - JSON-RPC 2.0 메시지 포맷 (request, response, notification)
  - Transport 레이어: stdio(로컬) vs Streamable HTTP(원격)
  - Capability Negotiation: 서버의 기능 선언
  - Session Lifecycle: initialize → initialized → operation → shutdown
- **데모**: MCP Inspector로 실시간 메시지 흐름 관찰
- **실습 과제**: MCP Inspector를 설치하고 샘플 서버의 initialize 메시지 캡처

### EP 03 — 첫 번째 MCP 서버 만들기

- **학습 목표**: FastMCP로 서버를 초기화하고 Claude Desktop에 연결할 수 있다
- **핵심 개념**:
  - FastMCP — Python MCP SDK의 high-level API
  - 서버 초기화: `FastMCP("server-name")`
  - Lifespan 패턴: `@asynccontextmanager` + `yield {"app": ctx}`
  - Transport 선택과 CLI argument
  - 프로젝트 디렉토리 구조 설계
- **데모**: starter-kit으로 Hello World 서버 구현, Claude Desktop 연결 확인
- **실습 과제**: server.py에 FastMCP를 초기화하고 `--transport` 인자 파싱 구현

---

## Module B: Tools 심화 (6편, 2시간)

### EP 04 — Tool 기초: 함수를 도구로

- **학습 목표**: `@mcp.tool()` 데코레이터로 Python 함수를 MCP Tool로 변환할 수 있다
- **핵심 개념**:
  - `@mcp.tool()` 데코레이터의 동작 원리
  - Tool 파라미터: 타입 힌트와 docstring이 스키마가 되는 과정
  - Tool 결과 포맷: 텍스트, JSON, 에러
  - Context 객체: `ctx.info()`, `ctx.report_progress()` 활용
- **데모**: echo tool 작성, MCP Inspector에서 호출 및 결과 확인
- **실습 과제**: `greet(name: str)` tool을 만들어 Inspector에서 테스트

### EP 05 — 실전 Tool (1) 재고 조회 (lookup_inventory)

- **학습 목표**: CSV 데이터 기반 재고 조회 Tool을 구현하고 실제 대화에서 활용할 수 있다
- **핵심 개념**:
  - CSV 데이터 로딩과 AppContext 연동
  - fuzzy 검색 구현 (키워드 매칭, 부분 일치)
  - JSON 결과 포맷팅 — LLM이 이해하기 쉬운 구조
  - 검색 결과가 없을 때의 처리
- **데모**: `lookup_inventory` 구현, Claude Desktop에서 "노트북 재고 알려줘" 테스트
- **실습 과제**: inventory.csv를 확장하고 카테고리 필터 파라미터 추가

### EP 06 — 에러 처리와 ToolError 패턴

- **학습 목표**: MCP의 에러 처리 메커니즘을 이해하고 적절한 에러 응답을 설계할 수 있다
- **핵심 개념**:
  - ErrorCode enum: InvalidParams, InternalError, MethodNotFound 등
  - ToolError 구조: `isError: true` 필드의 의미
  - 클라이언트가 에러를 받았을 때의 동작 (LLM에게 에러 메시지 전달)
  - 에러 vs 빈 결과 — 언제 에러를 던지고, 언제 빈 배열을 반환하나
  - 사용자 친화적 에러 메시지 작성법
- **데모**: 의도적 에러 발생 시나리오, Inspector에서 에러 메시지 확인
- **실습 과제**: `lookup_inventory`에 에러 처리 로직 추가 (빈 쿼리, 잘못된 카테고리)

### EP 07 — 실전 Tool (2) 정책 검색 (search_policy)

- **학습 목표**: Markdown 파일 기반 사내 정책 검색 Tool을 구현할 수 있다
- **핵심 개념**:
  - Markdown 파일 파싱: 제목, 섹션, 본문 분리
  - YAML front-matter 활용 (제목, 태그, 최종 수정일)
  - 키워드 기반 검색과 스니펫 추출
  - 검색 결과 랭킹 (제목 매치 > 태그 매치 > 본문 매치)
- **데모**: `search_policy` 구현, "VPN 설정 방법" 검색 테스트
- **실습 과제**: 검색 결과에 관련도 점수(relevance score)를 추가

### EP 08 — 입력 검증과 보안 (validation.py)

- **학습 목표**: LLM이 생성하는 임의 입력을 안전하게 검증하는 방법을 이해한다
- **핵심 개념**:
  - 왜 검증이 필요한가: LLM은 예측 불가능한 입력을 생성할 수 있다
  - `validation.py`의 4가지 핵심 함수: `sanitize_string()`, `validate_path()`, `validate_ticket_input()`, `validate_query()`
  - Path Traversal 방지: `../` 패턴 차단
  - Injection 방지: SQL/NoSQL injection 패턴 탐지
  - 화이트리스트 vs 블랙리스트 접근법
- **데모**: validation.py 구현, 악의적 입력 테스트 (path traversal, injection 시도)
- **실습 과제**: `validate_email()` 함수를 추가하고 테스트 작성

### EP 09 — 실전 Tool (3) 티켓 생성 (create_ticket)

- **학습 목표**: 확인 게이트가 포함된 상태 기반 Tool을 설계하고 구현할 수 있다
- **핵심 개념**:
  - 확인 게이트 패턴: `confirm=False`일 때 프리뷰, `confirm=True`일 때 생성
  - Idempotency Key: 중복 생성 방지
  - JSONL 파일 기반 영속성
  - 상태 기반 도구 설계: 프리뷰 → 확인 → 생성 → 조회
  - 티켓 ID 생성 전략 (UUID vs sequential)
- **데모**: `create_ticket` 구현, 프리뷰 → 확인 → 생성 전체 플로우 테스트
- **실습 과제**: 티켓 상태 변경 tool(`update_ticket_status`) 추가

---

## Module C: Resources & Prompts (7편, 2시간 20분)

### EP 10 — Resource 기초: 데이터를 노출하라

- **학습 목표**: MCP Resource의 개념을 이해하고 정적/동적 Resource를 구현할 수 있다
- **핵심 개념**:
  - Resource란: LLM이 읽을 수 있는 데이터 엔드포인트
  - Tool vs Resource: Tool은 "행동", Resource는 "정보"
  - URI 스키마: `ops://` 커스텀 프로토콜
  - 정적 Resource: 고정 URI (`ops://policies/index`)
  - 동적 Resource Template: URI 파라미터 (`ops://policies/{slug}`)
  - MIME 타입과 Content-Type
- **데모**: 간단한 정적 Resource 구현, Inspector에서 읽기 테스트
- **실습 과제**: `ops://status` Resource를 만들어 서버 상태 정보 반환

### EP 11 — 실전 Resource (1) 정책 인덱스와 상세

- **학습 목표**: 정책 문서를 Resource로 노출하여 LLM이 맥락을 이해할 수 있게 한다
- **핵심 개념**:
  - 정책 인덱스 Resource: 전체 정책 목록 반환
  - 정책 상세 Resource Template: slug 기반 개별 정책 반환
  - Resource와 Tool의 협업: 검색(Tool) → 상세 조회(Resource)
  - Resource 캐싱 전략
- **데모**: `ops://policies/index`와 `ops://policies/{slug}` 구현
- **실습 과제**: 정책에 버전 정보를 추가하고 `ops://policies/{slug}/v/{version}` 구현

### EP 12 — Resource 보안: Path Traversal 방지

- **학습 목표**: Resource URI를 통한 보안 위협을 이해하고 방어 코드를 작성할 수 있다
- **핵심 개념**:
  - Path Traversal 공격: `ops://policies/../../etc/passwd`
  - `os.path.realpath()`를 이용한 경로 정규화
  - 허용 디렉토리 밖 접근 차단 (base directory check)
  - URI 파라미터 화이트리스트 검증
  - 에러 메시지에 민감 정보 노출 방지
- **데모**: Path Traversal 시도와 방어 코드 동작 확인
- **실습 과제**: 보안 테스트 케이스 5개 작성

### EP 13 — Prompt Template 이해와 활용

- **학습 목표**: MCP Prompt Template을 작성하여 LLM의 응답 품질을 향상시킬 수 있다
- **핵심 개념**:
  - Prompt Template이란: 서버가 제공하는 대화 템플릿
  - `@mcp.prompt()` 데코레이터 사용법
  - 파라미터화된 Prompt: 동적 변수 주입
  - Multi-turn Prompt: `UserMessage`와 `AssistantMessage` 조합
  - Prompt와 Resource의 조합: 맥락 + 지시사항
- **데모**: `triage-ticket` Prompt Template 구현
- **실습 과제**: `summarize-policy` Prompt Template 작성

### EP 14 — 감사 로깅 (Audit Logging)

- **학습 목표**: 모든 Tool 호출을 기록하는 감사 로깅 시스템을 구현할 수 있다
- **핵심 개념**:
  - 감사 로깅의 필요성: 누가, 언제, 무엇을 했는가
  - 로그 포맷 설계: timestamp, tool_name, parameters, result, duration
  - JSONL 파일 기반 로깅
  - 비동기 로깅과 성능 고려
  - 로그 분석과 통계
- **데모**: `audit.py` 구현, Tool 호출 시 자동 로깅 확인
- **실습 과제**: 로그 분석 스크립트 작성 (가장 많이 호출된 Tool, 평균 응답 시간)

### EP 15 — 테스트 전략과 pytest 셋업

- **학습 목표**: MCP 서버의 단위 테스트 환경을 구축하고 Tool 단위 테스트를 작성할 수 있다
- **핵심 개념**:
  - MCP 서버 테스트의 특수성: 비동기, JSON-RPC
  - pytest + pytest-asyncio 셋업
  - Mock AppContext 패턴
  - Tool 함수 직접 호출 테스트
  - conftest.py에서 fixture 설계
- **데모**: `test_tools.py` 작성 및 실행
- **실습 과제**: `lookup_inventory`와 `search_policy`의 엣지 케이스 테스트 5개 작성

### EP 16 — 통합 테스트로 서버 검증

- **학습 목표**: MCP 프로토콜 수준의 통합 테스트를 작성할 수 있다
- **핵심 개념**:
  - 통합 테스트 vs 단위 테스트: 무엇을 검증하는가
  - MCP Test Client 활용
  - stdio Transport를 이용한 E2E 테스트
  - 테스트 시나리오 설계: 정상 흐름, 에러 흐름, 경계 조건
  - CI/CD 파이프라인에서의 테스트 실행
- **데모**: `test_integration.py` 작성, 전체 서버 기동 → Tool 호출 → 결과 검증
- **실습 과제**: 재고 조회 → 티켓 생성 시나리오를 통합 테스트로 작성

---

## Module D: 통합 & 배포 (5편, 1시간 40분)

### EP 17 — Streamable HTTP Transport

- **학습 목표**: HTTP 기반 Transport를 설정하고 원격 서버를 운영할 수 있다
- **핵심 개념**:
  - stdio vs Streamable HTTP 비교
  - Streamable HTTP의 동작 원리: 단일 HTTP 엔드포인트
  - 세션 관리와 상태 유지
  - 방화벽, 프록시 환경에서의 고려사항
  - CORS 설정
- **데모**: 서버를 HTTP 모드로 실행하고 원격 클라이언트에서 접속
- **실습 과제**: HTTP Transport로 서버를 실행하고 curl로 JSON-RPC 메시지 전송

### EP 18 — Claude Desktop 연동

- **학습 목표**: Claude Desktop에 MCP 서버를 등록하고 실제 대화에서 활용할 수 있다
- **핵심 개념**:
  - `claude_desktop_config.json` 구조와 위치
  - stdio 서버 등록 방법
  - HTTP 서버 등록 방법
  - 환경 변수 전달 (`env` 필드)
  - 디버깅: Claude Desktop 로그 확인
- **데모**: Internal Ops Assistant를 Claude Desktop에 연결하여 실제 업무 시나리오 테스트
- **실습 과제**: 3가지 시나리오 테스트 (재고 조회, 정책 검색, 티켓 생성)

### EP 19 — Cursor / VS Code 연동

- **학습 목표**: Cursor와 VS Code에서 MCP 서버를 활용할 수 있다
- **핵심 개념**:
  - Cursor의 MCP 지원 현황
  - VS Code + Copilot Chat에서의 MCP 활용
  - `.cursor/mcp.json` 설정
  - IDE별 특성과 제약사항
  - 개발자 워크플로우에서의 MCP 활용 사례
- **데모**: Cursor에서 Internal Ops Assistant 연결 및 사용
- **실습 과제**: Cursor에서 "재고가 부족한 품목의 발주 티켓 생성" 시나리오 테스트

### EP 20 — SSE에서 Streamable HTTP 마이그레이션

- **학습 목표**: 레거시 SSE Transport에서 Streamable HTTP로 마이그레이션할 수 있다
- **핵심 개념**:
  - SSE Transport의 역사와 한계
  - Streamable HTTP가 SSE를 대체하는 이유
  - 마이그레이션 체크리스트
  - 하위 호환성 유지 전략
  - 클라이언트 업데이트 가이드
- **데모**: SSE 서버 → Streamable HTTP 서버 변환 과정
- **실습 과제**: 기존 SSE 설정을 Streamable HTTP로 변환

### EP 21 — 캡스톤 리뷰: 전체 시스템 점검

- **학습 목표**: Internal Ops Assistant의 전체 구성 요소를 점검하고 개선점을 도출할 수 있다
- **핵심 개념**:
  - 아키텍처 리뷰: Tools, Resources, Prompts 전체 구조
  - 코드 품질 점검: 타입 힌트, docstring, 에러 처리
  - 테스트 커버리지 확인
  - 성능 프로파일링 기초
  - 개선 과제 도출 (Advanced 모듈 예고)
- **데모**: 전체 시스템 데모 — 실제 업무 시나리오 3개 연속 수행
- **실습 과제**: 자신의 프로젝트에 대한 리뷰 체크리스트 작성

---

## Module E: Advanced (6편, 2시간)

### EP 22 — OAuth 2.1 & 인증 게이트웨이

- **학습 목표**: MCP 서버에 OAuth 2.1 인증을 구현하고 인증된 요청만 처리할 수 있다
- **핵심 개념**:
  - MCP 스펙의 인증 요구사항 (2025-03-26 spec)
  - OAuth 2.1 플로우: Authorization Code + PKCE
  - Bearer Token 검증
  - 인증 게이트웨이 패턴: 인증 로직을 서버 코드에서 분리
  - Scope 기반 권한 관리 (tools:read, tools:write)
- **데모**: 인증 미들웨어 구현, 인증 없이 호출 시 거부 확인
- **실습 과제**: Scope 기반 Tool 접근 제어 구현

### EP 23 — Docker 컨테이너화

- **학습 목표**: MCP 서버를 Docker 이미지로 패키징하고 컨테이너로 배포할 수 있다
- **핵심 개념**:
  - Dockerfile 작성: uv 기반 빌드
  - Multi-stage 빌드로 이미지 크기 최적화
  - 환경 변수와 볼륨 마운트
  - Docker Compose로 서버 + 데이터 구성
  - 헬스 체크 엔드포인트
- **데모**: Docker 이미지 빌드 → 컨테이너 실행 → 클라이언트 연결
- **실습 과제**: Docker Compose로 서버 + 로그 수집기 구성

### EP 24 — Rate Limiting & Caching

- **학습 목표**: MCP 서버에 Rate Limiting과 캐싱을 적용하여 안정성을 높일 수 있다
- **핵심 개념**:
  - Rate Limiting의 필요성: LLM의 반복 호출 방지
  - Token Bucket 알고리즘 구현
  - 결과 캐싱: TTL 기반 in-memory 캐시
  - Tool별 Rate Limit 차등 적용
  - 캐시 무효화 전략
- **데모**: Rate Limiter 미들웨어 구현, 초과 시 에러 응답 확인
- **실습 과제**: `search_policy` 결과에 TTL 캐싱 적용

### EP 25 — Multi-Server 오케스트레이션

- **학습 목표**: 여러 MCP 서버를 조합하여 복합 워크플로우를 구성할 수 있다
- **핵심 개념**:
  - Multi-Server 아키텍처: 하나의 Host에 여러 Server 연결
  - 서버 간 역할 분리: Ops Server, Analytics Server, Notification Server
  - 클라이언트의 서버 선택 로직
  - 서버 간 데이터 공유 패턴
  - Fallback과 Circuit Breaker 패턴
- **데모**: 2개 서버(Ops + Analytics) 동시 연결, Claude Desktop에서 교차 활용
- **실습 과제**: Notification Server를 추가하고 티켓 생성 시 알림 전송

### EP 26 — Observability: 메트릭 & 트레이싱

- **학습 목표**: MCP 서버의 운영 상태를 모니터링하고 문제를 진단할 수 있다
- **핵심 개념**:
  - 관찰 가능성의 3대 축: Metrics, Logging, Tracing
  - OpenTelemetry 연동
  - 주요 메트릭: 요청 수, 응답 시간, 에러율
  - 분산 트레이싱: Tool 호출 체인 추적
  - 대시보드 구성 (Grafana 연동 개요)
- **데모**: OpenTelemetry 트레이서 설정, Jaeger에서 트레이스 확인
- **실습 과제**: 커스텀 메트릭 3개 추가 (Tool 호출 횟수, 평균 응답 시간, 에러 비율)

### EP 27 — 프로덕션 체크리스트 & 마무리

- **학습 목표**: MCP 서버를 프로덕션에 배포하기 위한 체크리스트를 완성할 수 있다
- **핵심 개념**:
  - 프로덕션 체크리스트 10항목
    1. 인증/인가
    2. 입력 검증
    3. 에러 처리
    4. 로깅
    5. 모니터링
    6. Rate Limiting
    7. 캐싱
    8. 컨테이너화
    9. CI/CD
    10. 문서화
  - MCP 스펙 업데이트 대응 전략
  - 커뮤니티와 생태계
  - 앞으로의 학습 방향
- **데모**: 프로덕션 체크리스트 순회 점검, 최종 데모
- **실습 과제**: 자신만의 MCP 서버 아이디어 1개 기획서 작성

---

## 부록

### 선수 지식 가이드

| 주제 | 권장 수준 | 참고 자료 |
|------|----------|----------|
| Python | 중급 (async/await 이해) | Python 공식 튜토리얼 |
| JSON | 기초 | MDN JSON Guide |
| HTTP | 기초 (메서드, 상태 코드) | MDN HTTP Guide |
| CLI | 기초 (터미널 사용법) | — |

### 도구 버전 정보

| 도구 | 권장 버전 |
|------|----------|
| Python | 3.11+ |
| uv | 0.5+ |
| FastMCP | 최신 |
| Claude Desktop | 최신 |
| MCP Inspector | 최신 |

### 자주 묻는 질문

**Q: pip 대신 uv를 사용하는 이유는?**
A: uv는 Rust로 작성된 Python 패키지 매니저로, pip보다 10-100배 빠르며 프로젝트 격리와 의존성 관리가 더 간편합니다.

**Q: Windows에서도 모든 실습이 가능한가요?**
A: 네. 모든 터미널 명령어에 macOS/Linux와 Windows 버전을 함께 제공합니다.

**Q: Claude Desktop이 없으면 수강할 수 없나요?**
A: MCP Inspector만으로도 대부분의 실습이 가능합니다. Claude Desktop은 EP18에서 본격적으로 사용합니다.
