# OmniContext: Enterprise Model Context Protocol (MCP) Gateway & Evaluation Proxy

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![MCP](https://img.shields.io/badge/MCP-Standard_v1.0-purple.svg)](https://modelcontextprotocol.io/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.9-red.svg)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose_Ready-2496ED.svg)](https://www.docker.com/)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fbarshal-horse%2FOmniContext&root-directory=frontend&project-name=omnicontext)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> 💡 **What is OmniContext in Simple Words?**  
> Imagine an enterprise wants to connect AI assistants (like Claude or custom agents) to internal documents and databases. Normally, this requires messy custom code that breaks easily, hallucinated answers that invent fake information, and malformed outputs that crash databases.  
> **OmniContext is a reliable bridge (gateway)** between AI models and company data. It gives every tool a universal plug (**Anthropic MCP**), searches documents using both exact words and concepts (**Hybrid Search**), double-checks that answers follow strict rules (**Pydantic Guardrails**), streams answers like a typewriter (**Server-Sent Events**), and automatically tests accuracy on every single build (**Continuous Evals**).

---

## 1. The 3 Real-World Problems OmniContext Solves

When companies try to move AI from a small prototype to real production, they face three major hurdles:

### Problem 1: The "Different Plugs" Crisis (M Tools × N Models)
* **The Analogy**: Imagine if every device in your house (phone, laptop, headphones, kettle) used a different proprietary wall plug. You would need 20 adapters, and if a manufacturer changed their plug, everything would stop working.
* **The Reality**: In enterprises, connecting 10 internal tools (PostgreSQL, Jira, internal CRM, docs) to 5 different AI models (OpenAI, Claude, local models) usually requires writing 50 brittle custom prompt wrappers.
* **How OmniContext Solves It**: We implement the **Anthropic Model Context Protocol (MCP)**. MCP is like **USB-C for AI**: one universal standard that connects any AI client to any tool or database without rewriting code.

### Problem 2: "Dirty" Outputs Crashing Databases
* **The Analogy**: Imagine ordering food online, but the delivery app sends the chef's response wrapped in weird symbols or forgets to include your address. The restaurant cannot fulfill your order.
* **The Reality**: AI models often return malformed JSON, markdown backticks (` ```json `), or forget required fields like `tenant_id` or `confidence_score`. When sent to downstream microservices, the database crashes.
* **How OmniContext Solves It**: We enforce **Pydantic v2 Schema Guardrails**. If a model makes a mistake, our engine catches it, cleans it up, and runs an automated self-healing repair loop before sending clean, guaranteed type-safe data downstream.

### Problem 3: "Vibes-Based" Prompt Testing
* **The Analogy**: Imagine building an airplane engine, and instead of measuring temperature and pressure with scientific gauges, the engineer just says: *"Well, it feels like it sounds okay to me!"*
* **The Reality**: Most teams test AI prompts manually by asking 2 or 3 questions in a playground. A prompt change that improves one question often secretly breaks 10 other questions in production without anyone noticing.
* **How OmniContext Solves It**: We built a **Continuous Evaluation (CI/CD Evals) Benchmark**. On every build, our system runs automated mathematical tests measuring **Context Relevancy** (did we fetch the right documents?), **Faithfulness** (is the answer 100% grounded with zero hallucinations?), and **Schema Adherence** in milliseconds.

---

## 2. System Architecture

```
                             [ CLIENTS & AGENTS ]
                     (Claude Desktop, Cursor, Web Browsers)
                                      │
                                      ▼  HTTP / SSE
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OMNICONTEXT GATEWAY (FastAPI / Port 8000)                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Model Context Protocol (MCP) Interface                                   │
│    ├── Tools: query_hybrid_context, verify_schema_contract                  │
│    └── Resources: enterprise://docs/{id} (Seed Knowledge Base)              │
│                                                                             │
│ 2. Hybrid Retrieval Engine                                                  │
│    ├── BM25 Sparse Search (Finds exact error codes & technical terms)       │
│    ├── Dense Vector Search (Finds broad concepts & semantic meaning)        │
│    └── Reciprocal Rank Fusion (RRF, k=60) ──> Scale-invariant reordering   │
│                                                                             │
│ 3. Real-Time Server-Sent Events (SSE) Streaming                             │
│    ├── Event 1: 'metadata'   ──> Emits retrieved docs & RRF scores early    │
│    ├── Event 2: 'token'      ──> Streams typewriter chunks in real-time     │
│    ├── Event 3: 'guardrail'  ──> Validates & auto-repairs Pydantic schema   │
│    ├── Event 4: 'telemetry'  ──> Measures latency (TTFT) and dollar cost    │
│    └── Event 5: 'done'       ──> Clean [DONE] stream termination            │
│                                                                             │
│ 4. Continuous Evaluation (CI/CD Evals) Engine                               │
│    ├── Context Relevancy Metric (Are query keywords in retrieved docs?)     │
│    ├── Faithfulness Metric (Is every claim strictly backed by context?)     │
│    └── Schema Adherence Metric (Did the payload pass Pydantic validation?)  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Real-Time SSE Stream / REST
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               VISUAL OPERATIONAL COCKPIT (Next.js 14 / Port 3000)           │
│  - Live SSE Typewriter Stream with First-Token Latency (TTFT)               │
│  - MCP Protocol & Tool Schema Inspector                                     │
│  - Continuous Evals Benchmark Radar & 5-Scenario Golden Test Results        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Concepts Explained Simply

### A. Hybrid Search: BM25 + Dense Vectors + Reciprocal Rank Fusion (RRF)
* **Dense Vectors** convert text into lists of numbers (embeddings) to understand meaning. They are great at understanding that *"automobile"* and *"car"* mean the same thing. However, they struggle with exact technical strings (like `HTTP 429` vs `HTTP 401`).
* **BM25** is an exact keyword search based on word frequencies. It is great at finding exact error codes, user IDs, or specific function names, but it cannot understand synonyms.
* **Why Combine Them?** OmniContext uses both! We search using Dense Cosine Similarity and Sparse BM25 simultaneously, then merge the rankings using **Reciprocal Rank Fusion (RRF)**:

$$\text{RRF\_Score}(d) = \frac{1}{60 + r_{\text{dense}}(d)} + \frac{1}{60 + r_{\text{sparse}}(d)}$$

> **What does this formula mean?**  
> $r_{\text{dense}}(d)$ is the position of document $d$ in the dense search (e.g. rank 1, rank 2).  
> $r_{\text{sparse}}(d)$ is its position in the BM25 search.  
> The number $60$ is a smoothing constant. It ensures that an outlier result doesn't completely drown out documents that scored consistently well across both searches.

---

### B. Real-Time Server-Sent Events (SSE) Streaming
Instead of forcing a user or client service to wait in total silence for 3–5 seconds while an AI model writes a long paragraph, **SSE streams the answer word-by-word** like a typewriter:
* **First Token Speed (TTFT)**: Delivered in $< 200\,\text{ms}$.
* **Eager Disconnect Protection**: If a user navigates away or closes their browser tab mid-sentence, our backend checks `await request.is_disconnected()` and stops generating immediately, saving expensive cloud compute.

---

### C. Self-Healing Pydantic v2 Guardrails
When models output structured data, OmniContext validates it against an official Pydantic schema:

```python
class EnterpriseQueryResponse(BaseModel):
    query: str
    answer: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    cited_doc_ids: List[str]
    requires_human_approval: bool = False
```

If the model forgets `confidence_score` or puts markdown backticks (` ```json `) around the text, the guardrail engine strips the backticks, injects default safe values, and marks the payload as **Auto-Repaired**. If the output is completely corrupted, it **fails closed** with an HTTP 422 error instead of sending garbage into your database.

---

### D. Continuous Evals (Testing Without Expensive LLM Judges)
Instead of paying for a slow, expensive external model to grade every test during GitHub Actions or local builds, OmniContext uses **in-process mathematical scoring**:

1. **Context Relevancy ($\mathcal{R}$)**:
   $$\mathcal{R} = \frac{|\text{Query Keywords} \cap \text{Context Keywords}|}{|\text{Query Keywords}|}$$
   Measures whether the search engine retrieved documents that actually mention the core subject of the user's question.

2. **Faithfulness ($\mathcal{F}$)**:
   Breaks down the answer into individual sentence claims and verifies that at least 50% of the key words in every claim are supported by the retrieved text. If an answer mentions invented concepts (e.g. claiming OmniContext runs on *"Cassandra and quantum blockchains"* when the docs say *"PostgreSQL 16"*), the faithfulness score plummets to $0.0$.

3. **Schema Adherence ($\mathcal{S}$)**:
   $1.0$ if the payload passes Pydantic v2 validation cleanly, and $0.0$ if it fails.

---

## 4. Project Directory Structure

```
OmniContext/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI server (SSE streaming & endpoints)
│   │   ├── mcp_server.py        # Anthropic MCP Server (tools & resources)
│   │   ├── retrieval.py         # Hybrid Search (BM25 + Cosine + Cormack RRF)
│   │   ├── guardrails.py        # Pydantic v2 schema & self-healing loops
│   │   ├── evals.py             # Relevancy, Faithfulness & Schema metrics
│   │   └── config.py            # Pydantic settings & offline mock mode
│   └── seed/
│       └── enterprise_knowledge.json # Offline enterprise technical corpus
├── frontend/                    # Next.js 14 App Router UI Cockpit
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout with Inter font wiring
│   │   │   ├── globals.css      # Institutional dark theme tokens
│   │   │   └── page.tsx         # Tabbed main cockpit view
│   │   └── components/
│   │       ├── StreamCockpit.tsx    # Live SSE streaming & telemetry
│   │       ├── MCPExplorer.tsx      # Tool schema & resource browser
│   │       └── EvalsDashboard.tsx   # Continuous evaluation benchmark
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── tests/
│   ├── test_retrieval.py        # Tests for BM25, Cosine & RRF scoring
│   ├── test_guardrails.py       # Tests for Pydantic v2 self-healing
│   ├── test_mcp_server.py       # Tests for MCP tool dispatch
│   ├── test_streaming.py        # Tests for SSE events & disconnects
│   └── test_evals_golden_set.py # 25+ automated evaluation assertions
├── docs/fde-engagement/         # Palantir/Scale AI style engagement docs
│   ├── 01_DISCOVERY_AND_PRD.md  # Product Requirements Document
│   ├── 02_ADR_ARCHITECTURE.md   # Architectural Decision Records
│   ├── 03_RUNBOOK_AND_WARROOM.md# Operational incident playbook
│   └── 04_FDE_MASTERCLASS_GUIDE.md # Systems interview defense & flashcards
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile                   # Backend production container
└── requirements.txt             # Python dependencies
```

---

## 5. Quickstart Guide (Zero-Credential Ready)

OmniContext is completely self-contained. It includes a **Zero-Credential Offline Mock Mode** so you can run the entire system, pass all 29 automated tests, and try the UI without needing paid OpenAI or Anthropic API keys!

### Option A: Running with Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/barshal-horse/OmniContext.git
cd OmniContext

# 2. Spin up both the FastAPI Gateway and the Next.js Cockpit
docker compose up --build

# 3. Open your browser:
#    - Operational Cockpit: http://localhost:3000
#    - FastAPI Swagger Docs: http://localhost:8000/docs
#    - Health Check: http://localhost:8000/health
```

---

### Option B: Running Locally on Your Machine

#### 1. Start the Python Backend
```bash
# In the OmniContext root directory:
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Run the 29 automated unit and evaluation tests
pytest tests/ -v

# Start the FastAPI gateway on port 8000
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Start the Next.js Visual Cockpit
```bash
# Open a new terminal window:
cd OmniContext/frontend

# Install frontend packages
npm install

# Start the Next.js dev server on port 3000
npm run dev

# Visit http://localhost:3000 in your browser!
```

---

## 6. Key API Endpoints & Examples

### 1. Real-Time Chat Stream (Server-Sent Events)
```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "How does Token Bucket rate limiting work in Redis?", "top_k": 2}'
```
*Emits real-time event blocks: `metadata` $\to$ `token` $\to$ `guardrail` $\to$ `telemetry` $\to$ `done`.*

### 2. List Available MCP Tools
```bash
curl http://localhost:8000/mcp/tools
```
*Returns standard MCP JSON schemas for `query_hybrid_context` and `verify_schema_contract`.*

### 3. Run the Golden Continuous Evaluation Benchmark
```bash
curl http://localhost:8000/api/evals/benchmark
```
*Returns aggregated pass rates, average relevancy, faithfulness, and schema adherence across all golden enterprise scenarios.*

---

## 7. Whiteboard Interview Defense (Questions & Answers)

Here are real interview questions asked by staff engineers at Palantir, OpenAI, and Anthropic, explained in simple terms:

#### Q1: "Why use both BM25 and vector search? Isn't vector search modern and strictly better?"
> **Simple Answer**: No! Vector embeddings are great at broad concepts, but they suffer from the **"Semantic Generalization Trap"**. In vector space, `HTTP 429` (Rate Limited) is very close to `HTTP 401` (Unauthorized) because both are 3-digit HTTP status codes. If a user searches for `HTTP 429`, a vector-only search will often mistakenly return `HTTP 401`. BM25 is an exact keyword matcher that guarantees exact error codes and IDs are matched perfectly. Combining both with RRF ($k=60$) gives you the best of both worlds.

#### Q2: "Why choose Server-Sent Events (SSE) over WebSockets for AI chat?"
> **Simple Answer**: WebSockets are bidirectional (two-way) and require special connection upgrade protocols that are frequently blocked by corporate firewalls and cloud load balancers. In AI chat, the communication is almost entirely **one-way**: the user sends one question, and the server sends a stream of tokens back. SSE runs over standard HTTP (`text/event-stream`), traverses enterprise proxies seamlessly, and reconnects automatically without complex custom code.

#### Q3: "What happens if a model outputs invalid JSON even after self-healing retries?"
> **Simple Answer**: We **fail closed, never silently**. We do not use messy regex hacks to guess what the missing data was, because passing partially corrupted data into a production database causes silent database corruption. Instead, the gateway returns a clean `HTTP 422 Unprocessable Entity` error with the exact Pydantic validation trace, logs the bad prompt for debugging, and can safely route to a fallback model.

---

## Author & Engineering Standards
- **Lead Developer**: Harshal Borse ([`barshal-horse`](https://github.com/barshal-horse))
- **Education**: B.Tech in Computer Science & Engineering, IIIT Guwahati (Class of 2026)
- **Design Baseline**: Palantir & Scale AI Forward Deployed Engineer (FDE) Architecture (Fail-closed design, Zero-Credential Fallback, 100% Automated Test Gates).
