"""Split markdown corpus files into retrievable chunks by heading.

Each chunk carries a stable id and a human-readable citation (``file#heading``)
so answers can always point back to their source.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str  # file name
    heading: str
    text: str

    @property
    def citation(self) -> str:
        return f"{self.source}#{self.heading}" if self.heading else self.source


def _split_sections(md: str) -> Iterator[tuple[str, str]]:
    """Yield (heading, body) pairs, splitting on markdown heading lines."""
    heading = ""
    buf: list[str] = []
    for line in md.splitlines():
        if line.lstrip().startswith("#"):
            if any(s.strip() for s in buf):
                yield heading, "\n".join(buf).strip()
            heading = line.lstrip("#").strip()
            buf = []
        else:
            buf.append(line)
    if any(s.strip() for s in buf):
        yield heading, "\n".join(buf).strip()


def load_corpus(corpus_dir: str | Path) -> list[Chunk]:
    """Load and chunk every ``*.md`` file under *corpus_dir*."""
    corpus_dir = Path(corpus_dir)
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.glob("*.md")):
        md = path.read_text(encoding="utf-8")
        for i, (heading, body) in enumerate(_split_sections(md)):
            if not body:
                continue
            # Prepend the heading to the body so heading terms are searchable.
            text = f"{heading}\n{body}" if heading else body
            chunks.append(Chunk(id=f"{path.name}::{i}", source=path.name, heading=heading, text=text))
    return chunks
