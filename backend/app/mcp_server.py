"""
Official Anthropic Model Context Protocol (MCP) Server for OmniContext.
Exposes enterprise knowledge and validation tools over standard stdio / SSE transport.
"""

from typing import List, Dict, Any
from backend.app.retrieval import HybridRetriever
from backend.app.guardrails import GuardrailEngine, EnterpriseQueryResponse
from backend.app.config import settings

class OmniContextMCPServer:
    def __init__(self, seed_path: str = None):
        path = seed_path or settings.seed_data_path
        self.retriever = HybridRetriever(path)
        self.guardrails = GuardrailEngine()

    def get_server_metadata(self) -> Dict[str, Any]:
        """Returns standard MCP server capabilities and metadata."""
        return {
            "name": "OmniContext-Gateway",
            "version": settings.app_version,
            "capabilities": {
                "resources": True,
                "tools": True,
                "prompts": False
            }
        }

    def list_resources(self) -> List[Dict[str, Any]]:
        """Lists available enterprise resources with standard MCP URI schemes."""
        resources = []
        for doc in self.retriever.documents:
            resources.append({
                "uri": f"enterprise://docs/{doc.get('id')}",
                "name": doc.get("title"),
                "mimeType": "application/json",
                "description": f"Category: {doc.get('category')} | Tags: {', '.join(doc.get('tags', []))}"
            })
        return resources

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Reads a specific enterprise document by URI."""
        doc_id = uri.replace("enterprise://docs/", "").strip()
        for doc in self.retriever.documents:
            if doc.get("id") == doc_id:
                return {
                    "uri": uri,
                    "mimeType": "application/json",
                    "content": doc
                }
        raise ValueError(f"Resource with URI {uri} not found in enterprise corpus.")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Exposes standard MCP tools with strict JSON schema definitions."""
        return [
            {
                "name": "query_hybrid_context",
                "description": "Performs high-precision hybrid retrieval (Dense + BM25 + RRF) across enterprise docs.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query or technical problem"},
                        "top_k": {"type": "integer", "default": 3, "description": "Number of top results to return"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "verify_schema_contract",
                "description": "Validates a raw agent response payload against strict Pydantic v2 data contracts.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "payload": {"type": "object", "description": "JSON payload to validate"}
                    },
                    "required": ["payload"]
                }
            }
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a declared MCP tool with error boundaries."""
        if name == "query_hybrid_context":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 3)
            results = self.retriever.query(query, top_k=top_k)
            return {"results": results, "count": len(results)}

        elif name == "verify_schema_contract":
            payload = arguments.get("payload", {})
            val_res = self.guardrails.validate_or_repair(payload, target_model=EnterpriseQueryResponse)
            return val_res

        else:
            raise ValueError(f"Unknown MCP tool: {name}")
