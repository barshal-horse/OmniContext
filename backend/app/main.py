"""
OmniContext Gateway — Core FastAPI Application.
Exposes REST endpoints, Model Context Protocol (MCP) dispatchers,
real-time Server-Sent Events (SSE) streaming, and continuous evaluation harness.
"""

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, AsyncGenerator
import time
import json
import asyncio
import re

from backend.app.config import settings
from backend.app.mcp_server import OmniContextMCPServer
from backend.app.retrieval import HybridRetriever
from backend.app.guardrails import GuardrailEngine, EnterpriseQueryResponse
from backend.app.evals import ContinuousEvalHarness, EvalResult, BenchmarkReport

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise Model Context Protocol Gateway & Evaluation Proxy"
)

# CORS middleware for Next.js / Streamlit cockpits
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP, retrieval, guardrail, and evals subsystems
mcp_server = OmniContextMCPServer()
retriever = HybridRetriever(settings.seed_data_path)
guardrail_engine = GuardrailEngine()
eval_harness = ContinuousEvalHarness()

# ----------------- SCHEMAS -----------------

class QueryRequest(BaseModel):
    query: str = Field(min_length=1, description="Search query")
    top_k: Optional[int] = Field(default=3, ge=1, le=10)

class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ChatStreamRequest(BaseModel):
    query: str = Field(min_length=1, description="User prompt or technical inquiry")
    top_k: Optional[int] = Field(default=3, ge=1, le=10, description="Number of context documents to retrieve")
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=512, ge=16, le=2048)

class EvalSampleRequest(BaseModel):
    query: str
    context_chunks: Optional[List[str]] = None
    answer: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    auto_retrieve: Optional[bool] = True

# ----------------- GOLDEN BENCHMARK DATASET -----------------

GOLDEN_EVAL_SET = [
    {
        "id": "gold-sec-01",
        "query": "How is authentication handled and what happens if a JWT is revoked?",
        "context_chunks": [
            "All inbound API requests must include an Authorization header with a Bearer JWT signed via RS256. Tokens expire after 3600 seconds. Replay protection is enforced by validating the jti against Redis. Revoked tokens return HTTP 401 with error code AUTH_TOKEN_REVOKED."
        ],
        "answer": "Authentication requires an Authorization Bearer JWT signed with RS256, which expires after 3600 seconds. If a token is revoked, the gateway returns HTTP 401 with error code AUTH_TOKEN_REVOKED.",
        "payload": {
            "query": "How is authentication handled and what happens if a JWT is revoked?",
            "answer": "Authentication requires an Authorization Bearer JWT signed with RS256. Revoked tokens return HTTP 401 with error code AUTH_TOKEN_REVOKED.",
            "confidence_score": 0.96,
            "cited_doc_ids": ["doc-sec-001"],
            "requires_human_approval": False
        }
    },
    {
        "id": "gold-rate-02",
        "query": "What algorithm enforces rate limits and what HTTP error is returned when quota is exceeded?",
        "context_chunks": [
            "Enterprise endpoints enforce a distributed Token Bucket rate limiter in Redis. Each tenant is allocated 60 requests per minute with a burst capacity of 10. When capacity is exceeded, the gateway emits HTTP 429 Too Many Requests with headers X-RateLimit-Limit, X-RateLimit-Remaining, and Retry-After."
        ],
        "answer": "Rate limiting is governed by a distributed Token Bucket algorithm in Redis. When the tenant quota is exceeded, the gateway returns an HTTP 429 Too Many Requests response with a Retry-After header.",
        "payload": {
            "query": "What algorithm enforces rate limits and what HTTP error is returned when quota is exceeded?",
            "answer": "Rate limiting uses a distributed Token Bucket in Redis emitting HTTP 429 Too Many Requests.",
            "confidence_score": 0.98,
            "cited_doc_ids": ["doc-rate-002"],
            "requires_human_approval": False
        }
    },
    {
        "id": "gold-db-03",
        "query": "What is the maximum PostgreSQL connection pool size and query timeout?",
        "context_chunks": [
            "OmniContext enforces schema-per-tenant isolation on PostgreSQL 16. Connection pooling is managed via PgBouncer in transaction pooling mode. Maximum pool size is configured to 20 connections per pod with a query timeout of 5000ms."
        ],
        "answer": "The maximum pool size is 20 connections per pod managed by PgBouncer, and the query timeout is configured to 5000ms.",
        "payload": {
            "query": "What is the maximum PostgreSQL connection pool size and query timeout?",
            "answer": "Maximum pool size is 20 connections per pod with a 5000ms query timeout.",
            "confidence_score": 0.95,
            "cited_doc_ids": ["doc-db-003"],
            "requires_human_approval": False
        }
    },
    {
        "id": "gold-mcp-04",
        "query": "How does MCP expose tools and what transports are supported for agent integration?",
        "context_chunks": [
            "The gateway implements the Anthropic Model Context Protocol specification v1.0. Tools are exposed with strict JSON schema definitions. Clients connect via stdio for local subprocess execution or Server-Sent Events (SSE) on /mcp/events for network-isolated agent microservices. Tool calls require explicit capability handshakes. Both stdio and SSE network transports are supported for agent integration."
        ],
        "answer": "MCP tools are exposed with strict JSON schema definitions. Supported transports include stdio for local execution and Server-Sent Events (SSE) for network agents.",
        "payload": {
            "query": "How does MCP expose tools and what transports are supported for agent integration?",
            "answer": "Tools are exposed via strict JSON schemas, supporting stdio and SSE transports.",
            "confidence_score": 0.94,
            "cited_doc_ids": ["doc-mcp-004"],
            "requires_human_approval": False
        }
    },
    {
        "id": "gold-guard-05",
        "query": "How does the guardrail engine handle validation failures when models produce malformed outputs?",
        "context_chunks": [
            "All model outputs are intercepted by the Guardrail engine and parsed against target Pydantic v2 schemas. If validation fails due to missing keys or type mismatch, the engine triggers an automatic reflection loop with error context (max 2 retries). If retries fail, a typed 422 Unprocessable Entity error is returned without silent fallback."
        ],
        "answer": "When outputs fail Pydantic v2 validation, the engine initiates an automated reflection repair loop for up to 2 retries. If the output remains invalid, it fails closed with HTTP 422 Unprocessable Entity.",
        "payload": {
            "query": "How does the guardrail engine handle validation failures when models produce malformed outputs?",
            "answer": "The engine runs a reflection repair loop (up to 2 retries) before failing closed with HTTP 422.",
            "confidence_score": 0.97,
            "cited_doc_ids": ["doc-guard-005"],
            "requires_human_approval": False
        }
    }
]

# ----------------- BASELINE ENDPOINTS -----------------

@app.get("/")
def read_root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "mcp_enabled": True,
        "offline_mode": settings.offline_mock_mode,
        "endpoints": {
            "chat_stream": "/api/chat/stream",
            "mcp_metadata": "/mcp/metadata",
            "evals_benchmark": "/api/evals/benchmark"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "timestamp": time.time(),
        "documents_loaded": len(retriever.documents)
    }

# ----------------- MCP PROTOCOL ENDPOINTS -----------------

@app.get("/mcp/metadata")
def get_mcp_metadata():
    return mcp_server.get_server_metadata()

@app.get("/mcp/resources")
def list_mcp_resources():
    return {"resources": mcp_server.list_resources()}

@app.get("/mcp/tools")
def list_mcp_tools():
    return {"tools": mcp_server.list_tools()}

@app.post("/mcp/call")
def call_mcp_tool(req: ToolCallRequest):
    try:
        result = mcp_server.call_tool(req.tool_name, req.arguments)
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal tool error: {str(e)}")

# ----------------- HYBRID SEARCH & GUARDRAILS -----------------

@app.post("/api/retrieve")
def search_hybrid(req: QueryRequest):
    start = time.perf_counter()
    results = retriever.query(req.query, top_k=req.top_k or 3)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "query": req.query,
        "results": results,
        "count": len(results),
        "latency_ms": elapsed_ms
    }

@app.post("/api/validate-contract")
def validate_contract(payload: Dict[str, Any]):
    return guardrail_engine.validate_or_repair(payload, target_model=EnterpriseQueryResponse)

# ----------------- REAL-TIME SSE STREAMING PIPELINE -----------------

def _synthesize_offline_response(query: str, docs: List[Dict[str, Any]]) -> str:
    """
    Synthesizes a grounded factual response directly from top retrieved documents
    for zero-credential offline demo and testing resilience.
    """
    if not docs:
        return "I could not locate authoritative enterprise documentation covering this query in the corpus."
    
    top = docs[0]
    # Compose structured response grounded in retrieved document content
    return (
        f"According to enterprise documentation ({top.get('title', 'Unknown')}), "
        f"{top.get('content', '')}"
    )

async def _sse_generator(
    request: Request,
    query: str,
    top_k: int = 3,
    chunk_delay: float = 0.008
) -> AsyncGenerator[str, None]:
    """
    Asynchronous Server-Sent Events generator.
    Yields strictly formatted W3C SSE frames: event: <type>\ndata: <json>\n\n
    """
    t_start = time.perf_counter()
    first_token_time = None

    # Step 1: Hybrid Context Retrieval
    docs = retriever.query(query, top_k=top_k)
    cited_ids = [d["id"] for d in docs]

    # [FDE-WHY]: Emit metadata event first so UI cockpits immediately render
    # retrieved sources and citations before the first token is synthesized.
    meta_event = {
        "query": query,
        "doc_ids": cited_ids,
        "retrieved_docs": [
            {
                "id": d["id"],
                "title": d["title"],
                "category": d["category"],
                "rrf_score": d["rrf_score"]
            }
            for d in docs
        ],
        "timestamp": time.time(),
        "offline_mock_mode": settings.offline_mock_mode
    }
    yield f"event: metadata\ndata: {json.dumps(meta_event)}\n\n"

    # Step 2: Stream Tokens
    full_text = _synthesize_offline_response(query, docs)
    # Split text into small word-level streaming chunks
    words = re.findall(r'\S+\s*', full_text)
    total_tokens = len(words)

    for idx, word in enumerate(words):
        # [FDE-WHY]: Check client disconnect eagerly on every iteration to abort
        # computation immediately if user navigates away or cancels stream.
        if await request.is_disconnected():
            break

        if first_token_time is None:
            first_token_time = time.perf_counter()

        token_event = {
            "index": idx,
            "token": word,
            "is_first": (idx == 0)
        }
        yield f"event: token\ndata: {json.dumps(token_event)}\n\n"

        # Cooperative async yield
        if chunk_delay > 0:
            await asyncio.sleep(chunk_delay)
        else:
            await asyncio.sleep(0)

    t_end = time.perf_counter()
    first_token_ms = round(((first_token_time - t_start) * 1000.0), 2) if first_token_time else 0.0
    total_duration_ms = round(((t_end - t_start) * 1000.0), 2)

    # Step 3: Guardrail Contract Validation Gate
    raw_payload = {
        "query": query,
        "answer": full_text,
        "confidence_score": 0.94 if docs else 0.40,
        "cited_doc_ids": cited_ids,
        "requires_human_approval": False
    }
    guard_res = guardrail_engine.validate_or_repair(raw_payload, target_model=EnterpriseQueryResponse)

    guard_event = {
        "valid": guard_res["success"],
        "repaired": guard_res.get("repaired", False),
        "confidence_score": guard_res["data"]["confidence_score"] if guard_res["success"] else 0.0,
        "cited_doc_ids": guard_res["data"]["cited_doc_ids"] if guard_res["success"] else [],
        "attempts": guard_res.get("attempts", 1)
    }
    yield f"event: guardrail\ndata: {json.dumps(guard_event)}\n\n"

    # Step 4: Streaming Telemetry & Simulated Enterprise Pricing
    # Cost model: $0.0015/1k input tokens, $0.002/1k output tokens
    input_tokens_est = max(1, len(query.split()) + sum(len(d.get("content", "").split()) for d in docs))
    output_tokens_est = total_tokens
    simulated_cost = round((input_tokens_est * 0.0000015) + (output_tokens_est * 0.0000020), 6)
    throughput_tps = round(total_tokens / (total_duration_ms / 1000.0), 1) if total_duration_ms > 0 else 0.0

    telemetry_event = {
        "first_token_ms": first_token_ms,
        "total_duration_ms": total_duration_ms,
        "tokens_input": input_tokens_est,
        "tokens_output": output_tokens_est,
        "tokens_per_second": throughput_tps,
        "simulated_cost_usd": simulated_cost
    }
    yield f"event: telemetry\ndata: {json.dumps(telemetry_event)}\n\n"

    # Step 5: Termination Delimiter
    yield "event: done\ndata: [DONE]\n\n"

@app.post("/api/chat/stream")
async def chat_stream_post(req: ChatStreamRequest, request: Request):
    """
    Primary SSE streaming endpoint for AI chat clients and web cockpits.
    """
    return StreamingResponse(
        _sse_generator(request, query=req.query, top_k=req.top_k or 3),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/chat/stream")
async def chat_stream_get(
    request: Request,
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=3, ge=1, le=10)
):
    """
    Browser-native EventSource GET endpoint for SSE streaming.
    """
    return StreamingResponse(
        _sse_generator(request, query=query, top_k=top_k),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )

# ----------------- CONTINUOUS EVALUATION ENDPOINTS -----------------

@app.post("/api/evals/run", response_model=EvalResult)
def run_evaluation_sample(req: EvalSampleRequest):
    """
    Runs deterministic evaluation (Context Relevancy, Faithfulness, Schema Adherence)
    on a single sample.
    """
    context_chunks = req.context_chunks
    answer = req.answer

    if not context_chunks and req.auto_retrieve:
        docs = retriever.query(req.query, top_k=3)
        context_chunks = [d["content"] for d in docs]
        if not answer:
            answer = _synthesize_offline_response(req.query, docs)

    context_chunks = context_chunks or []
    answer = answer or ""

    return eval_harness.evaluate_sample(
        query=req.query,
        context_chunks=context_chunks,
        answer=answer,
        response_payload=req.payload
    )

@app.get("/api/evals/benchmark", response_model=BenchmarkReport)
def run_golden_benchmark():
    """
    Executes automated evaluation against the golden enterprise test suite.
    """
    return eval_harness.evaluate_benchmark(GOLDEN_EVAL_SET)
