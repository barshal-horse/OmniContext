"""
Golden Continuous Evaluation Benchmark Test Suite for OmniContext.
Executes 25+ automated assertions evaluating Context Relevancy, Faithfulness,
and Schema Adherence across enterprise domains without flaky external LLM calls.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.evals import ContinuousEvalHarness, EvalResult, BenchmarkReport
from backend.app.main import app, GOLDEN_EVAL_SET

@pytest.fixture
def eval_harness():
    return ContinuousEvalHarness(
        relevancy_threshold=0.45,
        faithfulness_threshold=0.70,
        schema_threshold=1.0
    )

@pytest.fixture
def client():
    return TestClient(app)

# ----------------- UNIT EVALUATION TESTS -----------------

def test_eval_relevancy_high_overlap(eval_harness):
    query = "Token Bucket rate limiting algorithm Redis"
    context = [
        "Enterprise endpoints enforce a distributed Token Bucket rate limiter in Redis."
    ]
    score, meta = eval_harness.compute_context_relevancy(query, context)
    assert score >= 0.70
    assert meta["matched_keywords_count"] >= 3
    assert "redis" in meta["matched_keywords"]

def test_eval_relevancy_zero_overlap(eval_harness):
    query = "quantum biology photosynthesis extraterrestrial astrophysics"
    context = [
        "PostgreSQL multi-tenant connection pooling with PgBouncer."
    ]
    score, meta = eval_harness.compute_context_relevancy(query, context)
    assert score == 0.0
    assert meta["matched_keywords_count"] == 0

def test_eval_faithfulness_grounded(eval_harness):
    context = [
        "All inbound API requests must include an Authorization header with a Bearer JWT signed via RS256. Tokens expire after 3600 seconds."
    ]
    answer = "All inbound API requests require an Authorization Bearer JWT signed with RS256. Tokens expire after 3600 seconds."
    score, meta = eval_harness.compute_faithfulness(answer, context)
    assert score >= 0.90
    assert len(meta["ungrounded_claims"]) == 0

def test_eval_faithfulness_hallucinated(eval_harness):
    context = [
        "OmniContext enforces schema-per-tenant isolation on PostgreSQL 16."
    ]
    answer = "OmniContext uses Cassandra distributed clusters running on MongoDB with quantum cryptographic blockchains."
    score, meta = eval_harness.compute_faithfulness(answer, context)
    assert score < 0.50
    assert len(meta["ungrounded_claims"]) > 0

def test_eval_schema_adherence_valid(eval_harness):
    payload = {
        "query": "Test query",
        "answer": "Test answer",
        "confidence_score": 0.92,
        "cited_doc_ids": ["doc-001"],
        "requires_human_approval": False
    }
    score, meta = eval_harness.compute_schema_adherence(payload)
    assert score == 1.0
    assert meta["status"] == "valid"

def test_eval_schema_adherence_invalid(eval_harness):
    payload = {
        "query": "Test query"
        # Missing answer and confidence_score
    }
    score, meta = eval_harness.compute_schema_adherence(payload)
    assert score == 0.0
    assert meta["status"] == "invalid"
    assert meta["errors"] is not None

# ----------------- GOLDEN BENCHMARK DATASET TESTS -----------------

def test_golden_benchmark_suite(eval_harness):
    report = eval_harness.evaluate_benchmark(GOLDEN_EVAL_SET)
    
    assert report.total_samples == len(GOLDEN_EVAL_SET)
    assert report.passed_samples == report.total_samples
    assert report.pass_rate == 100.0
    assert report.avg_context_relevancy >= 0.70
    assert report.avg_faithfulness >= 0.85
    assert report.avg_schema_adherence == 1.0
    assert report.avg_overall_score >= 0.80
    assert report.avg_latency_ms < 50.0  # Under 50ms in-process speed

def test_golden_sec_jwt_scenario(eval_harness):
    sample = GOLDEN_EVAL_SET[0]
    res = eval_harness.evaluate_sample(
        query=sample["query"],
        context_chunks=sample["context_chunks"],
        answer=sample["answer"],
        response_payload=sample["payload"]
    )
    assert res.passed is True
    assert res.context_relevancy >= 0.60
    assert res.faithfulness >= 0.80
    assert res.schema_adherence == 1.0
    assert "doc-sec-001" in res.details["schema"]["status"] or res.details["schema"]["status"] == "valid"

def test_golden_ratelimit_scenario(eval_harness):
    sample = GOLDEN_EVAL_SET[1]
    res = eval_harness.evaluate_sample(
        query=sample["query"],
        context_chunks=sample["context_chunks"],
        answer=sample["answer"],
        response_payload=sample["payload"]
    )
    assert res.passed is True
    assert res.context_relevancy >= 0.45
    assert res.faithfulness >= 0.80

def test_golden_db_scenario(eval_harness):
    sample = GOLDEN_EVAL_SET[2]
    res = eval_harness.evaluate_sample(
        query=sample["query"],
        context_chunks=sample["context_chunks"],
        answer=sample["answer"],
        response_payload=sample["payload"]
    )
    assert res.passed is True
    assert res.overall_score >= 0.80

def test_golden_mcp_scenario(eval_harness):
    sample = GOLDEN_EVAL_SET[3]
    res = eval_harness.evaluate_sample(
        query=sample["query"],
        context_chunks=sample["context_chunks"],
        answer=sample["answer"],
        response_payload=sample["payload"]
    )
    assert res.passed is True

def test_golden_guardrails_scenario(eval_harness):
    sample = GOLDEN_EVAL_SET[4]
    res = eval_harness.evaluate_sample(
        query=sample["query"],
        context_chunks=sample["context_chunks"],
        answer=sample["answer"],
        response_payload=sample["payload"]
    )
    assert res.passed is True
    assert res.schema_adherence == 1.0

# ----------------- FASTAPI EVALS HTTP ENDPOINT TESTS -----------------

def test_evals_run_endpoint(client):
    res = client.post("/api/evals/run", json={
        "query": "How are rate limits configured in Redis?",
        "auto_retrieve": True
    })
    assert res.status_code == 200
    data = res.json()
    assert "context_relevancy" in data
    assert "faithfulness" in data
    assert "schema_adherence" in data
    assert data["passed"] is True

def test_evals_benchmark_endpoint(client):
    res = client.get("/api/evals/benchmark")
    assert res.status_code == 200
    report = res.json()
    assert report["total_samples"] >= 5
    assert report["pass_rate"] >= 90.0
    assert report["avg_schema_adherence"] == 1.0
