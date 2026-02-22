---
marp: true
theme: default
paginate: true
header: "MCP 실전 마스터"
footer: "EP 27 — 프로덕션 체크리스트 & 마무리"
---

# EP 27 — 프로덕션 체크리스트 & 마무리
## Module E (Advanced) · MCP 실전 마스터

---

## 학습 목표

1. 프로덕션 배포를 위한 체크리스트를 검토하고 적용할 수 있다
2. 배포 아키텍처 옵션을 비교하고 선택할 수 있다
3. 전체 과정을 회고하고 다음 단계를 계획할 수 있다

---

## 프로덕션 체크리스트: 7개 영역

```
1. 보안           ████████████  EP10, EP22
2. 안정성         ████████████  EP12, EP24
3. 관측성         ████████████  EP14, EP26
4. 배포           ████████████  EP23
5. 테스트         ████████████  EP15-17
6. 문서화         ████████████  EP09
7. 규정 준수      ████████████  EP14

모든 항목 통과 → 프로덕션 배포 가능!
```

---

## 1) 보안 (Security)

| # | 항목 | EP | 상태 |
|---|------|-----|------|
| 1-1 | 입력 검증 (Pydantic) | EP12 | [v] |
| 1-2 | Path traversal 방지 | EP10 | [v] |
| 1-3 | 인증 (Bearer / OAuth 2.1) | EP22 | [v] |
| 1-4 | Scope 기반 권한 검사 | EP22 | [v] |
| 1-5 | 환경변수로 비밀값 관리 | EP23 | [v] |

---

## 2) 안정성 + 3) 관측성

**안정성 (Reliability)**

| # | 항목 | EP |
|---|------|-----|
| 2-1 | 에러 처리 (try/except) | EP12 |
| 2-2 | Rate Limiting | EP24 |
| 2-3 | 타임아웃 설정 | EP12 |

**관측성 (Observability)**

| # | 항목 | EP |
|---|------|-----|
| 3-1 | 구조화 로깅 (JSONL) | EP14 |
| 3-2 | Prometheus 메트릭 | EP26 |
| 3-3 | 분산 트레이싱 (OTel) | EP26 |

---

## 4) 배포 + 5) 테스트

**배포 (Deployment)**

| # | 항목 | EP |
|---|------|-----|
| 4-1 | Docker 컨테이너화 | EP23 |
| 4-2 | 환경변수 분리 (.env) | EP23 |
| 4-3 | 헬스체크 엔드포인트 | EP23 |

**테스트 (Testing)**

| # | 항목 | EP |
|---|------|-----|
| 5-1 | 단위 테스트 (pytest) | EP15 |
| 5-2 | 통합 테스트 | EP16 |
| 5-3 | 보안 테스트 | EP17 |

---

## 배포 아키텍처 옵션

```
옵션 1: 단일 서버 (Docker + systemd)
  VM/EC2 → Docker → MCP Server
  적합: 소규모, 단일 팀

옵션 2: 쿠버네티스
  K8s Cluster → 3 Pods → Service → Ingress
  적합: 대규모, 고가용성

옵션 3: 서버리스 (Lambda)
  API Gateway → Lambda → MCP Handler
  적합: 간헐적 사용 (주의: 콜드 스타트)
```

---

## Kubernetes 배포

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ops-assistant
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: mcp-server
        image: ops-assistant:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
        resources:
          limits:
            memory: "256Mi"
            cpu: "500m"
```

---

## 스케일링 전략

| 항목 | 문제 | 해결 |
|------|------|------|
| **캐시** | 인스턴스별 불일치 | Redis 공유 (EP24) |
| **Rate Limit** | 카운트 분리 | Redis 분산 (EP24) |
| **세션** | 스티키 필요? | Stateless 설계 |
| **로그** | 수집 분산 | 중앙 로깅 (ELK) |
| **메트릭** | 통합 필요 | Prometheus federation |

> 핵심: **Stateless 설계** + **Redis 공유 상태**

---

## 자동 검증 스크립트

```python
# scripts/production_check.py
def main():
    print("MCP Server Production Checklist")

    check("입력 검증 모듈", path_exists("src/validation.py"))
    check("인증 모듈", path_exists("src/auth.py"))
    check("Rate Limiter", path_exists("src/rate_limiter.py"))
    check("메트릭 모듈", path_exists("src/metrics.py"))
    check("Dockerfile", path_exists("Dockerfile"))
    check("테스트 통과", run_tests() == 0)

    print(f"결과: {passed}/{total}")
```

```bash
uv run python scripts/production_check.py
```

---

## 전체 과정 회고

```
Module A (EP01-05): MCP 기초
  → 프로토콜, 프리미티브, 아키텍처 이해

Module B (EP06-13): 서버 구현
  → Tools, Resources, Prompts, Validation

Module C (EP14-17): 품질 보증
  → AuditLogger, 단위/통합/보안 테스트

Module D (EP18-21): 연동 & 배포
  → 클라이언트 연동, stdio, Streamable HTTP

Module E (EP22-27): 프로덕션 운영
  → 인증, Docker, Rate Limit, Multi-Server,
    Observability, 프로덕션 체크리스트
```

---

## 우리가 만든 것

**Acme Corp Internal Ops Assistant**

- 3 Tools: `lookup_inventory`, `search_policy`, `create_ticket`
- 2 Resources: `policy://index`, `policy://{doc_id}`
- 2 Prompts: `incident_report`, `policy_answer`
- AuditLogger (JSONL) + Validation + Lifespan
- 인증 (OAuth 2.1) + Rate Limiting + Caching
- Docker + docker-compose + Prometheus + Grafana
- 단위/통합/보안 테스트 (pytest)

---

## 다음 단계 제안

1. **DB 연동**: JSON 파일 → PostgreSQL/SQLite
2. **실시간 알림**: WebSocket으로 티켓 알림
3. **오픈소스 기여**: 자신만의 MCP 서버 공유
4. **AI Agent 파이프라인**: 도구 조합 자동화
5. **프롬프트 엔지니어링**: MCP Prompts 고급 활용

---

## 운영 트러블슈팅 가이드

| 증상 | 원인 | 해결 |
|------|------|------|
| 401 Unauthorized | 토큰 만료 | 새 토큰 발급 |
| 429 Too Many Requests | Rate Limit | 한도 조정 |
| P95 > 500ms | 캐시 미스 | TTL 조정/DB 최적화 |
| 컨테이너 재시작 | OOM Killed | 메모리 리밋 상향 |

---

## 수료 축하!

**"MCP 실전 마스터" 전체 과정을 완주하셨습니다!**

EP01에서 "MCP란 무엇인가?"를 물으며 시작한 여정이
EP27에서 프로덕션 배포까지 도달했습니다.

여러분은 이제 MCP 프로토콜을 이해하고,
서버를 구현하고, 테스트하고,
프로덕션에 배포할 수 있는 역량을 갖추셨습니다.

> Internal Ops Assistant는 시작일 뿐입니다.
> 여러분만의 MCP 서버를 만들어 보세요!

**수고하셨습니다!**
