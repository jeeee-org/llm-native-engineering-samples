"""Refusal gate — decide whether retrieval is strong enough to answer.

A lexical (BM25) score has no absolute meaning across corpora, so the threshold
here is **calibrated for the bundled Acme corpus** (see ``evals/``). A production
system should calibrate per corpus, or gate on a normalized embedding similarity
/ cross-encoder score instead. See README "Failure modes".
"""
from __future__ import annotations

from dataclasses import dataclass

from .retriever import Hit

# Calibrated against evals/cases.json: in-scope questions score >= ~6,
# out-of-scope questions score <= ~4.6, so 5.0 cleanly separates them.
DEFAULT_MIN_SCORE = 5.0


@dataclass
class GateResult:
    answerable: bool
    top_score: float
    reason: str


def assess(hits: list[Hit], min_score: float = DEFAULT_MIN_SCORE) -> GateResult:
    if not hits:
        return GateResult(False, 0.0, "no documents matched the query")
    top = hits[0].score
    if top < min_score:
        return GateResult(False, top, f"top score {top:.2f} below threshold {min_score:.2f}")
    return GateResult(True, top, "sufficient retrieval confidence")
