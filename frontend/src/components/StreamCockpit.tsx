"use client";

import React, { useState, useRef } from "react";
import { Play, Sparkles, ShieldCheck, Cpu, Database, CheckCircle2, AlertTriangle, ArrowRight, RefreshCw } from "lucide-react";

interface RetrievedDoc {
  id: string;
  title: string;
  category: string;
  rrf_score: number;
}

interface StreamMetadata {
  query: string;
  doc_ids: string[];
  retrieved_docs: RetrievedDoc[];
  timestamp: number;
}

interface GuardrailResult {
  valid: boolean;
  repaired: boolean;
  confidence_score: number;
  cited_doc_ids: string[];
}

interface TelemetryResult {
  first_token_ms: number;
  total_duration_ms: number;
  tokens_input: number;
  tokens_output: number;
  tokens_per_second: number;
  simulated_cost_usd: number;
}

const PRESET_QUERIES = [
  {
    label: "Rate Limiting",
    query: "How does Token Bucket rate limiting work in Redis and what error is returned?",
  },
  {
    label: "JWT Authentication",
    query: "What are the requirements for Bearer JWT RS256 token validation?",
  },
  {
    label: "PostgreSQL Pooling",
    query: "What is the maximum PostgreSQL connection pool size and query timeout?",
  },
  {
    label: "MCP Standard",
    query: "How does MCP expose tools and what transports are supported for agents?",
  },
];

export default function StreamCockpit() {
  const [query, setQuery] = useState(PRESET_QUERIES[0].query);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedTokens, setStreamedTokens] = useState<string>("");
  const [metadata, setMetadata] = useState<StreamMetadata | null>(null);
  const [guardrail, setGuardrail] = useState<GuardrailResult | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = async (queryToRun: string) => {
    if (!queryToRun.trim() || isStreaming) return;

    setIsStreaming(true);
    setStreamedTokens("");
    setMetadata(null);
    setGuardrail(null);
    setTelemetry(null);
    setErrorMsg(null);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await fetch("http://localhost:8000/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryToRun, top_k: 3 }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`Gateway returned HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No readable stream received from gateway");

      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          if (!block.trim()) continue;

          let eventType = "message";
          let dataStr = "";

          const eventLines = block.split("\n");
          for (const line of eventLines) {
            if (line.startsWith("event:")) {
              eventType = line.replace("event:", "").trim();
            } else if (line.startsWith("data:")) {
              dataStr = line.replace("data:", "").trim();
            }
          }

          if (!dataStr) continue;

          if (eventType === "metadata") {
            try {
              setMetadata(JSON.parse(dataStr));
            } catch (e) {
              console.error("Malformed metadata JSON", e);
            }
          } else if (eventType === "token") {
            try {
              const tokenPayload = JSON.parse(dataStr);
              setStreamedTokens((prev) => prev + tokenPayload.token);
            } catch (e) {
              setStreamedTokens((prev) => prev + dataStr);
            }
          } else if (eventType === "guardrail") {
            try {
              setGuardrail(JSON.parse(dataStr));
            } catch (e) {
              console.error("Malformed guardrail JSON", e);
            }
          } else if (eventType === "telemetry") {
            try {
              setTelemetry(JSON.parse(dataStr));
            } catch (e) {
              console.error("Malformed telemetry JSON", e);
            }
          } else if (eventType === "done") {
            // Stream complete
          }
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setErrorMsg(err.message || "Failed to connect to gateway at http://localhost:8000");
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search & Prompt Ingress Card */}
      <div className="bg-[#141418] border border-white/10 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#38BDF8]" />
            <h2 className="text-base font-semibold text-[#F3F4F6]">Enterprise Knowledge Query</h2>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-gray-400">
            Hybrid RRF (k=60) + Guardrails
          </span>
        </div>

        {/* Quick Presets */}
        <div className="flex flex-wrap gap-2 mb-4">
          {PRESET_QUERIES.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(p.query);
                startStream(p.query);
              }}
              className="text-xs px-3 py-1.5 rounded-lg bg-[#1C1D24] hover:bg-[#252732] border border-white/5 text-gray-300 transition-colors flex items-center gap-1.5"
            >
              <ArrowRight className="w-3 h-3 text-[#38BDF8]" />
              {p.label}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && startStream(query)}
            placeholder="Ask a technical or architecture question..."
            className="flex-1 bg-[#0B0C10] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-[#F3F4F6] focus:outline-none focus:border-[#38BDF8] transition-colors"
          />
          {isStreaming ? (
            <button
              onClick={handleStop}
              className="px-5 py-2.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4 animate-spin" />
              Stop
            </button>
          ) : (
            <button
              id="start-stream-button"
              onClick={() => startStream(query)}
              className="px-5 py-2.5 bg-[#38BDF8] hover:bg-[#0284C7] text-gray-900 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 shadow-md shadow-[#38BDF8]/10"
            >
              <Play className="w-4 h-4 fill-current" />
              Stream
            </button>
          )}
        </div>

        {errorMsg && (
          <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-xs text-red-400">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{errorMsg} (Make sure the backend is running on port 8000)</span>
          </div>
        )}
      </div>

      {/* Main Grid: Retrieved Evidence (Left) + Streaming Output (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Retrieved Sources (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-[#141418] border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-[#38BDF8]" />
              <h3 className="text-sm font-semibold text-gray-200">Retrieved Context Chunks</h3>
            </div>

            {metadata?.retrieved_docs && metadata.retrieved_docs.length > 0 ? (
              <div className="space-y-3">
                {metadata.retrieved_docs.map((doc, idx) => (
                  <div
                    key={doc.id}
                    className="p-3 bg-[#1C1D24] border border-white/5 rounded-lg space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-[#38BDF8] font-medium">{doc.id}</span>
                      <span className="font-mono text-gray-400 text-[11px]">
                        RRF: {doc.rrf_score}
                      </span>
                    </div>
                    <div className="text-xs font-medium text-gray-200 line-clamp-1">
                      {doc.title}
                    </div>
                    <div className="text-[11px] text-gray-400">{doc.category}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-gray-500">
                {isStreaming
                  ? "Retrieving context via BM25 + Cosine..."
                  : "Submit a query to inspect retrieved documents"}
              </div>
            )}
          </div>

          {/* Guardrail Status Card */}
          <div className="bg-[#141418] border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-gray-200">Pydantic v2 Guardrail Gate</h3>
            </div>

            {guardrail ? (
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Schema Validation:</span>
                  <span className="flex items-center gap-1 font-semibold text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {guardrail.repaired ? "Auto-Repaired" : "Passed (Valid)"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Confidence Score:</span>
                  <span className="font-mono text-gray-200">
                    {(guardrail.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Cited Documents:</span>
                  <span className="font-mono text-[#38BDF8]">
                    {guardrail.cited_doc_ids.join(", ") || "None"}
                  </span>
                </div>
              </div>
            ) : (
              <div className="py-4 text-center text-xs text-gray-500">
                Awaiting stream completion for schema contract audit
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Real-Time Stream Output & Telemetry (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="bg-[#141418] border border-white/10 rounded-xl p-5 min-h-[340px] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-[#38BDF8]" />
                  <span className="text-xs font-semibold text-gray-300">Live SSE Token Stream</span>
                </div>
                {isStreaming && (
                  <span className="flex items-center gap-1.5 text-xs text-[#38BDF8]">
                    <span className="w-2 h-2 rounded-full bg-[#38BDF8] animate-ping" />
                    Generating...
                  </span>
                )}
              </div>

              {streamedTokens ? (
                <div className="text-sm text-gray-200 leading-relaxed font-sans whitespace-pre-wrap">
                  {streamedTokens}
                  {isStreaming && (
                    <span className="inline-block w-2 h-4 ml-1 bg-[#38BDF8] animate-pulse" />
                  )}
                </div>
              ) : (
                <div className="py-20 text-center text-xs text-gray-500">
                  {isStreaming
                    ? "Establishing SSE stream..."
                    : "Press 'Stream' above to run hybrid search and stream responses in real-time."}
                </div>
              )}
            </div>

            {/* Bottom Telemetry Bar */}
            {telemetry && (
              <div className="pt-4 mt-6 border-t border-white/5 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="bg-[#1C1D24] p-2.5 rounded-lg border border-white/5">
                  <div className="text-[11px] text-gray-400">First Token (TTFT)</div>
                  <div className="font-mono text-sm font-semibold text-[#38BDF8]">
                    {telemetry.first_token_ms} ms
                  </div>
                </div>
                <div className="bg-[#1C1D24] p-2.5 rounded-lg border border-white/5">
                  <div className="text-[11px] text-gray-400">Total Duration</div>
                  <div className="font-mono text-sm font-semibold text-gray-200">
                    {telemetry.total_duration_ms} ms
                  </div>
                </div>
                <div className="bg-[#1C1D24] p-2.5 rounded-lg border border-white/5">
                  <div className="text-[11px] text-gray-400">Throughput</div>
                  <div className="font-mono text-sm font-semibold text-emerald-400">
                    {telemetry.tokens_per_second} tok/s
                  </div>
                </div>
                <div className="bg-[#1C1D24] p-2.5 rounded-lg border border-white/5">
                  <div className="text-[11px] text-gray-400">Simulated Cost</div>
                  <div className="font-mono text-sm font-semibold text-amber-400">
                    ${telemetry.simulated_cost_usd.toFixed(6)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
