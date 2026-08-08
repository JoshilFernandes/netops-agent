"""
Central configuration. Reads from environment / .env so the same code runs
locally, in CI, and on a hosted demo (e.g. Hugging Face Spaces) without
changes — only environment variables differ.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY") or None

    NETWORK_API_BASE: str = os.getenv("NETWORK_API_BASE", "http://localhost:8001")
    TICKETING_API_BASE: str = os.getenv("TICKETING_API_BASE", "http://localhost:8002")

    KB_DIR: str = os.getenv("KB_DIR", "data/runbooks")
    KB_STORE_DIR: str = os.getenv("KB_STORE_DIR", "kb_store")
    KB_COLLECTION: str = os.getenv("KB_COLLECTION", "netops_runbooks")

    TRACE_LOG_PATH: str = os.getenv("TRACE_LOG_PATH", "traces.jsonl")


settings = Settings()
