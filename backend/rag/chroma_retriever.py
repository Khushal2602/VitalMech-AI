"""
rag/chroma_retriever.py — ChromaDB retriever (optional upgrade).

Activate by setting RAG_BACKEND=chroma in .env.
Requires: pip install chromadb sentence-transformers

This stub documents the interface — implement after Phase 2 is verified.
"""
from rag.base import Retriever


class ChromaRetriever(Retriever):
    """
    ChromaDB-backed retriever using sentence-transformer embeddings.
    Persists vector store to backend/chroma_db/.
    """

    def __init__(self):
        # TODO: initialize ChromaDB PersistentClient and collection
        raise NotImplementedError(
            "ChromaRetriever not yet implemented. Set RAG_BACKEND=simple to use SimpleRetriever."
        )

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        raise NotImplementedError("ChromaRetriever not yet implemented.")
