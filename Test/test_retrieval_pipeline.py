import pytest
from retrieval_pipeline import RetrievalPipeline


class FakeEmbedder:
    def __init__(self):
        self.queries = []

    def embed_query(self, query):
        self.queries.append(query)
        return [0.1, 0.2, 0.3]


class FakeDocument:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}


class FakeVectorStore:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def similarity_search_with_score(self, query_embedding, k):
        self.calls.append({"query_embedding": query_embedding, "k": k})
        return self.results


def test_retrieve_returns_only_chunks_above_threshold():
    embedder = FakeEmbedder()
    store = FakeVectorStore([
        (FakeDocument("Relevant chunk", {"page": 1}), 0.91),
        (FakeDocument("Weak chunk", {"page": 2}), 0.55),
        (FakeDocument("Another relevant chunk", {"page": 3}), 0.80),
    ])
    pipeline = RetrievalPipeline(embedder, store, top_k=3, score_threshold=0.70)

    results = pipeline.retrieve("How does RAG work?")

    assert len(results) == 2
    assert results[0].content == "Relevant chunk"
    assert results[0].score == 0.91
    assert results[0].metadata == {"page": 1}
    assert results[1].content == "Another relevant chunk"
    assert embedder.queries == ["How does RAG work?"]
    assert store.calls[0]["k"] == 3


def test_retrieve_rejects_empty_query():
    pipeline = RetrievalPipeline(FakeEmbedder(), FakeVectorStore([]))
    with pytest.raises(ValueError, match="query must not be empty"):
        pipeline.retrieve("   ")


def test_pipeline_validates_top_k():
    with pytest.raises(ValueError, match="top_k"):
        RetrievalPipeline(FakeEmbedder(), FakeVectorStore([]), top_k=0)


def test_pipeline_validates_score_threshold():
    with pytest.raises(ValueError, match="score_threshold"):
        RetrievalPipeline(FakeEmbedder(), FakeVectorStore([]), score_threshold=1.5)


def test_retrieve_supports_dictionary_documents():
    store = FakeVectorStore([
        ({"page_content": "Dictionary document",
          "metadata": {"source": "test.pdf"}}, 0.85)
    ])
    pipeline = RetrievalPipeline(FakeEmbedder(), store)

    results = pipeline.retrieve("test query")

    assert len(results) == 1
    assert results[0].content == "Dictionary document"
    assert results[0].metadata == {"source": "test.pdf"}


def test_retrieve_raises_for_invalid_document():
    store = FakeVectorStore([
        ({"content": "missing page_content"}, 0.90)
    ])
    pipeline = RetrievalPipeline(FakeEmbedder(), store)

    with pytest.raises(ValueError, match="no page_content"):
        pipeline.retrieve("test query")
