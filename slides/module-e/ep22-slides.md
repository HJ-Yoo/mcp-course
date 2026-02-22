---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 22 — OAuth 2.1 & 인증 게이트웨이"
---

# EP 22 — OAuth 2.1 & 인증 게이트웨이
## Module E (Advanced) · MCP 실전 마스터

---

## 학습 목표

1. MCP 스펙에서 인증이 필요한 이유를 설명할 수 있다
2. OAuth 2.1 핵심 흐름 (Authorization Code + PKCE)을 이해한다
3. FastMCP 서버에 인증 미들웨어를 구현할 수 있다

---

## 왜 인증이 필요한가?

| 상황 | 위험 |
|------|------|
| **다중 사용자** | 누가 요청했는지 식별 불가 |
| **원격 서버** | 네트워크에서 요청 가로채기 |
| **민감 데이터** | 비인가 접근으로 데이터 유출 |

> EP21까지의 서버는 **누구나 접근 가능** — 프로덕션에서는 치명적!

---

## MCP 스펙의 인증 원칙

- **전송 계층 독립**: MCP 프로토콜 자체는 인증 강제 안 함
- **Bearer Token**: `Authorization: Bearer <token>` 헤더 사용
- **OAuth 2.1 권장**: 서버가 인증 요구 시 표준 흐름

```
클라이언트 → MCP 서버: 요청 (토큰 없음)
MCP 서버 → 클라이언트: 401 + WWW-Authenticate: Bearer
클라이언트 → OAuth Provider: 인증 흐름
클라이언트 → MCP 서버: 요청 + Bearer Token → 200 OK
```

---

## OAuth 2.1 = OAuth 2.0 + 보안 강화

| 변경사항 | 이유 |
|---------|------|
| Implicit Grant **제거** | 보안 취약점 |
| PKCE **필수화** | Authorization Code 탈취 방지 |
| Refresh Token **회전** | 토큰 재사용 방지 |

---

## PKCE 흐름

```
1. code_verifier = 랜덤 문자열 생성
2. code_challenge = BASE64URL(SHA256(code_verifier))
3. 인증 요청에 code_challenge 포함
4. 토큰 교환 시 code_verifier 전송
5. 서버: SHA256(code_verifier) == code_challenge 확인
```

> 중간에 authorization code를 탈취해도
> `code_verifier` 없이는 토큰 교환 **불가**

---

## JWT 토큰 검증

```python
def verify_token(token: str) -> User:
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=["HS256"],
        audience="ops-assistant",
    )
    return User(
        user_id=payload["sub"],
        name=payload["name"],
        scopes=payload.get("scopes", []),
    )
```

검증 항목: **서명** → **만료** → **Audience** → **Scope**

---

## 인증 미들웨어 구현

```python
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = verify_token(auth.removeprefix("Bearer "))
        request.state.user = user
        return await call_next(request)
```

---

## 데모: 인증 테스트

```bash
# 1) 인증 없이 → 401
curl http://localhost:8000/mcp \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# 2) 토큰 생성
TOKEN=$(uv run python -c "
from auth import create_token
print(create_token('user-001', 'Alice', ['read','write']))
")

# 3) 토큰으로 → 200
curl http://localhost:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

---

## Scope 기반 권한 검사

```python
def require_scope(user: User, required: str):
    if required not in user.scopes:
        raise PermissionError(f"'{required}' scope 필요")

@mcp.tool()
async def create_ticket(title: str, description: str):
    user = get_current_user()
    require_scope(user, "write")  # write 권한 필요
    ...
```

**read** scope → 조회만 / **write** scope → 생성/수정 가능

---

## 인증 게이트웨이 패턴

```
클라이언트 → [인증 게이트웨이] → MCP 서버
              (JWT 검증,          (비즈니스
               Rate Limit,         로직만)
               TLS 종료)
```

- 장점: 관심사 분리, 여러 서버에 동일 정책
- 단점: 인프라 복잡도 증가, 추가 레이턴시

---

## 핵심 정리

- MCP 원격 배포 시 **인증은 필수**
- **OAuth 2.1 + PKCE**가 표준 흐름
- 인증은 **미들웨어**로 분리하여 비즈니스 로직과 독립
- **Scope 기반 권한 검사**로 세밀한 접근 제어
- **인증 게이트웨이**로 공통 정책 중앙 관리 가능

---

## 다음 편 예고

**EP 23 — Docker 컨테이너화**

인증된 서버를 어디서든 동일하게 실행하기 위한
멀티스테이지 빌드와 docker-compose 구성
