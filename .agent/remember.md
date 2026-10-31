# OmniContext — Agent Memory & Active State Tracker

## Project Overview
- **Repository**: OmniContext (Enterprise Model Context Protocol Gateway & Evaluation Proxy)
- **Author**: Harshal Borse (IIIT Guwahati CSE '26 | `barshal-horse`)
- **Location**: `C:\Users\bhars\Desktop\anti gravity\FDE 10\OmniContext`
- **Objective**: Build a production-grade Forward Deployed Engineer (FDE) system showcasing:
  1. Official Anthropic Model Context Protocol (MCP) Server implementation.
  2. Hybrid Retrieval (Dense Vector + Sparse BM25 + Reciprocal Rank Fusion RRF).
  3. Deterministic Pydantic v2 Schema Guardrails with Self-Healing Retry Loops.
  4. Real-time Server-Sent Events (SSE) Streaming with in-flight guardrail gates & telemetry.
  5. Continuous Evaluation Benchmark Harness (Context Relevancy, Faithfulness, and Schema Adherence).
  6. Visual Operational Cockpit built with Next.js 14 App Router and Tailwind CSS.
  7. Zero-Credential Offline Mock Mode with realistic enterprise seed data and Docker Compose orchestration.

---

## Active Milestone Status

- [x] **Milestone 0: Workspace & Documentation Scaffolding**
  - Created `README.md` with system architecture diagram and benchmark table.
  - Created `GEMINI.md` with agent execution protocols and FDE standards.
  - Created `.agent/remember.md` for session persistence.
  - Generated complete `/docs/fde-engagement/` documentation suite.
- [x] **Milestone 1: Backend Core & Hybrid Retrieval Engine**
  - Implemented `backend/app/retrieval.py` with in-memory BM25 + Vector cosine similarity + RRF ($k=60$).
  - Populated `backend/seed/enterprise_knowledge.json`.
- [x] **Milestone 2: MCP Server, Guardrails, FastAPI SSE Streaming & Continuous Evals**
  - Implemented `backend/app/mcp_server.py` exposing standard MCP tools and resources.
  - Implemented `backend/app/guardrails.py` with Pydantic v2 `EnterpriseQueryResponse` contract and automated reflection repair loops.
  - Implemented `backend/app/evals.py` with deterministic Context Relevancy, Claim-Level Faithfulness, and Schema Adherence metrics.
  - Implemented `backend/app/main.py` with `/api/chat/stream` (SSE streaming POST and browser EventSource GET), W3C frame ordering (`metadata` -> `token` -> `guardrail` -> `telemetry` -> `done`), eager client disconnect detection (`request.is_disconnected()`), and simulated cost calculations.
  - Implemented `/api/evals/run` and `/api/evals/benchmark` endpoints.
  - Implemented `tests/test_streaming.py` and `tests/test_evals_golden_set.py`.
  - **Verification**: 29/29 tests passing in 3.05s (`100% pass rate`).
- [x] **Milestone 3: Human-Centered UX Overhaul, Visual Cockpit, Packaging & Systematic README**
  - Executed complete UX overhaul using `impeccable` craft-floor principles:
    - `AskAssistant.tsx`: Replaced generic cards with a 3-Step Transparent Answer Pipeline (Step 1: Verified Evidence Cards, Step 2: Live Grounded Answer with typewriter stream and copy button, Step 3: Safety & Quality Guarantee with Zero Hallucinations badge).
    - `ToolConnectors.tsx`: Replaced raw JSON editors with an intuitive "USB-C for AI" connector hub with friendly inputs and 1-click test runners.
    - `AccuracyBenchmark.tsx`: Replaced cryptic numbers with The 3 Quality Pillars (Document Relevance, Truthfulness, Format Compliance) and 100% passing golden benchmark scorecards.
    - Welcoming orientation banner so any user immediately understands what the product does.
  - Verified static compilation with zero errors via `npm run build` (`4/4 pages statically generated`).
  - Configured multi-service `docker-compose.yml` (`omni-gateway` on port 8000 and `omni-cockpit` on port 3000) with container health checks.
  - Rewrote `README.md` into an accessible, structured, beginner-friendly guide explaining all concepts without obscure jargon.
- [x] **Milestone 4: Push to GitHub & Vercel Deployment Ready**
  - Created public GitHub repository and pushed all source code to `https://github.com/barshal-horse/OmniContext`.
  - Added 1-Click Vercel Deploy button and zero-credential offline cloud resilience for portfolio visitors.

---

## Key Technical Decisions
1. **Zero External Dependency on First Boot**: The system passes 100% of tests and serves demo queries out-of-the-box using local mock embeddings and seed data, without requiring a paid OpenAI/Anthropic API key.
2. **RRF Constant $k=60$**: Proven enterprise standard (Cormack et al.) preventing rank-dominance from any single retriever.
3. **Pydantic v2 Schema Constraints**: Every endpoint output is validated against strict Pydantic v2 models before leaving the gateway.
4. **Eager Disconnect Handling**: `await request.is_disconnected()` in the token generator prevents "ghost generation" compute waste.
5. **Deterministic In-Process Evals**: Fast, reproducible evaluations without flaky, expensive LLM judges in CI/CD.
6. **Accessible Plain-English Explanations**: Concepts like RRF, MCP, SSE, and Evals are explained with physical-world analogies for early-graduate interview readiness.
