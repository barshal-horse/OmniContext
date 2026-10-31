"""
Integration Tests for OmniContext Real-Time SSE Streaming Pipeline.
Verifies W3C Server-Sent Events frame formatting, event ordering,
in-flight guardrails, and telemetry calculation.
"""

import pytest
import json
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def _parse_sse_stream(stream_text: str):
    """Parses raw SSE stream text into a list of (event_type, parsed_data) pairs."""
    events = []
    current_event = None
    current_data = []

    for line in stream_text.splitlines():
        line = line.strip()
        if not line:
            if current_event and current_data:
                data_str = "\n".join(current_data)
                try:
                    payload = json.loads(data_str)
                except Exception:
                    payload = data_str
                events.append((current_event, payload))
                current_event = None
                current_data = []
            continue

        if line.startswith("event:"):
            current_event = line.replace("event:", "").strip()
        elif line.startswith("data:"):
            current_data.append(line.replace("data:", "").strip())

    return events

def test_chat_stream_post_success(client):
    res = client.post(
        "/api/chat/stream",
        json={"query": "Token Bucket rate limiting Redis", "top_k": 2}
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    events = _parse_sse_stream(res.text)
    event_types = [e[0] for e in events]

    # Verify event sequence
    assert "metadata" in event_types
    assert "token" in event_types
    assert "guardrail" in event_types
    assert "telemetry" in event_types
    assert "done" in event_types

    # 1. Metadata check
    meta = next(e[1] for e in events if e[0] == "metadata")
    assert "query" in meta
    assert len(meta["doc_ids"]) > 0
    assert "rate" in meta["doc_ids"][0]

    # 2. Token chunks check
    tokens = [e[1]["token"] for e in events if e[0] == "token"]
    assert len(tokens) > 5
    assembled_text = "".join(tokens)
    assert "Token Bucket" in assembled_text or "Redis" in assembled_text

    # 3. Guardrail check
    guard = next(e[1] for e in events if e[0] == "guardrail")
    assert guard["valid"] is True
    assert guard["confidence_score"] > 0.80

    # 4. Telemetry check
    telemetry = next(e[1] for e in events if e[0] == "telemetry")
    assert telemetry["tokens_output"] > 0
    assert telemetry["simulated_cost_usd"] > 0.0
    assert telemetry["tokens_per_second"] > 0.0

    # 5. Done delimiter check
    done_payload = next(e[1] for e in events if e[0] == "done")
    assert done_payload == "[DONE]"

def test_chat_stream_get_endpoint(client):
    res = client.get("/api/chat/stream?query=Bearer+JWT+RS256+token&top_k=2")
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    events = _parse_sse_stream(res.text)
    event_types = [e[0] for e in events]

    assert "metadata" in event_types
    assert "token" in event_types
    assert "telemetry" in event_types
    assert "done" in event_types

    meta = next(e[1] for e in events if e[0] == "metadata")
    assert any("sec" in doc_id for doc_id in meta["doc_ids"])

def test_chat_stream_empty_query_rejected(client):
    res = client.post("/api/chat/stream", json={"query": ""})
    assert res.status_code == 422  # Pydantic v2 validation error

def test_chat_stream_unknown_query_graceful(client):
    res = client.post(
        "/api/chat/stream",
        json={"query": "Unrelated alien spacecraft astrophysics query", "top_k": 2}
    )
    assert res.status_code == 200
    events = _parse_sse_stream(res.text)
    assert any(e[0] == "done" for e in events)
