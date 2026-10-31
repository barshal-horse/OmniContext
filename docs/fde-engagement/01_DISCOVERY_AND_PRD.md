# FDE Engagement 01: Discovery & Product Requirements Document (PRD)

**Project**: OmniContext (Enterprise Model Context Protocol Gateway & Evaluation Proxy)  
**Lead Engineer**: Harshal Borse (IIIT Guwahati CSE '26 | `barshal-horse`)  
**Deployment Profile**: Forward Deployed AI Systems Engineer  

---

## 1. Enterprise Problem Statement

Enterprise clients (FinTech, Healthcare, Logistics, and Defense) are rushing to deploy generative AI assistants and multi-agent workflows. However, initial prototypes consistently fail when moving from proof-of-concept (POC) to production because of three fatal flaws:

1. **The M×N Integration Crisis**:
   Connecting $M$ proprietary tools (PostgreSQL, Jira, internal CRM, Confluence) to $N$ models (OpenAI, Anthropic, local Llama) creates brittle, custom prompt wrappers that collapse on API updates.
2. **Schema Drift & Downstream Crashes**:
   Non-deterministic LLM text generation frequently omits required fields, changes keys, or returns invalid JSON, causing crashes in production microservices.
3. **The "Vibes-Based" Deployment Blindspot**:
   Engineering teams alter prompts or change model providers based on subjective manual inspections. Without automated regression benchmarks, improvements in one area trigger catastrophic regressions in others.

---

## 2. Product Requirements & Objectives

### Functional Requirements (FR)
- **FR-1 (MCP Compliance)**: Expose internal enterprise data and verification actions via the official Model Context Protocol (MCP) using standard tools and resource URIs (`uri://enterprise/docs/{id}`).
- **FR-2 (Hybrid Context Retrieval)**: Combine dense semantic search with sparse lexical BM25 matching, aggregated via Reciprocal Rank Fusion (RRF, $k=60$), followed by cross-encoder re-ranking.
- **FR-3 (Deterministic Guardrails)**: Intercept model outputs and enforce strict Pydantic v2 schemas. If output validation fails, execute a self-correcting reflection loop (maximum 2 retries) before failing closed.
- **FR-4 (Continuous Evals Suite)**: Provide a golden test harness measuring Context Relevancy, Faithfulness, and Schema Compliance on every build.
- **FR-5 (Streaming Telemetry)**: Provide Server-Sent Events (SSE) streaming with async logging of tokens, latency, and simulated dollar cost.

### Non-Functional Requirements (NFR)
- **NFR-1 (Latency)**: First token delivered in $< 400\,\text{ms}$; cache hits delivered in $< 15\,\text{ms}$.
- **NFR-2 (Zero-Credential Resilience)**: The system must boot and pass 100% of unit tests offline without requiring external paid API keys.
- **NFR-3 (Reproducibility)**: Complete 1-click execution via `docker compose up --build`.

---

## 3. Success Metrics

| Goal | Target Metric |
| :--- | :--- |
| **Retrieval Accuracy** | $\ge 92\%$ Top-3 Precision on enterprise technical questions |
| **Schema Compliance** | $100\%$ zero-error JSON schema adherence on downstream payloads |
| **Test Coverage** | $\ge 90\%$ branch coverage across core gateway modules |
| **Offline Pass Rate** | $100\%$ passing tests in zero-credential mock mode |
