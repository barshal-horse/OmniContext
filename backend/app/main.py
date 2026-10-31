"""
OmniContext Gateway — Core FastAPI Application.
Exposes REST endpoints, MCP tool dispatchers, and health checks.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time

from backend.app.config import settings
from backend.app.mcp_server import OmniContextMCPServer
from backend.app.retrieval import HybridRetriever
from backend.app.guardrails import GuardrailEngine, EnterpriseQueryResponse

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

# Initialize MCP and retrieval subsystems
mcp_server = OmniContextMCPServer()
retriever = HybridRetriever(settings.seed_data_path)
guardrail_engine = GuardrailEngine()

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@app.get("/")
def read_root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "mcp_enabled": True,
        "offline_mode": settings.offline_mock_mode
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
    start = time.time()
    results = retriever.query(req.query, top_k=req.top_k or 3)
    elapsed_ms = round((time.time() - start) * 1000, 2)
    return {
        "query": req.query,
        "results": results,
        "count": len(results),
        "latency_ms": elapsed_ms
    }

@app.post("/api/validate-contract")
def validate_contract(payload: Dict[str, Any]):
    return guardrail_engine.validate_or_repair(payload, target_model=EnterpriseQueryResponse)
