"""
Lightweight observability layer for the agent graph.

This is intentionally framework-agnostic (no vendor lock-in): it writes
structured JSONL trace events with per-node latency, token estimates, and
tool-call I/O. In a production Reply engagement this would typically be
swapped for / fed into LangSmith, OpenTelemetry + an APM backend, or a
client's existing observability stack — the important part is that every
node emits *structured, queryable* events rather than only log strings.

The dashboard/ Streamlit app reads this same JSONL file to visualize
latency-per-node and tool-call volume.
"""
from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from agent.config import settings


class Tracer:
    def __init__(self, log_path: str | None = None):
        self.log_path = Path(log_path or settings.TRACE_LOG_PATH)

    def _write(self, event: dict) -> None:
        event["ts"] = time.time()
        with self.log_path.open("a") as f:
            f.write(json.dumps(event) + "\n")

    def new_trace_id(self) -> str:
        return str(uuid.uuid4())[:8]

    @contextmanager
    def span(self, trace_id: str, node: str, **extra):
        start = time.perf_counter()
        error = None
        try:
            yield
        except Exception as e:  # noqa: BLE001
            error = str(e)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            self._write(
                {
                    "trace_id": trace_id,
                    "node": node,
                    "duration_ms": duration_ms,
                    "error": error,
                    **extra,
                }
            )

    def log_tool_call(self, trace_id: str, tool: str, tool_input: dict, tool_output: dict) -> None:
        self._write(
            {
                "trace_id": trace_id,
                "event": "tool_call",
                "tool": tool,
                "input": tool_input,
                "output": tool_output,
            }
        )


tracer = Tracer()
