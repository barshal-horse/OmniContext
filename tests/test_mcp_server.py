"""Tests for OmniContextMCPServer (Model Context Protocol conformance)."""

import pytest
from backend.app.mcp_server import OmniContextMCPServer

@pytest.fixture
def mcp():
    return OmniContextMCPServer()

def test_mcp_metadata(mcp):
    meta = mcp.get_server_metadata()
    assert meta["name"] == "OmniContext-Gateway"
    assert meta["capabilities"]["tools"] is True
    assert meta["capabilities"]["resources"] is True

def test_mcp_list_resources(mcp):
    res = mcp.list_resources()
    assert len(res) > 0
    assert any("doc-sec-001" in r["uri"] for r in res)

def test_mcp_tool_execution_query(mcp):
    call_res = mcp.call_tool("query_hybrid_context", {"query": "Token bucket rate limit", "top_k": 2})
    assert "results" in call_res
    assert call_res["count"] > 0
    assert "rate" in call_res["results"][0]["id"]

def test_mcp_tool_execution_guardrail(mcp):
    payload = {
        "query": "Test query",
        "answer": "Test answer",
        "confidence_score": 0.92
    }
    call_res = mcp.call_tool("verify_schema_contract", {"payload": payload})
    assert call_res["success"] is True
