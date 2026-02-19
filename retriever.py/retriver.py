from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from kb_loader import KBChunk


@dataclass
class RetrievalResult:
    source: str
    score: float
    text: str


class TfidfRetriever:
    def __init__(self, chunks: List[KBChunk]) -> None:
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=30000,
        )
        self.matrix = self.vectorizer.fit_transform([c.text for c in chunks])

    def search(self, query: str, top_k: int = 4) -> List[RetrievalResult]:
        if not query.strip():
            return []
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        ranked: List[Tuple[int, float]] = sorted(
            enumerate(sims), key=lambda x: x[1], reverse=True
        )
        results: List[RetrievalResult] = []
        for idx, score in ranked[:top_k]:
            c = self.chunks[idx]
            results.append(RetrievalResult(source=c.source, score=float(score), text=c.text))
        return results
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from kb_loader import KBChunk


@dataclass
class RetrievalResult:
    source: str
    score: float
    text: str


class TfidfRetriever:
    def __init__(self, chunks: List[KBChunk]) -> None:
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=30000,
        )
        self.matrix = self.vectorizer.fit_transform([c.text for c in chunks])

    def search(self, query: str, top_k: int = 4) -> List[RetrievalResult]:
        if not query.strip():
            return []
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        ranked: List[Tuple[int, float]] = sorted(
            enumerate(sims), key=lambda x: x[1], reverse=True
        )
        results: List[RetrievalResult] = []
        for idx, score in ranked[:top_k]:
            c = self.chunks[idx]
            results.append(RetrievalResult(source=c.source, score=float(score), text=c.text))
        return results
