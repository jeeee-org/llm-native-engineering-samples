"""RAG Helpdesk Agent — a small, dependency-free RAG sample.

Pipeline: load corpus -> chunk -> BM25 retrieve -> refusal gate -> answer
(extractive by default; OpenAI / Anthropic optional).
"""

__all__ = ["chunking", "tokenizer", "retriever", "gate", "answer"]
