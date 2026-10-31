"""Tests for GuardrailEngine & Pydantic v2 Contract Validation."""

import pytest
from backend.app.guardrails import GuardrailEngine, EnterpriseQueryResponse

@pytest.fixture
def engine():
    return GuardrailEngine(max_retries=2)

def test_valid_payload_passes(engine):
    valid_data = {
        "query": "How are rate limits enforced?",
        "answer": "Via Token Bucket in Redis emitting HTTP 429 when exhausted.",
        "confidence_score": 0.95,
        "cited_doc_ids": ["doc-rate-002"],
        "requires_human_approval": False
    }
    res = engine.validate_or_repair(valid_data, target_model=EnterpriseQueryResponse)
    assert res["success"] is True
    assert res["repaired"] is False
    assert res["data"]["confidence_score"] == 0.95

def test_self_healing_repair_missing_fields(engine):
    # Missing confidence_score and cited_doc_ids
    imperfect_data = {
        "question": "What is the token lifetime?",
        "answer": "3600 seconds."
    }
    res = engine.validate_or_repair(imperfect_data, target_model=EnterpriseQueryResponse)
    assert res["success"] is True
    assert res["repaired"] is True
    assert res["data"]["query"] == "What is the token lifetime?"
    assert res["data"]["confidence_score"] == 0.85
    assert res["data"]["cited_doc_ids"] == []

def test_markdown_code_block_stripping(engine):
    wrapped_json = """
    ```json
    {
        "query": "Postgres pool size?",
        "answer": "20 connections per pod.",
        "confidence_score": 0.9,
        "cited_doc_ids": ["doc-db-003"]
    }
    ```
    """
    res = engine.validate_or_repair(wrapped_json, target_model=EnterpriseQueryResponse)
    assert res["success"] is True
    assert res["data"]["query"] == "Postgres pool size?"
