"""Offline evaluation harness for the RAG Helpdesk Agent.

Runs retrieval + the refusal gate against a fixed set of labelled questions and
checks two behaviours that matter most for a helpdesk RAG:

  1. In-scope questions are answerable and retrieve the expected source.
  2. Out-of-scope questions are **refused** (no hallucination).

No API key or network is required, so this can run in CI on every PR.
Exits non-zero if any case fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag_helpdesk.chunking import load_corpus  # noqa: E402
from rag_helpdesk.gate import DEFAULT_MIN_SCORE, assess  # noqa: E402
from rag_helpdesk.retriever import BM25Retriever  # noqa: E402


def main() -> int:
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    retriever = BM25Retriever(load_corpus(ROOT / "corpus"))

    passed = failed = 0
    print(f"{'result':6} {'expect':7} {'top source':24} {'score':>6}  question")
    print("-" * 90)
    for case in cases:
        hits = retriever.retrieve(case["question"], k=4)
        gate = assess(hits, min_score=DEFAULT_MIN_SCORE)
        top_src = hits[0].chunk.source if hits else "-"

        if case["expect"] == "refuse":
            ok = not gate.answerable
        else:
            ok = gate.answerable and ("source" not in case or top_src == case["source"])

        passed += ok
        failed += not ok
        print(
            f"{'PASS' if ok else 'FAIL':6} {case['expect']:7} {top_src:24} "
            f"{gate.top_score:6.2f}  {case['question']}"
        )

    print("-" * 90)
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
