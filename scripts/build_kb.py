"""CLI entrypoint: (re)build the vector index from the runbook markdown files."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.kb import build_index

if __name__ == "__main__":
    n = build_index()
    print(f"Indexed {n} chunks into ChromaDB collection.")
