# EP 24 — Rate Limiting & Caching

> Module E (Advanced) · 약 20분

## 학습 목표

1. MCP 서버에 Rate Limiting이 필요한 이유를 이해하고 Token Bucket 알고리즘을 설명할 수 있다
2. In-memory 및 Redis 기반 Rate Limiter를 구현할 수 있다
3. TTL 기반 캐시를 구현하여 반복 요청의 성능을 최적화할 수 있다

---

## 1. 인트로 (2분)

EP23에서 Docker로 서버를 컨테이너화했습니다. 이제 어디서든 동일하게 배포할 수 있지만, 새로운 위협이 기다리고 있습니다.

> "LLM이 도구를 무한 반복 호출하면 어떻게 될까요?"

LLM은 때때로 예상치 못한 행동을 합니다. 같은 도구를 수십 번 연속으로 호출하거나, 에러 시 재시도를 무한 반복하는 경우가 실제로 발생합니다. 이런 상황에서 서버를 보호하지 않으면 리소스가 고갈되고, 비용이 폭증하고, 다른 사용자의 요청이 지연됩니다.

이번 에피소드에서는 **Rate Limiting**으로 API 남용을 방지하고, **Caching**으로 반복 요청의 성능을 최적화하는 방법을 다룹니다.

---

## 2. 핵심 개념 (6분)

### 2.1 왜 Rate Limiting인가?

MCP 서버에서 Rate Limiting이 특히 중요한 이유:

```
일반 API:   사람이 직접 호출 → 자연스러운 속도 제한
MCP 서버:   LLM이 자동 호출 → 초당 수십~수백 회 가능

시나리오 1: 무한 루프
  LLM: "재고를 확인해야겠다" → lookup_inventory 호출
  LLM: "아, 다시 확인해야겠다" → lookup_inventory 호출
  LLM: "한 번 더..." → lookup_inventory 호출
  ... (수백 회 반복)

시나리오 2: 에러 재시도 폭주
  LLM: create_ticket 호출 → 에러
  LLM: "다시 시도" → 에러
  LLM: "다시 시도" → 에러
  ... (서버 과부하 발생)
```

Rate Limiting의 목적:
- **비용 통제**: 외부 API 호출 비용 제한
- **서버 보호**: 리소스 고갈 방지
- **공정성**: 다중 사용자 환경에서 공정한 리소스 분배
- **안정성**: 예상 가능한 서버 동작 보장

### 2.2 Token Bucket 알고리즘

가장 널리 사용되는 Rate Limiting 알고리즘인 **Token Bucket**을 이해합시다:

```
Token Bucket 알고리즘:

  ┌─────────────────────┐
  │   Bucket (용량: 10)  │     ← 최대 10개 토큰 보관
  │  ○ ○ ○ ○ ○ ○ ○ ○   │     ← 현재 8개 토큰
  │                     │
  └──────────┬──────────┘
             │ 요청당 1개 소비
             ▼
       [API 요청 처리]

  토큰 보충: 매 초 1개씩 추가 (rate)
  최대 용량: 10개 (burst)
  토큰 = 0이면: 429 Too Many Requests

  장점: 순간적 burst 허용 + 평균 속도 제한
```

다른 알고리즘과 비교:

| 알고리즘 | 특징 | 적합한 경우 |
|---------|------|-----------|
| **Token Bucket** | Burst 허용, 평균 속도 제한 | 일반적 API |
| **Sliding Window** | 정확한 윈도우 카운팅 | 정밀한 제한 필요 |
| **Fixed Window** | 구현 단순, 경계 문제 | 간단한 시스템 |
| **Leaky Bucket** | 일정 속도 출력 | 일정한 처리율 필요 |

### 2.3 Rate Limit 적용 포인트

Rate Limit은 여러 수준에서 적용할 수 있습니다:

```
┌─────────────────────────────────────────────┐
│ Level 1: 전체 서버 (Global)                   │
│   - 전체 요청: 1000/분                       │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │ Level 2: 사용자별 (Per-User)         │   │
│   │   - user-001: 100/분               │   │
│   │   - user-002: 100/분               │   │
│   │                                     │   │
│   │   ┌─────────────────────────────┐   │   │
│   │   │ Level 3: 도구별 (Per-Tool)   │   │   │
│   │   │   - lookup_inventory: 30/분  │   │   │
│   │   │   - create_ticket: 10/분     │   │   │
│   │   │   - search_policy: 20/분     │   │   │
│   │   └─────────────────────────────┘   │   │
│   └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 2.4 캐싱 전략

반복 요청에 대해 동일한 결과를 돌려주는 **캐싱**은 성능 최적화의 핵심입니다:

| 도구 | 캐시 TTL | 이유 |
|------|---------|------|
| `search_policy` | 5분 | 정책 문서는 자주 변경되지 않음 |
| `lookup_inventory` | 1분 | 재고는 비교적 자주 변동 |
| `create_ticket` | 캐시 안 함 | 부수 효과가 있는 쓰기 작업 |

**캐시 키 설계**: 도구 이름 + 입력 파라미터 조합

```python
cache_key = f"search_policy:{query}:{department}"
# 예: "search_policy:반품정책:고객지원"
```

### 2.5 Cache Invalidation 전략

> "컴퓨터 과학에서 어려운 것 두 가지: 캐시 무효화와 이름 짓기" — Phil Karlton

- **TTL 기반**: 일정 시간 후 자동 만료 (가장 단순)
- **이벤트 기반**: 데이터 변경 시 관련 캐시 삭제
- **버전 기반**: 캐시 키에 버전 포함 (`policy_v2:{query}`)

---

## 3. 라이브 데모 (10분)

### Step 1: In-memory Rate Limiter 구현

`src/rate_limiter.py` 파일을 생성합니다:

```python
"""MCP 서버 Rate Limiter"""

import time
from collections import defaultdict
from typing import Any


class RateLimiter:
    """Sliding Window 기반 Rate Limiter"""

    def __init__(self, max_calls: int = 10, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        """
        요청 허용 여부 확인.
        True = 허용, False = 제한 초과
        """
        now = time.monotonic()
        calls = self._calls[key]

        # 윈도우 밖의 호출 기록 제거
        self._calls[key] = [t for t in calls if now - t < self.window]

        # 제한 초과 확인
        if len(self._calls[key]) >= self.max_calls:
            return False

        # 현재 호출 기록
        self._calls[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        """남은 호출 가능 횟수"""
        now = time.monotonic()
        calls = [t for t in self._calls[key] if now - t < self.window]
        return max(0, self.max_calls - len(calls))

    def reset_time(self, key: str) -> float:
        """제한 초기화까지 남은 시간 (초)"""
        if not self._calls[key]:
            return 0.0
        oldest = min(t for t in self._calls[key]
                     if time.monotonic() - t < self.window)
        return max(0.0, self.window - (time.monotonic() - oldest))


# --- 기본 설정 ---
# 도구별 Rate Limiter 인스턴스
TOOL_LIMITS = {
    "lookup_inventory": RateLimiter(max_calls=30, window_seconds=60),
    "search_policy": RateLimiter(max_calls=20, window_seconds=60),
    "create_ticket": RateLimiter(max_calls=10, window_seconds=60),
}

# 전역 Rate Limiter (모든 도구 합산)
GLOBAL_LIMITER = RateLimiter(max_calls=100, window_seconds=60)


def check_rate_limit(tool_name: str, user_id: str = "anonymous") -> None:
    """
    Rate Limit 검사. 초과 시 예외 발생.

    Args:
        tool_name: 호출된 도구 이름
        user_id: 사용자 식별자

    Raises:
        RuntimeError: Rate Limit 초과 시
    """
    # 1) 전역 제한 확인
    global_key = f"global:{user_id}"
    if not GLOBAL_LIMITER.check(global_key):
        remaining_time = GLOBAL_LIMITER.reset_time(global_key)
        raise RuntimeError(
            f"전역 Rate Limit 초과. {remaining_time:.0f}초 후 다시 시도해주세요."
        )

    # 2) 도구별 제한 확인
    tool_limiter = TOOL_LIMITS.get(tool_name)
    if tool_limiter:
        tool_key = f"{tool_name}:{user_id}"
        if not tool_limiter.check(tool_key):
            remaining_time = tool_limiter.reset_time(tool_key)
            raise RuntimeError(
                f"{tool_name} Rate Limit 초과 "
                f"({tool_limiter.max_calls}회/{tool_limiter.window}초). "
                f"{remaining_time:.0f}초 후 다시 시도해주세요."
            )
```

### Step 2: TTL Cache 구현

`src/cache.py` 파일을 생성합니다:

```python
"""MCP 서버 TTL Cache"""

import time
import hashlib
import json
from typing import Any, Optional


class TTLCache:
    """Time-To-Live 기반 캐시"""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: dict[str, tuple[float, Any]] = {}
        self._hits = 0
        self._misses = 0

    def _make_key(self, tool_name: str, **kwargs) -> str:
        """캐시 키 생성 (도구 이름 + 파라미터 해시)"""
        params = json.dumps(kwargs, sort_keys=True, default=str)
        param_hash = hashlib.md5(params.encode()).hexdigest()[:12]
        return f"{tool_name}:{param_hash}"

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회. 만료되었으면 None 반환"""
        if key in self._cache:
            ts, value = self._cache[key]
            if time.monotonic() - ts < self.ttl:
                self._hits += 1
                return value
            # 만료된 항목 삭제
            del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        """캐시에 값 저장"""
        # 최대 크기 초과 시 가장 오래된 항목 제거
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        self._cache[key] = (time.monotonic(), value)

    def invalidate(self, key: str) -> bool:
        """특정 키의 캐시 무효화"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def invalidate_prefix(self, prefix: str) -> int:
        """접두사가 일치하는 모든 캐시 무효화"""
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)

    def clear(self) -> None:
        """전체 캐시 초기화"""
        self._cache.clear()

    def stats(self) -> dict:
        """캐시 통계"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }

    def _evict_oldest(self) -> None:
        """가장 오래된 캐시 항목 제거"""
        if self._cache:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]


# --- 도구별 캐시 인스턴스 ---
policy_cache = TTLCache(ttl_seconds=300)     # 정책 검색: 5분
inventory_cache = TTLCache(ttl_seconds=60)   # 재고 조회: 1분
```

### Step 3: 도구에 Rate Limiter & Cache 적용

기존 도구에 Rate Limiter와 Cache를 통합합니다:

```python
# src/server.py (관련 부분)
from rate_limiter import check_rate_limit
from cache import policy_cache, inventory_cache

@mcp.tool()
async def lookup_inventory(item_name: str) -> str:
    """재고 조회 (Rate Limited + Cached)"""
    # 1) Rate Limit 검사
    check_rate_limit("lookup_inventory", user_id="current_user")

    # 2) 캐시 확인
    cache_key = inventory_cache._make_key("lookup_inventory", item_name=item_name)
    cached = inventory_cache.get(cache_key)
    if cached is not None:
        return f"[캐시] {cached}"

    # 3) 실제 조회
    result = _do_inventory_lookup(item_name)

    # 4) 캐시 저장
    inventory_cache.set(cache_key, result)

    return result


@mcp.tool()
async def search_policy(query: str, department: str = "") -> str:
    """정책 검색 (Rate Limited + Cached)"""
    check_rate_limit("search_policy", user_id="current_user")

    cache_key = policy_cache._make_key("search_policy", query=query, department=department)
    cached = policy_cache.get(cache_key)
    if cached is not None:
        return f"[캐시] {cached}"

    result = _do_policy_search(query, department)
    policy_cache.set(cache_key, result)
    return result


@mcp.tool()
async def create_ticket(title: str, description: str, priority: str = "medium") -> str:
    """티켓 생성 (Rate Limited, 캐시 없음)"""
    check_rate_limit("create_ticket", user_id="current_user")

    # 쓰기 작업은 캐시하지 않음
    result = _do_create_ticket(title, description, priority)

    # 관련 캐시 무효화 (티켓 생성 시 재고 상태가 바뀔 수 있음)
    inventory_cache.invalidate_prefix("lookup_inventory")

    return result
```

### Step 4: 데코레이터 패턴으로 리팩토링

반복되는 Rate Limit + Cache 로직을 데코레이터로 추출합니다:

```python
# src/decorators.py
import functools
from rate_limiter import check_rate_limit
from cache import TTLCache


def rate_limited(tool_name: str):
    """Rate Limiting 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get("_user_id", "anonymous")
            check_rate_limit(tool_name, user_id)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def cached(cache: TTLCache, tool_name: str):
    """TTL 캐싱 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성 (내부 파라미터 제외)
            cache_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
            key = cache._make_key(tool_name, **cache_kwargs)

            # 캐시 확인
            result = cache.get(key)
            if result is not None:
                return result

            # 실행 & 캐싱
            result = await func(*args, **kwargs)
            cache.set(key, result)
            return result
        return wrapper
    return decorator


# 사용 예시:
# @mcp.tool()
# @rate_limited("search_policy")
# @cached(policy_cache, "search_policy")
# async def search_policy(query: str) -> str:
#     ...
```

### Step 5: Rate Limit 테스트

macOS/Linux:
```bash
# 서버 시작
cd /path/to/ops-assistant
uv run python src/server.py --transport streamable-http --port 8000 &

# 빠른 연속 호출로 Rate Limit 트리거
for i in $(seq 1 15); do
  echo "--- Request $i ---"
  curl -s -X POST http://localhost:8000/mcp \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
      "jsonrpc": "2.0",
      "id": '$i',
      "method": "tools/call",
      "params": {"name": "create_ticket", "arguments": {"title": "Test '$i'", "description": "test"}}
    }' | python -m json.tool
  sleep 0.1
done
```

Windows (PowerShell):
```powershell
# 빠른 연속 호출로 Rate Limit 트리거
for ($i = 1; $i -le 15; $i++) {
    Write-Host "--- Request $i ---"
    $body = @{
        jsonrpc = "2.0"
        id = $i
        method = "tools/call"
        params = @{ name = "create_ticket"; arguments = @{ title = "Test $i"; description = "test" } }
    } | ConvertTo-Json -Depth 5
    $headers = @{ "Authorization" = "Bearer $token" }
    try {
        Invoke-RestMethod -Uri http://localhost:8000/mcp -Method POST -ContentType "application/json" -Headers $headers -Body $body
    } catch {
        Write-Host "Rate Limited: $($_.Exception.Message)"
    }
    Start-Sleep -Milliseconds 100
}
```

### Step 6: 캐시 통계 확인

캐시 효과를 확인하는 관리용 도구를 추가합니다:

```python
@mcp.tool()
async def cache_stats() -> str:
    """캐시 통계 조회 (관리자용)"""
    return json.dumps({
        "policy_cache": policy_cache.stats(),
        "inventory_cache": inventory_cache.stats(),
    }, indent=2, ensure_ascii=False)
```

### Step 7: Redis 기반 Rate Limiter (다중 서버용)

단일 서버가 아닌 여러 서버에서 Rate Limit을 공유해야 할 때는 Redis를 사용합니다:

```python
# src/redis_rate_limiter.py (참고용)
import redis.asyncio as redis


class RedisRateLimiter:
    """Redis 기반 분산 Rate Limiter"""

    def __init__(self, redis_url: str, max_calls: int = 10, window_seconds: int = 60):
        self.redis = redis.from_url(redis_url)
        self.max_calls = max_calls
        self.window = window_seconds

    async def check(self, key: str) -> bool:
        """Redis INCR + EXPIRE로 Rate Limit 확인"""
        redis_key = f"ratelimit:{key}"

        # 현재 카운트 증가
        count = await self.redis.incr(redis_key)

        # 첫 번째 요청이면 TTL 설정
        if count == 1:
            await self.redis.expire(redis_key, self.window)

        return count <= self.max_calls

    async def remaining(self, key: str) -> int:
        redis_key = f"ratelimit:{key}"
        count = await self.redis.get(redis_key)
        current = int(count) if count else 0
        return max(0, self.max_calls - current)
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- LLM의 자동 도구 호출은 **무한 루프와 과부하 위험**이 있으므로 Rate Limiting은 필수입니다
- **Token Bucket / Sliding Window** 알고리즘으로 burst를 허용하면서도 평균 속도를 제한합니다
- Rate Limit은 **전역, 사용자별, 도구별** 세 수준으로 적용합니다
- **TTL Cache**로 반복 조회의 성능을 최적화하되, 쓰기 작업은 캐시하지 않습니다
- 다중 서버 환경에서는 **Redis 기반 분산 Rate Limiter**를 사용합니다
- **데코레이터 패턴**으로 Rate Limiting과 Caching 로직을 깔끔하게 분리할 수 있습니다

### 퀴즈

1. create_ticket 도구에 캐싱을 적용하지 않는 이유는?
   → 부수 효과(side effect)가 있는 쓰기 작업이므로 매번 실제로 실행되어야 함

2. Redis 기반 Rate Limiter가 In-memory보다 유리한 경우는?
   → 여러 서버 인스턴스가 동일한 Rate Limit 상태를 공유해야 할 때 (수평 스케일링 환경)

3. Cache invalidation 전략 중 TTL 기반의 장단점은?
   → 장점: 구현이 단순하고 자동으로 만료됨. 단점: TTL 동안 오래된 데이터를 반환할 수 있음

### 다음 편 예고

하나의 MCP 서버로 모든 것을 처리할 필요는 없습니다. EP25에서 **여러 MCP 서버를 조합하는 Multi-Server 오케스트레이션** 패턴을 다룹니다.
