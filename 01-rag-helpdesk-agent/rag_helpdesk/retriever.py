"""In-memory BM25 retriever (Okapi BM25, dependency-free).

The ``Retriever`` surface is intentionally tiny (``retrieve(query, k) -> [Hit]``)
so the lexical backend can be swapped for an embedding + vector-DB backend
without touching the gate / answer / CLI layers. See README "Future improvements".
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from .chunking import Chunk
from .tokenizer import tokenize


@dataclass
class Hit:
    chunk: Chunk
    score: float


class BM25Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        if not chunks:
            raise ValueError("cannot build a retriever over an empty corpus")
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self._docs = [tokenize(c.text) for c in chunks]
        self._doc_len = [len(d) for d in self._docs]
        self._avgdl = sum(self._doc_len) / len(self._docs)
        self._tf = [Counter(d) for d in self._docs]

        df: Counter[str] = Counter()
        for doc in self._docs:
            for term in set(doc):
                df[term] += 1
        n = len(self._docs)
        self._idf = {
            term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()
        }

    def _score(self, q_terms: list[str], i: int) -> float:
        tf = self._tf[i]
        dl = self._doc_len[i]
        score = 0.0
        for term in q_terms:
            freq = tf.get(term, 0)
            if not freq:
                continue
            idf = self._idf.get(term, 0.0)
            denom = freq + self.k1 * (1 - self.b + self.b * dl / self._avgdl)
            score += idf * (freq * (self.k1 + 1)) / denom
        return score

    def retrieve(self, query: str, k: int = 4) -> list[Hit]:
        q_terms = tokenize(query)
        hits = [Hit(self.chunks[i], self._score(q_terms, i)) for i in range(len(self.chunks))]
        hits.sort(key=lambda h: h.score, reverse=True)
        return [h for h in hits[:k] if h.score > 0.0]
