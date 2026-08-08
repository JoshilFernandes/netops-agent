"""
Retrieval layer (RAG) over the runbook knowledge base, backed by ChromaDB.

Embedding backend: a scikit-learn TF-IDF vectorizer wrapped to satisfy
Chroma's EmbeddingFunction interface. This is a deliberate engineering
choice for this portfolio project: it avoids any runtime download of large
embedding models (keeps the project fully offline-runnable and CI-friendly),
while still exercising the real thing being demonstrated — a vector
database with persisted embeddings and similarity search.

Swapping in a hosted embedding model (e.g. `sentence-transformers/all-MiniLM-L6-v2`
via `langchain_huggingface`, or `voyage-3` / Anthropic embeddings) is a
one-line change in `get_embedding_function()` below and does not touch any
other module — this is the adapter pattern used deliberately so retrieval
quality can be upgraded without refactoring the agent.
"""
from __future__ import annotations

import os
import pickle
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_IMPL", "none")

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb import Documents, EmbeddingFunction, Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer

from agent.config import settings

VECTORIZER_PATH = Path(settings.KB_STORE_DIR) / "tfidf_vectorizer.pkl"


class TfidfEmbeddingFunction(EmbeddingFunction):
    """Fits once at ingestion time, then reused (loaded from disk) for queries."""

    def __init__(self, vectorizer: TfidfVectorizer | None = None):
        self.vectorizer = vectorizer

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        if self.vectorizer is None:
            raise RuntimeError(
                "Vectorizer not loaded. Run `python scripts/build_kb.py` first."
            )
        matrix = self.vectorizer.transform(input)
        return matrix.toarray().tolist()


def get_embedding_function() -> TfidfEmbeddingFunction:
    if VECTORIZER_PATH.exists():
        with VECTORIZER_PATH.open("rb") as f:
            vectorizer = pickle.load(f)
        return TfidfEmbeddingFunction(vectorizer)
    return TfidfEmbeddingFunction(None)


def build_index(docs_dir: str | None = None) -> int:
    """Ingest all runbooks into Chroma. Returns number of chunks indexed."""
    docs_dir = Path(docs_dir or settings.KB_DIR)
    store_dir = Path(settings.KB_STORE_DIR)
    store_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted(docs_dir.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"No runbooks found in {docs_dir}")

    texts, ids, metadatas = [], [], []
    for path in paths:
        content = path.read_text()
        # simple chunking: split on '## ' headers so each chunk is one
        # diagnostic/resolution/comms section — keeps retrieved context
        # focused rather than dumping the whole runbook.
        sections = content.split("\n## ")
        title_section = sections[0]
        for i, section in enumerate(sections):
            chunk = section if i == 0 else "## " + section
            texts.append(chunk.strip())
            ids.append(f"{path.stem}::chunk{i}")
            metadatas.append({"source": path.name, "chunk": i})

    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    vectorizer.fit(texts)
    with VECTORIZER_PATH.open("wb") as f:
        pickle.dump(vectorizer, f)

    client = chromadb.PersistentClient(path=str(store_dir), settings=ChromaSettings(anonymized_telemetry=False))
    try:
        client.delete_collection(settings.KB_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        settings.KB_COLLECTION,
        embedding_function=TfidfEmbeddingFunction(vectorizer),
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(documents=texts, ids=ids, metadatas=metadatas)
    return len(texts)


def query_kb(query: str, k: int = 3) -> list[dict]:
    """Return top-k retrieved chunks with similarity scores for a query."""
    store_dir = Path(settings.KB_STORE_DIR)
    client = chromadb.PersistentClient(path=str(store_dir), settings=ChromaSettings(anonymized_telemetry=False))
    collection = client.get_collection(
        settings.KB_COLLECTION, embedding_function=get_embedding_function()
    )
    results = collection.query(query_texts=[query], n_results=k)

    out = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        out.append(
            {
                "source": meta.get("source", "unknown"),
                "content": doc,
                "score": round(max(0.0, 1 - dist), 4),  # cosine distance -> similarity in [0,1]
            }
        )
    return out
