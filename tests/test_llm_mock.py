"""Unit tests for the deterministic mock LLM classification rules."""
from agent.llm import _keyword_classify


def test_classify_fiber_outage():
    category, severity = _keyword_classify("total loss of optical signal, fiber cut suspected")
    assert category == "physical_layer"
    assert severity == "critical"


def test_classify_bgp_flap():
    category, severity = _keyword_classify("bgp session flapping repeatedly with peer router")
    assert category == "routing"
    assert severity == "high"


def test_classify_unknown_defaults_gracefully():
    category, severity = _keyword_classify("something completely unrelated happened today")
    assert category == "unknown"
    assert severity == "medium"
