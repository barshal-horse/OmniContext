# FDE Engagement 02: Architecture Decision Records (ADR)

**Project**: OmniContext (Enterprise Model Context Protocol Gateway & Evaluation Proxy)  
**Lead Engineer**: Harshal Borse (IIIT Guwahati CSE '26 | `barshal-horse`)  

---

## ADR 1: Adoption of Anthropic Model Context Protocol (MCP) as the Primary Interface

### Context
Enterprise clients demand that AI tools integrate with diverse platforms (Claude Desktop, Cursor, LangGraph agents, internal microservices). Writing proprietary REST endpoints for each tool creates an unsustainable integration matrix.

### Decision
Adopt the **Anthropic Model Context Protocol (MCP)** specification. The gateway exposes:
1. **Resources**: Static/dynamic data accessible via `uri://enterprise/docs/{id}`.
2. **Tools**: Executable functions (`query_hybrid_context`, `verify_schema_contract`).
3. **Transports**: Standard input/output (`stdio`) for local developer workflows and Server-Sent Events (`sse`) for network clients.

### Consequences
- **Positive**: Clients can add OmniContext to their `claude_desktop_config.json` or Cursor settings with zero code changes.
- **Trade-off**: Requires running an MCP server runtime alongside the FastAPI REST proxy.

---

## ADR 2: Hybrid Retrieval with Reciprocal Rank Fusion (RRF, $k=60$)

### Context
Dense vector embeddings excel at broad conceptual semantics ("how do I handle user sessions?") but fail on exact technical keywords, error codes, and specific identifiers ("HTTP 429", "tenant_id", "RFC-6749"). BM25 lexical search excels at exact keywords but fails on paraphrased natural language.

### Decision
Implement dual-retrieval combining Dense Cosine Similarity with BM25 Lexical scoring, combined via Reciprocal Rank Fusion (RRF):

$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{k + r_m(d)}$$

Where:
- $r_{\text{dense}}(d)$ is the 1-based rank of document $d$ in dense retrieval.
- $r_{\text{sparse}}(d)$ is the 1-based rank of document $d$ in sparse BM25 retrieval.
- $k = 60$ is the smoothing constant (standard established by Cormack, Clarke, and Buettcher) preventing outliers from dominating the ranking.

### Consequences
- **Positive**: Eliminates blind spots for both conceptual questions and exact error codes/identifiers.
- **Trade-off**: Requires maintaining both vector indices and inverted lexical indices.

---

## ADR 3: Deterministic Pydantic v2 Schema Guardrails with Self-Healing Loops

### Context
Direct LLM outputs frequently drop required fields, wrap JSON in markdown ticks, or invent unsupported enum values.

### Decision
Enforce strict Pydantic v2 schemas for all structured outputs. If validation fails:
1. Capture the exact Pydantic `ValidationError` trace.
2. Append the error message to the conversation history as an automated reflection prompt:
   *"Your previous output violated the schema with error: {error}. Please correct the JSON and return only valid data."*
3. Allow up to 2 self-healing retries before raising a deterministic domain exception.

### Consequences
- **Positive**: Downstream microservices receive guaranteed type-safe payloads ($0.0\%$ schema crashes).
- **Trade-off**: Malformed outputs incur latency for 1 additional LLM turn (mitigated by setting low temperature $\tau \le 0.1$).
