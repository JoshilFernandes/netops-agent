"""
Thin, provider-agnostic LLM client.

Supports Anthropic Claude, Groq (OpenAI-compatible, used the same way as
in prior free-tier projects), and a deterministic "mock" mode. Mock mode
is the default: it lets the entire agent graph, its tests, and its evals
run with zero API keys and zero network calls — which matters both for a
reviewer running this without credentials, and for CI.

Swapping providers is a config change (LLM_PROVIDER env var), not a code
change anywhere else in the project.
"""
from __future__ import annotations

import json
import re

from agent.config import settings


class LLMClient:
    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.LLM_PROVIDER

    def complete(self, system: str, user: str) -> str:
        if self.provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            return self._anthropic(system, user)
        if self.provider == "groq" and settings.GROQ_API_KEY:
            return self._groq(system, user)
        return self._mock(system, user)

    # -- real providers -----------------------------------------------
    def _anthropic(self, system: str, user: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=800,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    def _groq(self, system: str, user: str) -> str:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content

    # -- deterministic mock, used for offline dev/tests/CI -------------
    def _mock(self, system: str, user: str) -> str:
        """
        Rule-based stand-in for an LLM call. Good enough to drive the
        agent graph deterministically for demos/tests without an API key.
        Real deployments set LLM_PROVIDER=anthropic|groq.
        """
        text = user.lower()

        if "classify" in system.lower():
            category, severity = _keyword_classify(text)
            return json.dumps({
                "category": category,
                "severity": severity,
                "rationale": f"Keyword match against alert text identified this as a '{category}' issue.",
            })

        if "synthesize" in system.lower() or "summary" in system.lower():
            return (
                "Root cause investigation points to the retrieved runbook procedure. "
                "Diagnostics and the matching runbook were used to determine severity "
                "and next steps; a ticket has been opened and the relevant team notified."
            )

        if "customer" in system.lower():
            return (
                "We have identified an issue affecting your service and are actively "
                "working on a resolution. We will keep you updated on progress."
            )

        return "OK"


def _keyword_classify(text: str) -> tuple[str, str]:
    rules = [
        (["fiber", "cut", "optical", "signal loss", "no signal"], "physical_layer", "critical"),
        (["bgp", "flap", "route flap", "routing instability"], "routing", "high"),
        (["dns", "resolve", "nxdomain", "servfail"], "application_layer", "medium"),
        (["congestion", "latency", "slow", "utilization", "peak hour"], "capacity", "medium"),
        (["hardware", "unreachable", "heartbeat", "core router", "power supply"], "hardware", "critical"),
        (["vpn", "tunnel", "ipsec", "ike"], "enterprise_services", "medium"),
    ]
    for keywords, category, severity in rules:
        if any(kw in text for kw in keywords):
            return category, severity
    return "unknown", "medium"


def extract_json(text: str) -> dict:
    """Best-effort JSON extraction from an LLM response (handles code fences)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {text!r}")
    return json.loads(match.group(0))
