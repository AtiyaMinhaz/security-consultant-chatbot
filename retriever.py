from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class RetrievalResult:
    score: int
    text: str


class KeywordRetriever:
    """
    Lightweight, dependency-free retriever.
    Scores KB chunks by keyword frequency (good enough for a demo / MVP).
    """

    def __init__(self, kb_texts: List[str]):
        self.kb_texts = [t for t in kb_texts if t and t.strip()]

    def search(self, query: str, top_k: int = 4) -> List[RetrievalResult]:
        q = (query or "").lower().strip()
        if not q:
            return []

        # Basic tokenization + stopword trimming (minimal)
        terms = [t for t in q.replace(",", " ").replace(".", " ").split() if len(t) >= 3]
        if not terms:
            return []

        scored: List[Tuple[int, str]] = []
        for text in self.kb_texts:
            t = text.lower()
            score = sum(t.count(term) for term in terms)
            if score > 0:
                scored.append((score, text))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [RetrievalResult(score=s, text=txt) for s, txt in scored[:top_k]]