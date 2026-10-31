# OmniContext — Agent Memory & Active State Tracker

## Project Overview
- **Repository**: OmniContext (Enterprise Model Context Protocol Gateway & Evaluation Proxy)
- **Author**: Harshal Borse (IIIT Guwahati CSE '26 | `barshal-horse`)
- **Location**: `C:\Users\bhars\Desktop\anti gravity\FDE 10\OmniContext`
- **Objective**: Build a production-grade Forward Deployed Engineer (FDE) system showcasing:
  1. Official Anthropic Model Context Protocol (MCP) Server implementation.
  2. Hybrid Retrieval (Dense Vector + Sparse BM25 + Reciprocal Rank Fusion RRF).
  3. Deterministic Pydantic v2 Schema Guardrails with Self-Healing Retry Loops.
  4. Automated Continuous Evaluation Benchmark (Golden Test Set measuring Faithfulness & Schema Compliance).
  5. Zero-Credential Offline Mock Mode with realistic enterprise seed data.

---

## Active Milestone Status

- [x] **Milestone 0: Workspace & Documentation Scaffolding**
  - Created `README.md` with system architecture diagram and benchmark table.
  - Created `GEMINI.md` with agent execution protocols and FDE standards.
  - Created `.agent/remember.md` for session persistence.
  - Generated complete `/docs/fde-engagement/` documentation suite.
- [ ] **Milestone 1: Backend Core & Hybrid Retrieval Engine**
  - Implement `backend/app/retrieval.py` with in-memory BM25 + Vector cosine similarity + RRF ($k=60$).
  - Populate `backend/seed/enterprise_knowledge.json`.
- [ ] **Milestone 2: MCP Server & Guardrails Engine**
  - Implement `backend/app/mcp_server.py` with standard MCP tools and resources.
  - Implement `backend/app/guardrails.py` with Pydantic v2 contracts and retry handlers.
- [ ] **Milestone 3: FastAPI Gateway & SSE Streaming**
  - Implement `backend/app/main.py` exposing REST and SSE token streaming.
- [ ] **Milestone 4: Continuous Evals Suite & Dockerization**
  - Build `tests/test_evals_golden_set.py` with 25+ automated assertions.
  - Package via `docker-compose.yml`.

---

## Key Technical Decisions
1. **Zero External Dependency on First Boot**: The system must pass all tests and serve demo queries out-of-the-box using local mock embeddings and seed data, without requiring a paid OpenAI/Anthropic API key.
2. **RRF Constant $k=60$**: Proven enterprise standard (Cormack et al.) preventing rank-dominance from any single retriever.
3. **Pydantic v2 Schema Constraints**: Every endpoint output is validated against strict Pydantic v2 models before leaving the gateway.
