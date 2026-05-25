"""RAG Helpdesk Agent — command-line entry point.

Usage:
    python -m rag_helpdesk.cli ask "有給休暇は何日前までに申請しますか?"
    python -m rag_helpdesk.cli ask "..." --provider anthropic
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .answer import compose
from .chunking import load_corpus
from .gate import DEFAULT_MIN_SCORE, assess
from .retriever import BM25Retriever

DEFAULT_CORPUS = Path(__file__).resolve().parent.parent / "corpus"


def _cmd_ask(args: argparse.Namespace) -> int:
    retriever = BM25Retriever(load_corpus(args.corpus))
    hits = retriever.retrieve(args.question, k=args.k)
    gate = assess(hits, min_score=args.min_score)
    answer = compose(args.question, hits, gate, provider=args.provider, model=args.model)

    print(answer.text)
    if not answer.refused:
        print("\n--- 根拠 (retrieved) ---")
        for i, h in enumerate(hits, 1):
            print(f"[{i}] {h.chunk.citation}  (score={h.score:.2f})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rag-helpdesk", description="社内ドキュメントRAGヘルプデスク (Acme AI Corp demo)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    ask = sub.add_parser("ask", help="質問する")
    ask.add_argument("question", help="質問文")
    ask.add_argument(
        "--provider",
        default="extractive",
        choices=["extractive", "openai", "anthropic"],
        help="回答生成プロバイダ (default: extractive — APIキー不要)",
    )
    ask.add_argument("--model", default=None, help="モデル名 (provider依存)")
    ask.add_argument("--k", type=int, default=4, help="取得チャンク数")
    ask.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE, help="回答する最小スコア")
    ask.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS, help="コーパスディレクトリ")
    ask.set_defaults(func=_cmd_ask)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
