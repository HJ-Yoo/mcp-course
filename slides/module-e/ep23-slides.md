---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 23 — Docker 컨테이너화"
---

# EP 23 — Docker 컨테이너화
## Module E (Advanced) · MCP 실전 마스터

---

## 학습 목표

1. MCP 서버를 Docker 이미지로 빌드할 수 있다
2. 멀티스테이지 빌드로 이미지 사이즈를 최적화할 수 있다
3. docker-compose로 MCP 서버 + 부가 서비스를 통합 구성할 수 있다

---

## 왜 컨테이너화인가?

```
기존: "내 컴퓨터에서는 되는데..."
  macOS → Python 3.11 + pip
  Ubuntu → Python 3.10 + apt
  Windows → Python 3.12 + pip
  = 3개의 배포 스크립트 유지관리

Docker: 어디서든 동일하게
  모든 환경 → docker run ops-assistant:latest
  = Dockerfile 하나로 통일
```

---

## 컨테이너화의 3대 이점

| 이점 | 설명 | MCP 서버 적용 |
|------|------|--------------|
| **일관된 환경** | 어디서든 동일 실행 | Python/의존성 통일 |
| **배포 용이성** | 이미지 하나로 배포 | `docker pull` + `run` |
| **스케일링** | 컨테이너 복제로 확장 | 인스턴스 추가 |

---

## Python + uv Dockerfile 전략

```dockerfile
# 나쁜 예: 캐시 무효화
COPY . .
RUN uv sync

# 좋은 예: 레이어 캐싱 활용
COPY pyproject.toml uv.lock ./    # 의존성 파일만 먼저
RUN uv sync --frozen --no-dev     # 의존성 레이어 캐싱
COPY src/ src/                     # 소스는 나중에
```

> 소스 코드만 변경 시 의존성 재설치 **생략**

---

## 멀티스테이지 빌드

```
┌─────────────────────┐    ┌─────────────────────┐
│ Stage 1: builder    │    │ Stage 2: runner      │
│                     │    │                     │
│ Python 3.11-slim    │    │ Python 3.11-slim    │
│ + uv 설치           │───→│ 빌드된 앱만 복사     │
│ + 모든 의존성       │    │ 빌드 도구 없음       │
│                     │    │                     │
│ ~800MB              │    │ ~150MB              │
└─────────────────────┘    └─────────────────────┘
```

이미지 크기 **80% 절감** + 보안 표면 축소

---

## Dockerfile 핵심

```dockerfile
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ src/

FROM python:3.11-slim AS runner
RUN useradd -r -s /bin/false mcp    # 비-root 사용자
WORKDIR /app
COPY --from=builder /app /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
USER mcp
EXPOSE 8000
CMD ["uv", "run", "python", "src/server.py",
     "--transport", "streamable-http", "--port", "8000"]
```

---

## 헬스체크 엔드포인트

```python
async def health_check(request):
    return JSONResponse({
        "status": "healthy",
        "uptime_seconds": round(time.time() - _start, 1),
        "version": "1.0.0",
    })
```

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; \
  urllib.request.urlopen('http://localhost:8000/health')"
```

---

## docker-compose 구성

```yaml
services:
  mcp-server:
    build: .
    ports: ["8000:8000"]
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file: .env
    depends_on:
      redis: { condition: service_healthy }

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
```

---

## 데모: 빌드 & 실행

```bash
# macOS/Linux
docker build -t ops-assistant:latest .
docker images ops-assistant    # 이미지 크기 확인

docker run -d --name ops-assistant \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  ops-assistant:latest

curl http://localhost:8000/health
```

```powershell
# Windows (PowerShell)
docker build -t ops-assistant:latest .
docker run -d --name ops-assistant `
  -p 8000:8000 -v ${PWD}/data:/app/data `
  --env-file .env ops-assistant:latest
```

---

## 환경변수 관리

```bash
# .env (git에 포함 X)
MCP_SERVER_PORT=8000
MCP_LOG_LEVEL=INFO
JWT_SECRET=your-production-secret
DATA_DIR=/app/data
LOG_DIR=/app/logs
```

- 비밀값은 **절대** 코드에 하드코딩하지 않음
- `.env`는 `.gitignore`에 반드시 포함
- `.env.example`로 필요한 변수 목록 문서화

---

## 볼륨 마운트 전략

| 디렉토리 | 용도 | 마운트 이유 |
|---------|------|-----------|
| `data/` | 재고, 정책 문서 | 컨테이너 재시작 시 데이터 보존 |
| `logs/` | 감사 로그 (EP14) | 로그 파일 호스트에서 접근 |

> 컨테이너는 **일시적(ephemeral)** — 볼륨 없으면 데이터 소실

---

## docker-compose 운영 명령어

```bash
# 전체 스택 시작
docker compose up -d --build

# 상태 확인
docker compose ps

# 서비스별 로그
docker compose logs mcp-server

# 전체 중지
docker compose down

# 볼륨 포함 완전 삭제
docker compose down -v
```

---

## 핵심 정리

- Docker로 **어디서든 동일한 환경** 보장
- **멀티스테이지 빌드**로 이미지 크기 80% 절감
- **레이어 캐싱**: pyproject.toml 먼저 복사
- **docker-compose**로 서버 + Redis + Prometheus 통합
- **헬스체크**로 자동 상태 모니터링
- **비-root 사용자**로 보안 강화

---

## 다음 편 예고

**EP 24 — Rate Limiting & Caching**

LLM이 도구를 무한 반복 호출하면?
Rate Limiter와 TTL Cache로 서버를 보호하는 방법
