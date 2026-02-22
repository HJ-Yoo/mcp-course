# EP 22 — OAuth 2.1 & 인증 게이트웨이

> Module E (Advanced) · 약 20분

## 학습 목표

1. MCP 스펙에서 인증이 필요한 이유와 인증 섹션의 구조를 설명할 수 있다
2. OAuth 2.1 핵심 흐름(Authorization Code + PKCE)을 이해하고 도식화할 수 있다
3. FastMCP 서버에 인증 미들웨어를 설계하고 구현할 수 있다

---

## 1. 인트로 (2분)

EP21까지 우리는 Internal Ops Assistant를 완성했습니다. Tools, Resources, Prompts를 구현하고, 감사 로깅, 입력 검증, 테스트까지 마쳤죠. 하지만 한 가지 치명적인 문제가 남아 있습니다.

> "지금 우리 서버는 **누구나** 접근할 수 있습니다."

로컬 stdio 전송에서는 큰 문제가 아니었지만, Streamable HTTP로 원격 배포하는 순간 보안은 필수입니다. 재고 데이터를 아무나 조회하고, 티켓을 아무나 생성할 수 있다면 프로덕션에서 쓸 수 없겠죠.

이번 에피소드에서는 **MCP 인증 스펙**, **OAuth 2.1의 핵심 흐름**, 그리고 **FastMCP에서 인증 미들웨어를 구현**하는 방법을 알아보겠습니다.

---

## 2. 핵심 개념 (6분)

### 2.1 왜 MCP에 인증이 필요한가?

MCP 서버가 프로덕션에 배포되면 세 가지 상황이 발생합니다:

1. **다중 사용자**: 여러 사람이 같은 MCP 서버에 접속합니다. 누가 어떤 요청을 보냈는지 식별해야 합니다.
2. **원격 서버**: 로컬이 아닌 네트워크를 통해 접근합니다. 중간에 요청이 가로채질 수 있습니다.
3. **민감 데이터**: 재고 정보, 인사 정책, 티켓 내용 등은 인가된 사용자만 접근해야 합니다.

```
인증 없는 MCP 서버:
┌──────────┐     HTTP      ┌──────────────┐
│ 아무나    │ ──────────── │ MCP 서버      │
│ (공격자?) │   열린 문     │ 민감 데이터   │
└──────────┘              └──────────────┘

인증 있는 MCP 서버:
┌──────────┐   Bearer     ┌──────────────┐
│ 인증된    │ ──Token───── │ MCP 서버      │
│ 사용자    │   🔒 검증    │ 민감 데이터   │
└──────────┘              └──────────────┘
```

### 2.2 MCP 스펙의 인증 섹션

2025년 MCP 스펙은 인증에 대해 다음과 같은 원칙을 제시합니다:

- **전송 계층 독립**: MCP 프로토콜 자체는 인증을 강제하지 않습니다. 전송 계층(HTTP)에서 처리합니다.
- **Bearer Token 방식**: HTTP 기반 전송에서는 `Authorization: Bearer <token>` 헤더를 사용합니다.
- **OAuth 2.1 권장**: 서버가 인증을 요구하는 경우 OAuth 2.1을 표준 흐름으로 권장합니다.

인증 흐름의 전체 시퀀스는 다음과 같습니다:

```
[클라이언트]                [MCP 서버]              [OAuth Provider]
    │                          │                          │
    │── 1. 요청 (토큰 없음) ──→│                          │
    │←─ 2. 401 Unauthorized ──│                          │
    │   WWW-Authenticate:     │                          │
    │   Bearer               │                          │
    │                          │                          │
    │── 3. Authorization Code + PKCE ─────────────────→│
    │←─ 4. Authorization Code ─────────────────────────│
    │── 5. Code → Token 교환 ──────────────────────────→│
    │←─ 6. Access Token ───────────────────────────────│
    │                          │                          │
    │── 7. 요청 + Bearer Token→│                          │
    │←─ 8. 200 OK (응답) ─────│                          │
```

### 2.3 OAuth 2.1 핵심: Authorization Code + PKCE

OAuth 2.1은 OAuth 2.0의 모범 사례를 통합한 업데이트입니다. 핵심 변경 사항:

- **Implicit Grant 제거**: 보안 취약점 때문에 완전히 제거되었습니다
- **PKCE 필수화**: 모든 Authorization Code 흐름에 PKCE(Proof Key for Code Exchange)가 필수입니다
- **Refresh Token Rotation**: Refresh Token은 일회용으로, 사용 시 새로운 Refresh Token이 발급됩니다

**PKCE 흐름**:

```
1. 클라이언트가 code_verifier (랜덤 문자열) 생성
2. code_challenge = BASE64URL(SHA256(code_verifier))
3. 인증 요청에 code_challenge 포함
4. 토큰 교환 시 code_verifier 전송
5. 서버가 SHA256(code_verifier) == code_challenge 확인

→ 중간에 authorization code를 탈취해도 code_verifier 없이는 토큰 교환 불가
```

### 2.4 토큰 검증: JWT

서버 측에서 Bearer Token을 검증하는 가장 일반적인 방법은 **JWT(JSON Web Token)**입니다:

```python
import jwt
from datetime import datetime, timezone

def verify_jwt(token: str, secret: str, audience: str) -> dict:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=audience,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("토큰이 만료되었습니다")
    except jwt.InvalidAudienceError:
        raise ValueError("유효하지 않은 audience입니다")
    except jwt.InvalidTokenError:
        raise ValueError("유효하지 않은 토큰입니다")
```

검증 항목:
- **서명 확인**: 토큰이 변조되지 않았는지 확인
- **만료 확인**: `exp` 클레임으로 토큰 유효기간 확인
- **Audience 확인**: 토큰이 이 서버용인지 확인
- **Scope 확인**: 요청된 작업에 필요한 권한이 있는지 확인

### 2.5 인증 게이트웨이 패턴

MCP 서버 자체에 인증 로직을 넣는 대신, **인증 게이트웨이(프록시)**를 앞에 두는 패턴도 있습니다:

```
┌──────────┐     ┌──────────────────┐     ┌──────────────┐
│ 클라이언트 │────→│ 인증 게이트웨이    │────→│ MCP 서버      │
│          │     │ (Nginx/Envoy/    │     │ (인증 없음)   │
│          │←────│  custom proxy)   │←────│              │
└──────────┘     └──────────────────┘     └──────────────┘
                  - JWT 검증                - 비즈니스 로직만
                  - Rate limiting           - 게이트웨이가 보낸
                  - TLS termination           요청만 신뢰
```

장점:
- MCP 서버 코드가 인증 로직과 분리됨 (관심사 분리)
- 여러 MCP 서버에 동일한 인증 정책 적용 가능
- Nginx, Envoy 등 검증된 프록시 사용 가능

단점:
- 인프라 복잡도 증가
- 사용자 정보를 서버에 전달하는 추가 헤더 필요 (X-User-Id 등)

---

## 3. 라이브 데모 (10분)

### Step 1: 필요한 패키지 설치

macOS/Linux:
```bash
cd /path/to/ops-assistant
uv add PyJWT starlette
```

Windows (PowerShell):
```powershell
cd C:\path\to\ops-assistant
uv add PyJWT starlette
```

### Step 2: 인증 백엔드 구현

`src/auth.py` 파일을 생성합니다:

```python
"""MCP 서버 인증 모듈"""

import jwt
import time
import secrets
import hashlib
import base64
from dataclasses import dataclass
from typing import Optional

# --- 설정 ---
JWT_SECRET = "your-secret-key-change-in-production"  # 프로덕션에서는 환경변수로!
JWT_ALGORITHM = "HS256"
JWT_AUDIENCE = "ops-assistant"
TOKEN_EXPIRY_SECONDS = 3600  # 1시간


@dataclass
class User:
    """인증된 사용자 정보"""
    user_id: str
    name: str
    scopes: list[str]


def create_token(user_id: str, name: str, scopes: list[str]) -> str:
    """테스트용 JWT 토큰 생성"""
    payload = {
        "sub": user_id,
        "name": name,
        "scopes": scopes,
        "aud": JWT_AUDIENCE,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> User:
    """JWT 토큰 검증 후 User 객체 반환"""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
        )
        return User(
            user_id=payload["sub"],
            name=payload["name"],
            scopes=payload.get("scopes", []),
        )
    except jwt.ExpiredSignatureError:
        raise PermissionError("토큰이 만료되었습니다")
    except jwt.InvalidTokenError as e:
        raise PermissionError(f"유효하지 않은 토큰: {e}")


# --- PKCE 유틸리티 ---

def generate_pkce_pair() -> tuple[str, str]:
    """PKCE code_verifier와 code_challenge 쌍 생성"""
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    """PKCE code_verifier 검증"""
    digest = hashlib.sha256(code_verifier.encode()).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return secrets.compare_digest(expected, code_challenge)
```

### Step 3: 인증 미들웨어 구현

`src/auth_middleware.py` 파일을 생성합니다:

```python
"""Starlette 인증 미들웨어 for MCP 서버"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from auth import verify_token, User
from typing import Optional

# 인증이 필요 없는 경로들
PUBLIC_PATHS = {"/health", "/metrics"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Bearer Token 인증 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        # 공개 경로는 인증 스킵
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "인증이 필요합니다"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.removeprefix("Bearer ")

        try:
            user = verify_token(token)
        except PermissionError as e:
            return JSONResponse(
                status_code=401,
                content={"error": str(e)},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 사용자 정보를 request.state에 저장
        request.state.user = user

        # 다음 미들웨어/핸들러로 전달
        response = await call_next(request)
        return response


def get_current_user(request: Request) -> Optional[User]:
    """요청에서 현재 사용자 정보 추출"""
    return getattr(request.state, "user", None)
```

### Step 4: 서버에 미들웨어 적용

`src/server.py`에 미들웨어를 적용합니다:

```python
from mcp.server.fastmcp import FastMCP
from auth_middleware import AuthMiddleware

mcp = FastMCP(
    "Ops Assistant",
    # Streamable HTTP 전송 시 미들웨어 적용
    middleware=[AuthMiddleware],
)

# 기존 도구들은 그대로 유지...
# @mcp.tool()
# async def lookup_inventory(...): ...
```

### Step 5: 인증 테스트

테스트용 토큰을 생성하고 확인합니다:

macOS/Linux:
```bash
# 서버 시작
uv run python src/server.py --transport streamable-http --port 8000 &

# 1) 인증 없이 접근 → 401 예상
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool

# 2) 테스트 토큰 생성
TOKEN=$(uv run python -c "
from auth import create_token
token = create_token('user-001', 'Alice', ['read', 'write'])
print(token)
")
echo "Token: $TOKEN"

# 3) 유효한 토큰으로 접근 → 200 예상
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool
```

Windows (PowerShell):
```powershell
# 서버 시작
Start-Process -NoNewWindow uv -ArgumentList "run", "python", "src/server.py", "--transport", "streamable-http", "--port", "8000"

# 1) 인증 없이 접근 → 401 예상
$body = '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
Invoke-RestMethod -Uri http://localhost:8000/mcp -Method POST -ContentType "application/json" -Body $body

# 2) 테스트 토큰 생성
$token = uv run python -c "from auth import create_token; print(create_token('user-001', 'Alice', ['read', 'write']))"
Write-Host "Token: $token"

# 3) 유효한 토큰으로 접근 → 200 예상
$headers = @{ "Authorization" = "Bearer $token" }
Invoke-RestMethod -Uri http://localhost:8000/mcp -Method POST -ContentType "application/json" -Headers $headers -Body $body
```

### Step 6: Scope 기반 권한 검사

도구별로 필요한 scope를 검사하는 헬퍼를 추가합니다:

```python
def require_scope(user: User, required: str) -> None:
    """사용자가 특정 scope를 가지고 있는지 확인"""
    if required not in user.scopes:
        raise PermissionError(
            f"권한 부족: '{required}' scope가 필요합니다. "
            f"현재 scope: {user.scopes}"
        )

# 도구에서 사용 예시
@mcp.tool()
async def create_ticket(title: str, description: str) -> str:
    """티켓 생성 (write scope 필요)"""
    user = get_current_user_from_context()
    require_scope(user, "write")
    # ... 티켓 생성 로직
```

### Step 7: OAuth 2.1 PKCE 플로우 다이어그램

전체 PKCE 흐름을 ASCII art로 정리합니다:

```
  ┌──────────────┐                      ┌──────────────┐                      ┌──────────────┐
  │  MCP Client  │                      │  MCP Server   │                      │ OAuth Server │
  │  (Claude 등)  │                      │  (우리 서버)  │                      │ (IdP)        │
  └──────┬───────┘                      └──────┬───────┘                      └──────┬───────┘
         │                                      │                                      │
         │  1. POST /mcp (토큰 없음)            │                                      │
         │─────────────────────────────────────→│                                      │
         │                                      │                                      │
         │  2. 401 + WWW-Authenticate: Bearer   │                                      │
         │←─────────────────────────────────────│                                      │
         │                                      │                                      │
         │  3. code_verifier 생성                │                                      │
         │     code_challenge = SHA256(verifier) │                                      │
         │                                      │                                      │
         │  4. GET /authorize?                   │                                      │
         │     response_type=code&               │                                      │
         │     code_challenge=XXX&               │                                      │
         │     code_challenge_method=S256        │                                      │
         │──────────────────────────────────────────────────────────────────────────────→│
         │                                      │                                      │
         │  5. 사용자 로그인 & 동의              │                                      │
         │←─────────────────────────────────── (브라우저 리다이렉트) ───────────────────│
         │                                      │                                      │
         │  6. POST /token                       │                                      │
         │     code=AUTH_CODE&                   │                                      │
         │     code_verifier=VERIFIER            │                                      │
         │──────────────────────────────────────────────────────────────────────────────→│
         │                                      │                                      │
         │  7. { access_token, refresh_token }   │                                      │
         │←─────────────────────────────────────────────────────────────────────────────│
         │                                      │                                      │
         │  8. POST /mcp + Bearer <access_token> │                                      │
         │─────────────────────────────────────→│                                      │
         │                                      │                                      │
         │  9. 200 OK (정상 응답)                │                                      │
         │←─────────────────────────────────────│                                      │
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- MCP 서버가 원격으로 배포되면 **인증은 필수**입니다
- MCP 스펙은 **Bearer Token + OAuth 2.1**을 인증 표준으로 권장합니다
- OAuth 2.1에서는 **PKCE가 필수**이며 Implicit Grant는 제거되었습니다
- 인증 로직은 **미들웨어**로 분리하여 비즈니스 로직과 관심사를 분리합니다
- **인증 게이트웨이 패턴**으로 여러 MCP 서버에 공통 인증 정책을 적용할 수 있습니다

### 퀴즈

1. MCP 스펙에서 인증이 필요한 세 가지 이유는?
   → 다중 사용자 식별, 원격 서버 보안, 민감 데이터 보호

2. OAuth 2.1에서 PKCE가 필수인 이유는?
   → Authorization Code 탈취 시 code_verifier 없이는 토큰 교환이 불가능하여 보안이 강화됨

3. 인증 게이트웨이 패턴의 장점은?
   → MCP 서버 코드에서 인증 로직을 분리하고, 여러 서버에 동일한 인증 정책을 적용할 수 있음

### 다음 편 예고

인증을 구현했으니, 이제 우리 서버를 **어디서든 동일하게 실행**할 수 있도록 Docker 컨테이너화를 진행합니다. EP23에서 멀티스테이지 빌드와 docker-compose 구성을 다룹니다.
