# FDE Engagement 03: Operational Runbook & Chaos Playbook

**Project**: OmniContext (Enterprise Model Context Protocol Gateway & Evaluation Proxy)  
**Lead Engineer**: Harshal Borse (IIIT Guwahati CSE '26 | `barshal-horse`)  

---

## 1. Local Development & Zero-Credential Boot

```bash
# 1. Clone & Enter
cd "C:\Users\bhars\Desktop\anti gravity\FDE 10\OmniContext"

# 2. Virtual Environment Setup
python -m venv venv
venv\Scripts\activate

# 3. Dependency Installation
pip install -r requirements.txt

# 4. Zero-Credential Offline Verification (All tests must pass without API keys)
pytest tests/ -v
```

---

## 2. Docker Compose Production Deployment

```bash
# Spin up full stack (PostgreSQL pgvector, FastAPI Gateway, MCP Server, Cockpit)
docker compose up --build -d

# Verify health check
curl http://localhost:8000/health
# Response: {"status": "ok", "service": "OmniContext", "mcp_active": true}
```

---

## 3. Chaos Playbook & Incident Triage

### Scenario A: External LLM API Outage (503 / Network Timeout)
* **Symptom**: External model providers (OpenAI / Anthropic) return HTTP 500/503 or fail to respond within $3,000\,\text{ms}$.
* **System Response**: Circuit breaker opens automatically after 3 consecutive failures.
* **Fallback Behavior**: Gateway diverts traffic to local fallback model (Ollama / deterministic Mock Provider) with an explicit header: `X-OmniContext-Fallback: true`.

### Scenario B: Schema Drift & Repeated Malformed Outputs
* **Symptom**: Model output fails Pydantic validation across all retry attempts.
* **System Response**: Gateway logs the full prompt and malformed JSON into the failure audit buffer, aborts execution cleanly, and returns a structured `HTTP 422 Unprocessable Entity` domain error with the exact Pydantic violation diff.
* **Resolution**: Inspect the failure audit log; update the prompt instructions or loosen optional schema fields.

### Scenario C: High-Concurrency Burst (1,000 RPS)
* **Symptom**: Concurrency spike causes connection starvation on the vector database.
* **System Response**: In-memory LRU semantic cache intercepts repeated queries in $< 15\,\text{ms}$, preventing 70%+ of read load from hitting the database or LLM endpoints.
