"""
Evaluation harness for the NetOps agent.

This is the kind of lightweight, homegrown eval suite the JD calls out
explicitly ("Entwicklung von Tests, Evaluierungen ... für LLM-basierte
Funktionen"). It checks three things independently, the way you'd want to
in a real agent pipeline:

  1. Triage accuracy      -> did the classifier pick the right category/severity?
  2. Retrieval relevance  -> did RAG surface the runbook that actually matches?
  3. Routing / tool-use   -> did the agent take the correct action (ticket vs. no ticket)
                             given the severity, i.e. is the *agentic* decision correct,
                             not just the text output?

Run with: python evals/run_evals.py
Exits non-zero if overall pass rate drops below the configured threshold,
so this can be wired into CI as a quality gate.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.graph import run_incident

PASS_THRESHOLD = 0.8


def load_cases() -> list[dict]:
    path = Path(__file__).parent / "eval_cases.json"
    return json.loads(path.read_text())


def evaluate_case(case: dict) -> dict:
    incident = {
        "incident_id": case["id"],
        "node_id": case["node_id"],
        "region": "eval",
        "raw_alert_text": case["raw_alert_text"],
    }
    start = time.perf_counter()
    result = run_incident(incident)
    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    category_correct = result["triage"]["category"] == case["expected_category"]
    severity_correct = result["triage"]["severity"] == case["expected_severity"]

    retrieved_sources = {d["source"] for d in result.get("retrieved_docs", [])}
    retrieval_correct = case["expected_source_doc"] in retrieved_sources

    ticket_created = result.get("ticket_id") is not None
    routing_correct = ticket_created == case["expect_ticket"]

    checks = {
        "category_correct": category_correct,
        "severity_correct": severity_correct,
        "retrieval_correct": retrieval_correct,
        "routing_correct": routing_correct,
    }
    passed = all(checks.values())

    return {
        "case_id": case["id"],
        "passed": passed,
        "checks": checks,
        "latency_ms": latency_ms,
        "actual_category": result["triage"]["category"],
        "actual_severity": result["triage"]["severity"],
        "retrieved_sources": sorted(retrieved_sources),
        "ticket_created": ticket_created,
    }


def main() -> int:
    cases = load_cases()
    results = [evaluate_case(c) for c in cases]

    pass_count = sum(1 for r in results if r["passed"])
    pass_rate = pass_count / len(results)

    print(f"{'CASE':<24} {'PASS':<6} {'CATEGORY':<10} {'SEVERITY':<8} {'RETRIEVAL':<10} {'ROUTING':<8} {'LATENCY_MS'}")
    for r in results:
        print(
            f"{r['case_id']:<24} "
            f"{'✅' if r['passed'] else '❌':<6} "
            f"{'✅' if r['checks']['category_correct'] else '❌':<10} "
            f"{'✅' if r['checks']['severity_correct'] else '❌':<8} "
            f"{'✅' if r['checks']['retrieval_correct'] else '❌':<10} "
            f"{'✅' if r['checks']['routing_correct'] else '❌':<8} "
            f"{r['latency_ms']}"
        )

    print(f"\nOverall pass rate: {pass_count}/{len(results)} ({pass_rate:.0%})")

    report_path = Path(__file__).parent / "last_eval_report.json"
    report_path.write_text(json.dumps({"pass_rate": pass_rate, "results": results}, indent=2))
    print(f"Full report written to {report_path}")

    if pass_rate < PASS_THRESHOLD:
        print(f"FAIL: pass rate below threshold ({PASS_THRESHOLD:.0%})")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
