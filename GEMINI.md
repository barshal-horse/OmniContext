# OmniContext — Agent Workspace & Architectural Instructions

> **Workspace Target**: `C:\Users\bhars\Desktop\anti gravity\FDE 10\OmniContext`  
> **Candidate**: Harshal Borse (IIIT Guwahati CSE '26 | `barshal-horse`)  
> **Role Context**: Forward Deployed Engineer (FDE) / Applied AI Systems Engineer  

---

## 1. Dual-Mode Agent Protocol (Mandatory)

Whenever an AI coding agent operates within this workspace, it MUST adhere strictly to the **FDE Dual-Capacity Protocol**:

1. **Principal Forward Deployed Engineer (Execution Mode)**:
   - Author production-grade, fail-closed, anti-slop code.
   - Enforce strict Pydantic v2 schemas for all inputs and outputs.
   - Zero-credential resilience: All systems must boot and pass tests offline using `backend/seed/` without requiring live external API keys.
   - 90%+ unit test coverage with automated assertions.
2. **Staff Systems Architect & Mentor (Teaching Mode)**:
   - Never dump code silently.
   - Before implementing any major component, output an architectural briefing explaining the physical intuition, mathematical foundation (RRF, Cosine, F1/Precision-Recall), failure modes at scale, and Whiteboard Interview defense questions.

---

## 2. The 4 Core Architectural Invariants

1. **Anthropic Model Context Protocol (MCP) Compliance**:
   All tools and enterprise data resources must be exposed via the standard Python MCP SDK (`mcp` library) supporting both `stdio` and `sse` transports.
2. **Hybrid Retrieval (Dense + BM25 + Reciprocal Rank Fusion)**:
   Never rely solely on dense embeddings. Combine dense vector search with sparse lexical BM25 matching, combined via Reciprocal Rank Fusion:
   $$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{k + r_m(d)} \quad (k=60)$$
3. **Deterministic Guardrails & Self-Healing Contracts**:
   Model outputs must be validated against Pydantic v2 models. If malformed, execute up to 2 automated self-correction reflection retries before failing closed.
4. **Code-Driven Evaluation (Evals First)**:
   Every feature must be verified against a golden benchmark (`tests/test_evals_golden_set.py`) measuring Context Relevancy, Faithfulness, and Schema Adherence.

---

## 3. Directory Layout & File Contracts

- `backend/app/main.py`: FastAPI server exposing REST and Server-Sent Events (SSE) endpoints.
- `backend/app/mcp_server.py`: Custom MCP Server exposing tools (`query_hybrid_context`, `verify_contract`).
- `backend/app/retrieval.py`: Hybrid search engine (in-memory / pgvector fallback + BM25 + RRF).
- `backend/app/guardrails.py`: Pydantic v2 validation contracts and reflection loop.
- `backend/app/evals.py`: Evaluation metrics scoring faithfulness, precision, and latency.
- `backend/seed/enterprise_knowledge.json`: Seed documents representing enterprise knowledge.
- `docs/fde-engagement/`: Engagement documentation (`01_PRD`, `02_ADR`, `03_RUNBOOK`, `04_MASTERCLASS`).
- `tests/`: Complete unit and integration test suite runnable offline via `pytest`.

---

## 4. Immediate Development Phases (For the Next Conversation)

When opening a new conversation in this directory:
1. **Phase 1**: Scaffold `requirements.txt` and core config in `backend/app/config.py`.
2. **Phase 2**: Implement `backend/app/retrieval.py` with pure Python in-memory BM25 + Dense vector cosine search + RRF (with zero required API keys).
3. **Phase 3**: Implement `backend/app/mcp_server.py` using official MCP Python SDK.
4. **Phase 4**: Implement `backend/app/guardrails.py` with Pydantic v2 contracts and self-healing retries.
5. **Phase 5**: Implement `backend/app/main.py` and test suite in `tests/`.
6. **Phase 6**: Package with `docker-compose.yml` and Next.js / Streamlit visual cockpit.
