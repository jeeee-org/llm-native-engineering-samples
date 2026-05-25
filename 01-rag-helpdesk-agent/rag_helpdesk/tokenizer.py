"""CJK-aware tokenizer for dependency-free lexical retrieval.

No external morphological analyzer (MeCab etc.) is required:
- ASCII alphanumeric runs are kept as whole tokens.
- CJK / kana runs are expanded into character **bigrams**, a standard
  language-agnostic technique for Japanese/Chinese full-text search.

Pure-hiragana bigrams are dropped: in Japanese, hiragana mostly encodes
particles and inflections (は / です / ますか …), which are shared by almost
every sentence and act as noise. Keeping only bigrams that contain a kanji or
katakana character concentrates the signal on content words — without this,
question-style queries spuriously match any question-style document.

This keeps the offline path zero-dependency while still giving usable recall on
Japanese documents. See README "Future improvements" for swapping in an
embedding-based retriever.
"""
from __future__ import annotations

import re

_ASCII = re.compile(r"[a-z0-9]+")
# Hiragana, Katakana, CJK Unified Ideographs, half-width Katakana.
_CJK = re.compile(r"[぀-ヿ㐀-鿿ｦ-ﾟ]+")


def _is_hiragana(ch: str) -> bool:
    return "぀" <= ch <= "ゟ"


def tokenize(text: str) -> list[str]:
    """Return a list of search tokens for *text*."""
    text = text.lower()
    tokens: list[str] = []
    for m in _ASCII.finditer(text):
        tokens.append(m.group())
    for m in _CJK.finditer(text):
        run = m.group()
        if len(run) == 1:
            if not _is_hiragana(run):
                tokens.append(run)
            continue
        for i in range(len(run) - 1):
            bigram = run[i : i + 2]
            # Skip noise bigrams made entirely of hiragana (particles/inflections).
            if _is_hiragana(bigram[0]) and _is_hiragana(bigram[1]):
                continue
            tokens.append(bigram)
    return tokens
