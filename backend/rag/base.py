"""
rag/base.py — Abstract base class for all retriever implementations.

Concrete implementations:
  SimpleRetriever  (simple_retriever.py) — keyword match on knowledge JSON
  ChromaRetriever  (chroma_retriever.py) — ChromaDB + sentence-transformers
"""
from abc import ABC, abstractmethod


class Retriever(ABC):
    """
    All RAG backends must implement this interface.
    The pipeline calls retrieve() without knowing which backend is active.
    """

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """
        Given a query string, return the top_k most relevant
        knowledge document content strings.
        """
        ...
