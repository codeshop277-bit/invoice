from dataclasses import dataclass
from typing import Any, Protocol


class Embedder(Protocol):
    def embed_query(self, query: str) -> list[float]: ...


class VectorStore(Protocol):
    def similarity_search_with_score(self, query_embedding, k):
        ...


@dataclass
class RetrievedChunk:
    content: str
    score: float
    metadata: dict[str, Any]


class RetrievalPipeline:
    """Embed a query, retrieve chunks, and filter by similarity score."""

    def __init__(self, embedder, vector_store, top_k=4, score_threshold=0.70):
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        if not 0 <= score_threshold <= 1:
            raise ValueError("score_threshold must be between 0 and 1")

        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k
        self.score_threshold = score_threshold

    def retrieve(self, query):
        if not query.strip():
            raise ValueError("query must not be empty")

        query_embedding = self.embedder.embed_query(query)

        results = self.vector_store.similarity_search_with_score(
            query_embedding=query_embedding,
            k=self.top_k,
        )

        return [
            RetrievedChunk(
                content=self._get_content(document),
                score=float(score),
                metadata=self._get_metadata(document),
            )
            for document, score in results
            if float(score) >= self.score_threshold
        ]

    @staticmethod
    def _get_content(document):
        if hasattr(document, "page_content"):
            return str(document.page_content)
        if isinstance(document, dict) and "page_content" in document:
            return str(document["page_content"])
        raise ValueError("Retrieved document has no page_content")

    @staticmethod
    def _get_metadata(document):
        if hasattr(document, "metadata"):
            return dict(document.metadata)
        if isinstance(document, dict):
            return dict(document.get("metadata", {}))
        return {}
