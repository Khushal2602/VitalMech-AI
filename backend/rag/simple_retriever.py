"""
rag/simple_retriever.py -- Keyword-based retriever (Phase 2 MVP).

Scoring approach: BM25-inspired TF-IDF with title boosting.
  - Term frequencies are capped (BM25 saturation) so a term repeated 50 times
    in a long document doesn't completely dominate.
  - IDF uses a steeper penalty so ultra-common terms (pressure, high, temperature)
    that appear in almost every doc contribute very little.
  - Title tokens are indexed separately with a 3x boost weight, so a document
    whose title contains "cavitation" or "overheating" scores much higher for
    those terms than a document that only mentions them in passing.
  - No external libraries required -- pure Python stdlib only.
"""
import json
import math
import re
from pathlib import Path
from typing import NamedTuple

from rag.base import Retriever

_KNOWLEDGE_FILE = Path(__file__).parent.parent / "knowledge" / "mechanical_faults.json"

# Common English stopwords to exclude from scoring
_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "to", "for", "is", "are",
    "was", "be", "by", "on", "at", "as", "it", "its", "from", "with",
    "that", "this", "if", "not", "may", "can", "will", "should", "have",
    "has", "had", "but", "also", "all", "any", "both", "each", "more",
    "than", "then", "when", "which", "who", "how", "do", "does", "their",
    "they", "them", "these", "those", "into", "through", "during", "before",
    "after", "above", "below", "between", "out", "up", "down", "off",
    # Domain terms that appear in nearly every doc -- too common to be useful for ranking
    "high", "low", "check", "replace", "fault", "failure", "machine",
    "operating", "normal", "indicates", "causes", "caused", "cause",
    "increased", "increasing", "reduce", "reduced", "possible",
}

# BM25 saturation parameter k1: higher = more reward for repeated terms (typical: 1.2-2.0)
_BM25_K1 = 1.5
# Title field boost multiplier -- higher value makes title keyword matches dominant
_TITLE_BOOST = 5.0


class ScoredDocument(NamedTuple):
    doc_id: str
    title: str
    score: float
    content: str


class SimpleRetriever(Retriever):
    """
    TF-IDF weighted keyword retriever over a local JSON knowledge base.

    Public methods:
      retrieve(query, top_k)         → list[str]  (plain content strings, for LLM context)
      retrieve_scored(query, top_k)  → list[ScoredDocument]  (with metadata, for testing)
    """

    def __init__(self):
        self._docs: list[dict] = []
        self._doc_tokens: list[dict[str, int]] = []   # per-doc term frequencies
        self._df: dict[str, int] = {}                  # document frequency per term
        self._n_docs: int = 0
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lowercase, strip punctuation, split into tokens, drop stopwords."""
        raw = re.findall(r"[a-z]+", text.lower())
        return [t for t in raw if t not in _STOPWORDS and len(t) > 2]

    @staticmethod
    def _term_freq(tokens: list[str]) -> dict[str, int]:
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        return tf

    def _load(self) -> None:
        if not _KNOWLEDGE_FILE.exists():
            return
        with open(_KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            self._docs = json.load(f)

        self._n_docs = len(self._docs)
        self._doc_tokens = []   # combined TF (title-boosted + content)
        self._df = {}           # document frequency per term

        for doc in self._docs:
            title_tokens = self._tokenize(doc.get("title", ""))
            content_tokens = self._tokenize(doc.get("content", ""))

            # Build combined TF: title tokens count with TITLE_BOOST weight
            combined: dict[str, float] = {}
            for t in content_tokens:
                combined[t] = combined.get(t, 0.0) + 1.0
            for t in title_tokens:
                combined[t] = combined.get(t, 0.0) + _TITLE_BOOST

            self._doc_tokens.append(combined)
            # DF tracks unique terms per doc (not boosted counts)
            for term in set(title_tokens) | set(content_tokens):
                self._df[term] = self._df.get(term, 0) + 1

    def _score(self, query_tokens: list[str], doc_tf: dict[str, float]) -> float:
        """
        BM25-inspired score:
          idf = log( (N - df + 0.5) / (df + 0.5) + 1 )   [Robertson IDF, always >= 0]
          tf_sat = tf * (k1 + 1) / (tf + k1)              [BM25 TF saturation]
          score += idf * tf_sat
        """
        if not query_tokens or not doc_tf:
            return 0.0
        score = 0.0
        for term in query_tokens:
            if term in doc_tf:
                tf = doc_tf[term]
                df = self._df.get(term, 1)
                n = self._n_docs
                idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
                tf_sat = tf * (_BM25_K1 + 1.0) / (tf + _BM25_K1)
                score += idf * tf_sat
        return score

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """
        Return top_k document content strings most relevant to query.
        Returns empty list if knowledge base is empty or no query given.
        """
        results = self.retrieve_scored(query, top_k)
        return [r.content for r in results]

    def retrieve_scored(self, query: str, top_k: int = 3) -> list[ScoredDocument]:
        """
        Return top_k ScoredDocument(doc_id, title, score, content) sorted by score.
        Useful for testing and debugging retrieval quality.
        """
        if not self._docs or not query.strip():
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored: list[ScoredDocument] = []
        for doc, doc_tf in zip(self._docs, self._doc_tokens):
            score = self._score(query_tokens, doc_tf)
            if score > 0:
                scored.append(ScoredDocument(
                    doc_id=doc.get("id", ""),
                    title=doc.get("title", ""),
                    score=round(score, 3),
                    content=doc.get("content", ""),
                ))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]
