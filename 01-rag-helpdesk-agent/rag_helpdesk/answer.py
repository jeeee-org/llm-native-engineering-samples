"""Answer composition with mandatory citations and an explicit refusal path.

Providers:
  - ``extractive`` (default): returns grounded snippets from the retrieved
    chunks. No network / API key required, fully deterministic — this is what
    the tests and CI exercise.
  - ``openai`` / ``anthropic``: generate a grounded answer constrained to the
    retrieved context. SDKs are imported lazily so the offline path stays
    dependency-free.

The contract for every provider: answer **only** from the supplied context, cite
sources, and refuse ("わかりません") when the context is insufficient.
"""
from __future__ import annotations

from dataclasses import dataclass

from .gate import GateResult
from .retriever import Hit

REFUSAL = "わかりません。提供された社内ドキュメントに該当する記述が見つかりませんでした。"

SYSTEM_PROMPT = (
    "あなたは社内ヘルプデスクAIです。必ず以下のコンテキストの内容だけに基づいて、"
    "日本語で簡潔に回答してください。コンテキストに無い情報は推測せず、"
    f"その場合は「{REFUSAL}」とだけ答えてください。"
    "回答の末尾には、使用した根拠を [1] [2] の形式で必ず示してください。"
)


@dataclass
class Answer:
    text: str
    citations: list[str]
    refused: bool


def _format_context(hits: list[Hit]) -> str:
    return "\n\n".join(f"[{i}] ({h.chunk.citation})\n{h.chunk.text}" for i, h in enumerate(hits, 1))


def compose(
    question: str,
    hits: list[Hit],
    gate: GateResult,
    provider: str = "extractive",
    model: str | None = None,
) -> Answer:
    """Build an :class:`Answer` for *question* from retrieved *hits*."""
    if not gate.answerable:
        return Answer(REFUSAL, [], refused=True)

    citations = [h.chunk.citation for h in hits]

    if provider == "extractive":
        top = hits[0]
        text = f"{top.chunk.text}\n\n[1] {top.chunk.citation}"
        return Answer(text, [top.chunk.citation], refused=False)

    context = _format_context(hits)
    user = f"# コンテキスト\n{context}\n\n# 質問\n{question}"
    if provider == "openai":
        text = _answer_openai(user, model or "gpt-4o-mini")
    elif provider == "anthropic":
        text = _answer_anthropic(user, model or "claude-haiku-4-5-20251001")
    else:
        raise ValueError(f"unknown provider: {provider!r}")
    return Answer(text, citations, refused=False)


def _answer_openai(user: str, model: str) -> str:
    from openai import OpenAI  # lazy import — only needed for this provider

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


def _answer_anthropic(user: str, model: str) -> str:
    from anthropic import Anthropic  # lazy import — only needed for this provider

    client = Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        # cache_control marks the static system prompt as cacheable — the
        # idiomatic way to cut cost/latency when the same instructions are reused.
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    return "\n".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
