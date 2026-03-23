"""
Audit logger — TODO (Episode 14): Implement JSONL audit logging.

asyncio.Lock()을 사용한 thread-safe 구현.
"""
from __future__ import annotations

from pathlib import Path


class AuditLogger:
    def __init__(self, log_dir: str | Path = "logs"):
        # TODO: self._log_dir = Path(log_dir)
        # TODO: 디렉토리 생성 (mkdir)
        # TODO: self._lock = asyncio.Lock()
        pass

    @property
    def log_path(self) -> Path:
        # TODO: self._log_dir / "audit.jsonl" 반환
        pass

    def start_timer(self) -> float:
        # TODO: time.perf_counter() 반환
        pass

    def elapsed_ms(self, start: float) -> float:
        # TODO: (현재 시간 - start) * 1000 계산
        pass

    async def log(self, action: str, tool_name: str, **kwargs) -> None:
        # TODO: timestamp, action, tool_name + kwargs로 entry 생성
        # TODO: async with self._lock으로 동시 쓰기 방지
        # TODO: JSONL 형식으로 append
        pass
