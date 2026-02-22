# EP 23 — Docker 컨테이너화

> Module E (Advanced) · 약 20분

## 학습 목표

1. MCP 서버를 Docker 이미지로 빌드하는 방법을 이해할 수 있다
2. 멀티스테이지 빌드를 활용하여 이미지 사이즈를 최적화할 수 있다
3. docker-compose로 MCP 서버와 부가 서비스를 통합 구성할 수 있다

---

## 1. 인트로 (2분)

EP22에서 인증 미들웨어를 구현하면서 서버가 점점 프로덕션에 가까워지고 있습니다. 하지만 아직 한 가지 큰 문제가 있습니다.

> "내 컴퓨터에서는 되는데..."

개발 환경마다 Python 버전이 다르고, 의존성 설치 방법이 다르고, OS가 다릅니다. 팀원 A의 macOS에서 잘 동작하는 서버가 팀원 B의 Windows에서는 에러를 내뿜는 상황, 경험해 보셨을 겁니다.

이번 에피소드에서는 **Docker를 사용하여 MCP 서버를 컨테이너화**합니다. "어디서든 동일한 환경"을 보장하고, 배포를 단순화하는 방법을 배웁니다.

---

## 2. 핵심 개념 (6분)

### 2.1 왜 컨테이너화인가?

컨테이너화의 세 가지 핵심 이점:

| 이점 | 설명 | MCP 서버 적용 |
|------|------|--------------|
| **일관된 환경** | 어디서든 동일하게 실행 | Python 버전, 의존성 통일 |
| **배포 용이성** | 이미지 하나로 배포 | `docker pull` + `docker run` |
| **스케일링** | 컨테이너 복제로 확장 | 트래픽 증가 시 인스턴스 추가 |

```
기존 배포:
  macOS: Python 3.11 + pip install + 환경변수 + systemd
  Ubuntu: Python 3.10 + apt-get + pip + 환경변수 + systemd
  Windows: Python 3.12 + pip install + 서비스 등록
  → 3개의 배포 스크립트 유지관리 필요

Docker 배포:
  모든 환경: docker run ops-assistant:latest
  → Dockerfile 하나로 통일
```

### 2.2 Python + uv를 위한 Dockerfile 전략

우리 프로젝트는 **uv**를 패키지 매니저로 사용합니다. Docker에서 uv를 활용하는 핵심 전략:

1. **공식 uv 이미지 활용**: `ghcr.io/astral-sh/uv:latest`에서 uv 바이너리를 복사합니다
2. **레이어 캐싱**: `pyproject.toml`과 `uv.lock`을 먼저 복사하여 의존성 레이어를 캐싱합니다
3. **`--frozen` 플래그**: lock 파일과 정확히 일치하는 버전만 설치합니다

```dockerfile
# 나쁜 예 — 의존성과 소스를 함께 복사 (캐시 무효화)
COPY . .
RUN uv sync

# 좋은 예 — 의존성 파일만 먼저 복사 (레이어 캐싱 활용)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ src/
```

### 2.3 멀티스테이지 빌드

멀티스테이지 빌드는 두 개 이상의 `FROM` 구문을 사용하여 빌드 환경과 실행 환경을 분리합니다:

```
┌─────────────────────────┐     ┌─────────────────────────┐
│ Stage 1: builder        │     │ Stage 2: runner          │
│                         │     │                         │
│ - Python 3.11-slim      │     │ - Python 3.11-slim      │
│ - uv 설치               │     │ - 빌드된 앱만 복사      │
│ - 모든 의존성 설치       │────→│ - uv 바이너리 없음      │
│ - 소스 코드 복사         │     │ - 빌드 도구 없음        │
│                         │     │                         │
│ 크기: ~800MB            │     │ 크기: ~150MB            │
└─────────────────────────┘     └─────────────────────────┘
```

불필요한 빌드 도구, 캐시, 헤더 파일 등을 최종 이미지에서 제거하여 이미지 크기를 크게 줄입니다.

### 2.4 환경변수 관리

프로덕션 설정은 코드에 하드코딩하지 않고 환경변수로 관리합니다:

```
# .env 파일 (git에 포함하지 않음!)
MCP_SERVER_PORT=8000
MCP_LOG_LEVEL=INFO
JWT_SECRET=your-production-secret-key
DATA_DIR=/app/data
LOG_DIR=/app/logs
```

docker-compose의 `env_file` 지시어로 `.env` 파일을 컨테이너에 전달합니다.

### 2.5 볼륨 마운트와 헬스체크

**볼륨 마운트**: 컨테이너가 재시작되어도 데이터가 유지되어야 하는 디렉토리를 호스트에 마운트합니다:
- `data/`: 재고 데이터, 정책 문서
- `logs/`: 감사 로그 (EP14에서 구현한 AuditLogger의 JSONL 파일)

**헬스체크**: 컨테이너 오케스트레이터(Docker, Kubernetes)가 서버 상태를 확인하는 엔드포인트:
- `GET /health` → `{"status": "healthy"}`
- 30초마다 확인, 3회 연속 실패 시 컨테이너 재시작

---

## 3. 라이브 데모 (10분)

### Step 1: 헬스체크 엔드포인트 추가

서버에 `/health` 엔드포인트를 추가합니다:

```python
# src/health.py
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import time

_start_time = time.time()

async def health_check(request: Request) -> JSONResponse:
    """헬스체크 엔드포인트"""
    uptime = time.time() - _start_time
    return JSONResponse({
        "status": "healthy",
        "uptime_seconds": round(uptime, 1),
        "version": "1.0.0",
    })

health_routes = [Route("/health", health_check)]
```

### Step 2: Dockerfile 작성

프로젝트 루트에 `Dockerfile`을 생성합니다:

```dockerfile
# ============================================================
# Stage 1: Builder — 의존성 설치
# ============================================================
FROM python:3.11-slim AS builder

# uv 설치 (공식 이미지에서 바이너리 복사)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 먼저 복사 (레이어 캐싱)
COPY pyproject.toml uv.lock ./

# 의존성 설치 (프로덕션만, lock 파일 기준)
RUN uv sync --frozen --no-dev

# 소스 코드와 데이터 복사
COPY src/ src/
COPY data/ data/

# ============================================================
# Stage 2: Runner — 실행 환경
# ============================================================
FROM python:3.11-slim AS runner

# 보안: 비-root 사용자 생성
RUN groupadd -r mcp && useradd -r -g mcp -s /bin/false mcp

# 작업 디렉토리 설정
WORKDIR /app

# Builder 스테이지에서 앱 복사
COPY --from=builder /app /app

# uv 바이너리도 복사 (실행 시 필요)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 로그 디렉토리 생성 및 권한 설정
RUN mkdir -p /app/logs && chown -R mcp:mcp /app

# 비-root 사용자로 전환
USER mcp

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 서버 실행
CMD ["uv", "run", "python", "src/server.py", "--transport", "streamable-http", "--port", "8000"]
```

### Step 3: .dockerignore 작성

불필요한 파일이 이미지에 포함되지 않도록 합니다:

```
# .dockerignore
__pycache__/
*.pyc
.git/
.github/
.env
.venv/
*.egg-info/
tests/
docs/
*.md
!README.md
.pytest_cache/
.mypy_cache/
```

### Step 4: Docker 이미지 빌드 및 실행

macOS/Linux:
```bash
# 이미지 빌드
docker build -t ops-assistant:latest .

# 이미지 크기 확인
docker images ops-assistant

# 컨테이너 실행
docker run -d \
  --name ops-assistant \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  ops-assistant:latest

# 헬스체크 확인
curl http://localhost:8000/health

# 로그 확인
docker logs ops-assistant

# 컨테이너 중지 & 삭제
docker stop ops-assistant && docker rm ops-assistant
```

Windows (PowerShell):
```powershell
# 이미지 빌드
docker build -t ops-assistant:latest .

# 이미지 크기 확인
docker images ops-assistant

# 컨테이너 실행
docker run -d `
  --name ops-assistant `
  -p 8000:8000 `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/logs:/app/logs `
  --env-file .env `
  ops-assistant:latest

# 헬스체크 확인
Invoke-RestMethod -Uri http://localhost:8000/health

# 로그 확인
docker logs ops-assistant

# 컨테이너 중지 & 삭제
docker stop ops-assistant; docker rm ops-assistant
```

### Step 5: docker-compose 구성

MCP 서버와 부가 서비스를 함께 관리하는 `docker-compose.yml`을 작성합니다:

```yaml
# docker-compose.yml
version: "3.9"

services:
  # ---- MCP 서버 ----
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ops-assistant
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file: .env
    environment:
      - MCP_SERVER_PORT=8000
      - MCP_LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    restart: unless-stopped
    networks:
      - mcp-network
    depends_on:
      redis:
        condition: service_healthy

  # ---- Redis (캐싱 & Rate Limiting) ----
  redis:
    image: redis:7-alpine
    container_name: ops-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped
    networks:
      - mcp-network

  # ---- Prometheus (메트릭 수집) ----
  prometheus:
    image: prom/prometheus:latest
    container_name: ops-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    restart: unless-stopped
    networks:
      - mcp-network

volumes:
  redis-data:
  prometheus-data:

networks:
  mcp-network:
    driver: bridge
```

### Step 6: Prometheus 설정 파일

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "mcp-server"
    static_configs:
      - targets: ["mcp-server:9090"]
    metrics_path: /metrics
```

### Step 7: docker-compose 실행

macOS/Linux:
```bash
# 전체 스택 빌드 & 실행
docker compose up -d --build

# 상태 확인
docker compose ps

# 서비스별 로그 확인
docker compose logs mcp-server
docker compose logs redis

# 헬스체크 확인
curl http://localhost:8000/health

# 전체 스택 중지
docker compose down

# 볼륨 포함 완전 삭제
docker compose down -v
```

Windows (PowerShell):
```powershell
# 전체 스택 빌드 & 실행
docker compose up -d --build

# 상태 확인
docker compose ps

# 서비스별 로그 확인
docker compose logs mcp-server
docker compose logs redis

# 헬스체크 확인
Invoke-RestMethod -Uri http://localhost:8000/health

# 전체 스택 중지
docker compose down

# 볼륨 포함 완전 삭제
docker compose down -v
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- Docker는 MCP 서버를 **어디서든 동일한 환경**으로 실행하게 합니다
- **멀티스테이지 빌드**로 빌드 환경과 실행 환경을 분리하여 이미지 크기를 줄입니다
- uv + Docker 조합에서는 `pyproject.toml` + `uv.lock`을 먼저 복사하여 **레이어 캐싱**을 활용합니다
- **docker-compose**로 MCP 서버, Redis, Prometheus를 통합 관리합니다
- **헬스체크**는 컨테이너 오케스트레이터가 서버 상태를 모니터링하는 핵심 장치입니다
- 보안을 위해 **비-root 사용자**로 컨테이너를 실행합니다

### 퀴즈

1. 멀티스테이지 빌드의 주요 이점은?
   → 빌드 도구와 캐시를 최종 이미지에서 제거하여 이미지 크기를 줄이고 보안 표면을 감소시킴

2. `pyproject.toml`과 `uv.lock`을 소스 코드보다 먼저 복사하는 이유는?
   → Docker 레이어 캐싱을 활용하여 소스 코드만 변경 시 의존성 재설치를 생략하기 위함

3. docker-compose에서 `depends_on`과 `condition: service_healthy`의 역할은?
   → Redis가 완전히 시작되고 헬스체크를 통과한 후에 MCP 서버를 시작하도록 순서를 보장

### 다음 편 예고

Docker로 서버를 배포할 준비가 되었습니다. 하지만 LLM이 도구를 무한 루프로 호출하면 어떻게 될까요? EP24에서 **Rate Limiting과 Caching**으로 서버를 보호하는 방법을 다룹니다.
