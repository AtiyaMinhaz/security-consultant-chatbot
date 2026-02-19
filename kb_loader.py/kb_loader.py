from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class KBChunk:
    source: str
    text: str


def load_kb(kb_dir: str = "kb") -> List[KBChunk]:
    """
    Loads markdown files from kb_dir into KBChunk objects.
    We keep it simple and treat each file as one chunk.
    """
    base = Path(kb_dir)
    if not base.exists():
        raise FileNotFoundError(f"Knowledge base folder not found: {kb_dir}")

    chunks: List[KBChunk] = []
    for md in sorted(base.glob("*.md")):
        text = md.read_text(encoding="utf-8").strip()
        if text:
            chunks.append(KBChunk(source=md.name, text=text))
    if not chunks:
        raise ValueError("Knowledge base is empty. Add .md files into /kb.")
    return chunks
