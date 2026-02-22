# EP 27 — 프로덕션 체크리스트 & 마무리

> Module E (Advanced) · 약 20분

## 학습 목표

1. MCP 서버 프로덕션 배포를 위한 체크리스트를 검토하고 적용할 수 있다
2. 배포 아키텍처 옵션(Docker, Kubernetes, 서버리스)을 비교하고 선택할 수 있다
3. Core부터 Advanced까지 전체 과정을 회고하고 다음 단계를 계획할 수 있다

---

## 1. 인트로 (2분)

드디어 마지막 에피소드입니다. EP01에서 "MCP란 무엇인가?"를 물으며 시작한 여정이 EP27에 도달했습니다.

그동안 우리는 Internal Ops Assistant를 처음부터 만들었습니다. Tools, Resources, Prompts를 구현하고, 감사 로깅과 입력 검증을 추가하고, 테스트를 작성하고, 인증과 컨테이너화와 모니터링까지 구축했습니다.

> "이제 정말 프로덕션에 배포해도 될까?"

이번 에피소드에서는 **프로덕션 체크리스트**를 하나씩 점검하고, 배포 아키텍처를 결정하고, 전체 과정을 회고합니다. 그리고 앞으로 나아갈 방향을 제시합니다.

---

## 2. 핵심 개념 (6분)

### 2.1 프로덕션 체크리스트

7개 영역, 총 21개 항목으로 프로덕션 준비 상태를 점검합니다:

```
┌──────────────────────────────────────────────────────────┐
│            프로덕션 체크리스트 (7 영역)                    │
│                                                          │
│  1. 보안           ████████████ EP10, EP22                │
│  2. 안정성         ████████████ EP12, EP24                │
│  3. 관측성         ████████████ EP14, EP26                │
│  4. 배포           ████████████ EP23                      │
│  5. 테스트         ████████████ EP15-17                   │
│  6. 문서화         ████████████ EP09                      │
│  7. 규정 준수      ████████████ EP14                      │
│                                                          │
│  모든 항목 통과 → 프로덕션 배포 가능!                     │
└──────────────────────────────────────────────────────────┘
```

#### 1) 보안 (Security)

| # | 항목 | 구현 에피소드 | 상태 |
|---|------|-------------|------|
| 1-1 | 입력 검증 (Pydantic, 길이 제한) | EP12 | 완료 |
| 1-2 | Path traversal 방지 | EP10 | 완료 |
| 1-3 | 인증 (Bearer Token / OAuth 2.1) | EP22 | 완료 |
| 1-4 | 권한 검사 (Scope 기반) | EP22 | 완료 |
| 1-5 | 환경변수로 비밀값 관리 | EP23 | 완료 |

#### 2) 안정성 (Reliability)

| # | 항목 | 구현 에피소드 | 상태 |
|---|------|-------------|------|
| 2-1 | 에러 처리 (try/except, 사용자 메시지) | EP12 | 완료 |
| 2-2 | Rate Limiting (도구별, 사용자별) | EP24 | 완료 |
| 2-3 | 타임아웃 설정 | EP12 | 완료 |

#### 3) 관측성 (Observability)

| # | 항목 | 구현 에피소드 | 상태 |
|---|------|-------------|------|
| 3-1 | 구조화 로깅 (JSONL AuditLogger) | EP14 | 완료 |
| 3-2 | Prometheus 메트릭 | EP26 | 완료 |
| 3-3 | 분산 트레이싱 (OpenTelemetry) | EP26 | 완료 |

#### 4) 배포 (Deployment)

| # | 항목 | 구현 에피소드 | 상태 |
|---|------|-------------|------|
| 4-1 | Docker 컨테이너화 | EP23 | 완료 |
| 4-2 | 환경변수 분리 (.env) | EP23 | 완료 |
| 4-3 | 헬스체크 엔드포인트 | EP23 | 완료 |

#### 5) 테스트 (Testing)

| # | 항목 | 구현 에피소드 | 상태 |
|---|------|-------------|------|
| 5-1 | 단위 테스트 (pytest) | EP15 | 완료 |
| 5-2 | 통합 테스트 | EP16 | 완료 |
| 5-3 | 보안 테스트 (path traversal 등) | EP17 | 완료 |

#### 6) 문서화 (Documentation)

| # | 항목 | 구현 에피소드 | 상태 |
|---|------|-------------|------|
| 6-1 | API 문서 (도구, 리소스, 프롬프트) | EP09 | 완료 |
| 6-2 | 운영 가이드 (배포, 설정, 트러블슈팅) | 이번 편 | 작성 |

#### 7) 규정 준수 (Compliance)

| # | 항목 | 구현 에피소드 | 상태 |
|---|------|-------------|------|
| 7-1 | 감사 로깅 (누가, 언제, 무엇을) | EP14 | 완료 |
| 7-2 | 데이터 보호 (민감 정보 마스킹) | EP14 | 완료 |

### 2.2 배포 아키텍처 옵션

프로덕션 환경에 따라 세 가지 배포 방식을 선택할 수 있습니다:

```
옵션 1: 단일 서버 (Docker + systemd)
┌──────────────────────────┐
│        VM / EC2          │
│  ┌────────────────────┐  │
│  │   Docker Engine    │  │
│  │  ┌──────────────┐  │  │
│  │  │ MCP Server   │  │  │
│  │  │ (container)  │  │  │
│  │  └──────────────┘  │  │
│  └────────────────────┘  │
│  systemd로 Docker 관리    │
└──────────────────────────┘
적합: 소규모, 단일 팀, 트래픽 적음


옵션 2: 쿠버네티스 (Deployment + Service)
┌──────────────────────────────────────┐
│          Kubernetes Cluster          │
│                                      │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ Pod (1) │ │ Pod (2) │ │Pod (3) │ │
│  │ MCP Srv │ │ MCP Srv │ │MCP Srv │ │
│  └────┬────┘ └────┬────┘ └───┬────┘ │
│       └───────────┼──────────┘      │
│              Service (LB)           │
│                  │                  │
│              Ingress                │
└──────────────────┼──────────────────┘
                   │
              클라이언트
적합: 대규모, 수평 확장, 고가용성 필요


옵션 3: 서버리스 (AWS Lambda)
┌────────────────────────────────────┐
│          API Gateway               │
│              │                     │
│      ┌───────────────┐             │
│      │  Lambda       │             │
│      │  (MCP 핸들러) │             │
│      └───────────────┘             │
│                                    │
│  주의: 콜드 스타트, WebSocket 미지원│
│  stdio 전송 불가, HTTP만 가능      │
└────────────────────────────────────┘
적합: 간헐적 사용, 비용 최소화
제약: 상태 유지 어려움, 콜드 스타트
```

### 2.3 스케일링 전략

수평 확장 시 고려사항:

| 항목 | 문제 | 해결 |
|------|------|------|
| **상태 관리** | 인스턴스별 캐시 불일치 | Redis 공유 캐시 (EP24) |
| **Rate Limiting** | 인스턴스별 카운트 분리 | Redis 분산 Rate Limiter (EP24) |
| **세션** | 세션 스티키 필요 여부 | Stateless 설계 권장 |
| **로그** | 여러 인스턴스의 로그 수집 | 중앙 집중 로깅 (ELK/Loki) |
| **메트릭** | 인스턴스별 메트릭 통합 | Prometheus federation |

### 2.4 전체 과정 회고

```
Module A (EP01-05): MCP 기초
  "MCP란 무엇인가?" → 프로토콜, 프리미티브, 아키텍처 이해

Module B (EP06-13): 서버 구현
  "실제로 만들어보자" → Tools, Resources, Prompts, Validation, Lifespan

Module C (EP14-17): 품질 보증
  "안전하고 테스트된 코드" → AuditLogger, 단위/통합/보안 테스트

Module D (EP18-21): 연동 & 배포
  "세상과 연결하자" → 클라이언트 연동, stdio, Streamable HTTP

Module E (EP22-27): 프로덕션 운영
  "실전 배포와 운영" → 인증, Docker, Rate Limiting, Multi-Server,
                       Observability, 프로덕션 체크리스트
```

### 2.5 다음 단계 제안

과정을 마친 후 도전해볼 수 있는 프로젝트:

1. **데이터베이스 연동**: 현재 JSON 파일 기반 → PostgreSQL/SQLite 전환
2. **WebSocket 실시간 알림**: 티켓 생성 시 실시간 알림
3. **MCP 생태계 기여**: 자신만의 MCP 서버를 오픈소스로 공유
4. **AI Agent 파이프라인**: 여러 MCP 도구를 조합한 자동화 워크플로우
5. **프롬프트 엔지니어링**: MCP Prompts를 활용한 고급 대화 설계

---

## 3. 라이브 데모 (10분)

### Step 1: 체크리스트 자동 검증 스크립트

프로덕션 배포 전 자동으로 체크리스트를 검증하는 스크립트:

```python
# scripts/production_check.py
"""프로덕션 배포 전 자동 체크리스트 검증"""

import subprocess
import sys
import json
from pathlib import Path


def check(name: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    symbol = "[v]" if condition else "[x]"
    print(f"  {symbol} {name}" + (f" — {detail}" if detail else ""))
    return condition


def main():
    project_root = Path(__file__).parent.parent
    results = []
    print("=" * 60)
    print("  MCP Server Production Checklist")
    print("=" * 60)

    # --- 1. 보안 ---
    print("\n[1] 보안 (Security)")
    results.append(check(
        "입력 검증 모듈 존재",
        (project_root / "src" / "validation.py").exists(),
    ))
    results.append(check(
        "인증 모듈 존재",
        (project_root / "src" / "auth.py").exists(),
    ))
    results.append(check(
        ".env 파일이 .gitignore에 포함",
        ".env" in (project_root / ".gitignore").read_text()
        if (project_root / ".gitignore").exists() else False,
    ))

    # --- 2. 안정성 ---
    print("\n[2] 안정성 (Reliability)")
    results.append(check(
        "Rate Limiter 모듈 존재",
        (project_root / "src" / "rate_limiter.py").exists(),
    ))
    results.append(check(
        "캐시 모듈 존재",
        (project_root / "src" / "cache.py").exists(),
    ))

    # --- 3. 관측성 ---
    print("\n[3] 관측성 (Observability)")
    results.append(check(
        "메트릭 모듈 존재",
        (project_root / "src" / "metrics.py").exists(),
    ))
    results.append(check(
        "감사 로거 존재",
        (project_root / "src" / "audit.py").exists() or
        (project_root / "src" / "audit_logger.py").exists(),
    ))

    # --- 4. 배포 ---
    print("\n[4] 배포 (Deployment)")
    results.append(check(
        "Dockerfile 존재",
        (project_root / "Dockerfile").exists(),
    ))
    results.append(check(
        "docker-compose.yml 존재",
        (project_root / "docker-compose.yml").exists(),
    ))
    results.append(check(
        ".env.example 존재",
        (project_root / ".env.example").exists(),
    ))

    # --- 5. 테스트 ---
    print("\n[5] 테스트 (Testing)")
    test_dir = project_root / "tests"
    test_files = list(test_dir.glob("test_*.py")) if test_dir.exists() else []
    results.append(check(
        f"테스트 파일 존재 ({len(test_files)}개)",
        len(test_files) > 0,
    ))

    # 테스트 실행
    if test_files:
        test_result = subprocess.run(
            ["uv", "run", "pytest", "--tb=no", "-q"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        results.append(check(
            "모든 테스트 통과",
            test_result.returncode == 0,
            test_result.stdout.strip().split("\n")[-1] if test_result.stdout else "",
        ))

    # --- 6. 문서화 ---
    print("\n[6] 문서화 (Documentation)")
    results.append(check(
        "README.md 존재",
        (project_root / "README.md").exists(),
    ))

    # --- 결과 요약 ---
    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 60)
    print(f"  결과: {passed}/{total} 통과")
    if passed == total:
        print("  --> 프로덕션 배포 준비 완료!")
    else:
        print(f"  --> {total - passed}개 항목 수정 필요")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
```

macOS/Linux:
```bash
uv run python scripts/production_check.py
```

Windows (PowerShell):
```powershell
uv run python scripts/production_check.py
```

### Step 2: 쿠버네티스 배포 매니페스트

프로덕션 쿠버네티스 배포를 위한 기본 매니페스트:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ops-assistant
  labels:
    app: ops-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ops-assistant
  template:
    metadata:
      labels:
        app: ops-assistant
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      containers:
      - name: mcp-server
        image: ops-assistant:latest
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: MCP_SERVER_PORT
          value: "8000"
        - name: MCP_LOG_LEVEL
          value: "INFO"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: jwt-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "128Mi"
            cpu: "250m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: ops-data-pvc
      - name: logs
        emptyDir: {}

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ops-assistant
spec:
  selector:
    app: ops-assistant
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ops-assistant
  annotations:
    nginx.ingress.kubernetes.io/rate-limit-connections: "10"
    nginx.ingress.kubernetes.io/rate-limit-rps: "50"
spec:
  rules:
  - host: mcp.acme-corp.internal
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ops-assistant
            port:
              number: 80
  tls:
  - hosts:
    - mcp.acme-corp.internal
    secretName: mcp-tls-secret
```

macOS/Linux:
```bash
# 쿠버네티스 배포 (클러스터 접근 가능 시)
kubectl apply -f k8s/
kubectl get pods -l app=ops-assistant
kubectl logs -l app=ops-assistant --tail=20
```

Windows (PowerShell):
```powershell
# 쿠버네티스 배포 (클러스터 접근 가능 시)
kubectl apply -f k8s/
kubectl get pods -l app=ops-assistant
kubectl logs -l app=ops-assistant --tail=20
```

### Step 3: 운영 가이드 (핵심 요약)

```
=== Ops Assistant 운영 가이드 ===

[서버 시작]
  로컬:   uv run python src/server.py --transport streamable-http --port 8000
  Docker: docker compose up -d
  K8s:    kubectl apply -f k8s/

[헬스체크]
  curl http://localhost:8000/health

[메트릭 확인]
  curl http://localhost:9090/metrics | grep mcp_

[로그 확인]
  Docker: docker compose logs mcp-server
  K8s:    kubectl logs -l app=ops-assistant

[트러블슈팅]
  Q: 401 Unauthorized?
  A: 토큰 만료 확인 → 새 토큰 발급

  Q: 429 Too Many Requests?
  A: Rate Limit 설정 확인 → 필요 시 한도 조정

  Q: 응답 느림 (P95 > 500ms)?
  A: 캐시 히트율 확인 → 캐시 TTL 조정 또는 DB 최적화

  Q: 컨테이너 재시작 반복?
  A: OOM Killed 여부 확인 → 메모리 리밋 상향
```

---

## 4. 요약 & 퀴즈 (2분)

### 핵심 정리

- **프로덕션 체크리스트** 7개 영역(보안, 안정성, 관측성, 배포, 테스트, 문서화, 규정 준수)을 모두 통과해야 합니다
- **배포 아키텍처**: 단일 서버(Docker), 쿠버네티스, 서버리스 중 환경에 맞게 선택합니다
- **스케일링**: Redis 공유 상태, Stateless 설계, 중앙 집중 로깅이 핵심입니다
- **자동 검증 스크립트**로 배포 전 체크리스트를 프로그래밍 방식으로 확인합니다
- EP01~EP27까지 **프로토콜 이해 → 서버 구현 → 테스트 → 연동 → 프로덕션 운영**의 전체 사이클을 완주했습니다

### 퀴즈

1. 서버리스(Lambda) 배포의 가장 큰 제약은?
   → 콜드 스타트로 인한 초기 지연, WebSocket/stdio 전송 미지원, 상태 유지 어려움

2. 수평 확장 시 In-memory 캐시의 문제는?
   → 인스턴스별로 독립된 캐시가 존재하여 불일치 발생. Redis 같은 공유 캐시로 해결

3. 이 과정에서 구현한 프로덕션 기능을 에피소드 순서대로 나열하면?
   → 입력 검증(EP12) → 감사 로깅(EP14) → 테스트(EP15-17) → 인증(EP22) → Docker(EP23) → Rate Limiting(EP24) → 모니터링(EP26)

### 수료 축하

축하합니다! "MCP 실전 마스터" 전체 과정을 완주하셨습니다.

여러분은 이제 MCP 프로토콜을 이해하고, 서버를 구현하고, 테스트하고, 프로덕션에 배포할 수 있는 역량을 갖추셨습니다. Internal Ops Assistant는 시작일 뿐입니다. 이 지식을 바탕으로 여러분만의 MCP 서버를 만들어 보세요.

MCP 생태계는 빠르게 성장하고 있습니다. 공식 스펙, 커뮤니티 서버, 새로운 클라이언트 구현 등 계속 발전하는 생태계에 참여해 주세요. 여러분이 만든 MCP 서버가 다른 개발자들에게도 도움이 될 수 있습니다.

다시 한 번 축하드립니다. 수고하셨습니다!
