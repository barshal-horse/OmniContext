"""Tests for HybridRetriever (Dense + BM25 + Reciprocal Rank Fusion)."""

import os
import pytest
from backend.app.retrieval import HybridRetriever
from backend.app.config import settings

@pytest.fixture
def retriever():
    return HybridRetriever(settings.seed_data_path)

def test_corpus_loaded(retriever):
    assert len(retriever.documents) > 0
    assert retriever.avg_doc_length > 0

def test_token_bucket_search(retriever):
    results = retriever.query("Token Bucket rate limiter Redis 429", top_k=2)
    assert len(results) > 0
    top_doc = results[0]
    assert "rate" in top_doc["id"] or "Rate Limiting" in top_doc["title"]
    assert top_doc["rrf_score"] > 0

def test_jwt_auth_search(retriever):
    results = retriever.query("Authorization Bearer JWT RS256 token", top_k=2)
    assert len(results) > 0
    top_doc = results[0]
    assert "sec" in top_doc["id"] or "Authentication" in top_doc["title"]

def test_rrf_scoring_order(retriever):
    results = retriever.query("PostgreSQL multi-tenant connection pool", top_k=3)
    assert len(results) >= 2
    for i in range(len(results) - 1):
        assert results[i]["rrf_score"] >= results[i+1]["rrf_score"]
