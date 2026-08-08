# Why this project — mapped to the Reply Agentic Software Engineer JD

A short note for whoever reviews this, mapping each requirement in the job posting
directly to where it's demonstrated in the code.

## Aufgaben (responsibilities)

| JD requirement | Where it's demonstrated |
|---|---|
| Implementierung von Komponenten agentenbasierter Systeme (Tools, Prompts, Retrieval-Pipelines, API-Integrationen) | `agent/tools.py` (5 typed tools), `agent/graph.py` (prompts + LangGraph nodes), `agent/kb.py` (RAG/retrieval pipeline), `services/*.py` (2 REST API integrations) |
| Entwicklung von Tests, Evaluierungen und Observability-Komponenten für LLM-basierte Funktionen | `tests/` (12 pytest cases), `evals/run_evals.py` (custom eval harness, 3 independent metrics × 6 scenarios), `agent/tracer.py` + `dashboard/observability_dashboard.py` |
| Unterstützung bei Proof-of-Concepts und Prototypen | The whole project is structured as a POC would be for a client demo: mocked backends standing in for real client systems, a Gradio demo for non-technical stakeholders, Docker for a one-command deploy |
| Zusammenarbeit an modernen AI- und Cloud-Lösungen | FastAPI + Docker/docker-compose, CI via GitHub Actions, cloud-deployable (HF Spaces demo, or any container platform) |

## Qualifikationen (qualifications)

| JD requirement | Where it's demonstrated |
|---|---|
| Python / TypeScript, Git, REST-APIs, Cloud | Entire project in Python; 3 FastAPI services; Git-ready repo; deployable to any cloud container platform |
| LLM-APIs, Prompt Engineering, RAG | `agent/llm.py` (multi-provider Claude/Groq client with prompt templates in `agent/graph.py`), `agent/kb.py` (ChromaDB RAG pipeline) |
| Agent Frameworks (LangChain, LangGraph) | `agent/graph.py` — explicit LangGraph state machine with conditional routing |
| Vector Databases | ChromaDB, persisted collection, cosine similarity, swappable embedding backend |
| Analytische, strukturierte Arbeitsweise | Eval harness separates triage/retrieval/routing correctness rather than one pass/fail number; tracer emits structured, queryable spans rather than log strings |

## A deliberate engineering decision worth calling out

The LLM defaults to a **mock mode** (rule-based, deterministic) rather than requiring
an API key. This was a conscious choice, not a limitation:

- The whole project — including the agent graph, RAG retrieval, tool calls, tests,
  and evals — is fully reviewable and runnable by anyone with zero setup cost or
  credentials.
- CI runs the real eval suite on every push without needing a secret API key in
  GitHub Actions.
- The LLM provider is a one-line config change (`LLM_PROVIDER=anthropic`) — swapping
  in live Claude reasoning doesn't touch the graph, tools, or tests at all.

That's the same kind of pragmatic tradeoff I'd want to make on a real client
engagement: keep the system demoable and testable without depending on production
credentials, while making the "real" path a trivial config change.

## Use case choice

Reply's roots are in telecom/network consulting (long-standing engagements with
operators like Vodafone and TIM), which is why this project models a NOC incident
triage agent rather than a generic customer-support chatbot — it's closer to the kind
of Delivery Squad work described in the JD, and it's a domain where "agentic" actually
matters: the system has to *decide* whether to escalate, not just answer a question.

— Joshil Fernandes
