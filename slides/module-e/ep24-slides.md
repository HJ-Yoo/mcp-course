---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 24 — Rate Limiting & Caching"
---

# EP 24 — Rate Limiting & Caching
## Module E (Advanced) · MCP 실전 마스터

---

## 학습 목표

1. MCP 서버에 Rate Limiting이 필요한 이유를 이해한다
2. Token Bucket 알고리즘을 설명하고 구현할 수 있다
3. TTL 기반 캐시를 구현하여 성능을 최적화할 수 있다

---

## 왜 Rate Limiting이 필요한가?

```
일반 API:  사람이 호출 → 자연스러운 속도 제한
MCP 서버:  LLM이 호출 → 초당 수십~수백 회 가능!

시나리오: 무한 루프
  LLM: "재고 확인" → lookup_inventory
  LLM: "다시 확인" → lookup_inventory
  LLM: "한 번 더..." → lookup_inventory
  ... (수백 회 반복, 서버 과부하)
```

> 비용 통제 + 서버 보호 + 공정성 + 안정성

---

## Token Bucket 알고리즘

```
  ┌─────────────────────┐
  │  Bucket (용량: 10)   │  ← 최대 10개 토큰
  │  O O O O O O O O    │  ← 현재 8개
  └──────────┬──────────┘
             │ 요청당 1개 소비
             v
       [API 요청 처리]

  보충: 매 초 1개 추가 (rate)
  최대: 10개 (burst)
  0개 시: 429 Too Many Requests
```

장점: **순간 burst 허용** + 평균 속도 제한

---

## Rate Limit 적용 수준

```
Level 1: 전체 서버 (Global)
  └── 전체 요청: 1000/분

  Level 2: 사용자별 (Per-User)
    └── user-001: 100/분

    Level 3: 도구별 (Per-Tool)
      ├── lookup_inventory: 30/분
      ├── search_policy: 20/분
      └── create_ticket: 10/분
```

**세밀한 제어**: 쓰기 도구는 더 엄격하게!

---

## Rate Limiter 구현

```python
class RateLimiter:
    def __init__(self, max_calls=10, window_seconds=60):
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls = defaultdict(list)

    def check(self, key: str) -> bool:
        now = time.monotonic()
        # 윈도우 밖 기록 제거
        self._calls[key] = [
            t for t in self._calls[key]
            if now - t < self.window
        ]
        if len(self._calls[key]) >= self.max_calls:
            return False  # 제한 초과!
        self._calls[key].append(now)
        return True  # 허용
```

---

## 캐싱 전략

| 도구 | 캐시 TTL | 이유 |
|------|---------|------|
| `search_policy` | 5분 | 정책은 자주 안 바뀜 |
| `lookup_inventory` | 1분 | 재고는 비교적 자주 변동 |
| `create_ticket` | 없음 | 쓰기 작업 (side effect) |

> 읽기는 캐시, 쓰기는 절대 캐시 안 함!

---

## TTL Cache 구현

```python
class TTLCache:
    def __init__(self, ttl_seconds=300):
        self.ttl = ttl_seconds
        self._cache = {}

    def get(self, key):
        if key in self._cache:
            ts, value = self._cache[key]
            if time.monotonic() - ts < self.ttl:
                return value  # 캐시 히트!
            del self._cache[key]
        return None  # 캐시 미스

    def set(self, key, value):
        self._cache[key] = (time.monotonic(), value)
```

---

## 도구에 적용하기

```python
@mcp.tool()
async def search_policy(query: str) -> str:
    # 1) Rate Limit 검사
    check_rate_limit("search_policy", user_id)

    # 2) 캐시 확인
    cached = policy_cache.get(cache_key)
    if cached:
        return f"[캐시] {cached}"

    # 3) 실제 조회
    result = _do_search(query)

    # 4) 캐시 저장
    policy_cache.set(cache_key, result)
    return result
```

---

## 데코레이터 패턴

```python
@mcp.tool()
@rate_limited("search_policy")
@cached(policy_cache, "search_policy")
async def search_policy(query: str) -> str:
    return _do_search(query)
```

- 반복 로직을 **데코레이터로 분리**
- 비즈니스 로직은 깔끔하게 유지
- 새 도구 추가 시 데코레이터만 붙이면 됨

---

## Cache Invalidation

> "어려운 것 두 가지: 캐시 무효화와 이름 짓기"

| 전략 | 설명 | 적합한 경우 |
|------|------|-----------|
| **TTL 기반** | 시간 경과 시 자동 만료 | 대부분 |
| **이벤트 기반** | 데이터 변경 시 삭제 | 실시간 중요 |
| **버전 기반** | 키에 버전 포함 | 대규모 변경 |

```python
# 티켓 생성 시 관련 캐시 무효화
inventory_cache.invalidate_prefix("lookup_inventory")
```

---

## Redis 기반 (다중 서버)

```python
class RedisRateLimiter:
    async def check(self, key: str) -> bool:
        redis_key = f"ratelimit:{key}"
        count = await self.redis.incr(redis_key)
        if count == 1:
            await self.redis.expire(redis_key, self.window)
        return count <= self.max_calls
```

- In-memory: 단일 서버용
- **Redis: 다중 서버**에서 상태 공유
- EP23의 docker-compose Redis와 연동

---

## 데모: Rate Limit 테스트

```bash
# 빠른 연속 호출 (10회 초과 시 Rate Limit)
for i in $(seq 1 15); do
  curl -s -X POST http://localhost:8000/mcp \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"jsonrpc":"2.0","id":'$i',
         "method":"tools/call",
         "params":{"name":"create_ticket",
                   "arguments":{"title":"Test"}}}'
  sleep 0.1
done
# 11번째부터 Rate Limit 에러 발생!
```

---

## 핵심 정리

- LLM 자동 호출 → **무한 루프 위험** → Rate Limiting 필수
- **Token Bucket**: burst 허용 + 평균 속도 제한
- **3단계 제한**: 전역 → 사용자별 → 도구별
- **TTL Cache**: 읽기 성능 최적화, 쓰기는 캐시 안 함
- **데코레이터 패턴**으로 깔끔한 적용
- 다중 서버 환경 → **Redis 기반** 분산 Rate Limiter

---

## 다음 편 예고

**EP 25 — Multi-Server 오케스트레이션**

하나의 서버로 모든 것을 처리할 필요 없다!
여러 MCP 서버를 조합하는 3가지 패턴
