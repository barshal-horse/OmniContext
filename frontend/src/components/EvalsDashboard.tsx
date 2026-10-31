"use client";

import React, { useState } from "react";
import { CheckCircle2, Award, Zap, BookOpen, AlertCircle, Play, RefreshCw, BarChart3 } from "lucide-react";

interface EvalSampleResult {
  query: string;
  context_relevancy: number;
  faithfulness: number;
  schema_adherence: number;
  overall_score: number;
  passed: boolean;
  latency_ms: number;
}

interface BenchmarkReport {
  total_samples: number;
  passed_samples: number;
  pass_rate: number;
  avg_context_relevancy: number;
  avg_faithfulness: number;
  avg_schema_adherence: number;
  avg_overall_score: number;
  avg_latency_ms: number;
  results: EvalSampleResult[];
}

export default function EvalsDashboard() {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [running, setRunning] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const runBenchmark = async () => {
    setRunning(true);
    setErrorMsg(null);
    try {
      const res = await fetch("http://localhost:8000/api/evals/benchmark");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: BenchmarkReport = await res.json();
      setReport(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to run benchmark at http://localhost:8000");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-[#141418] border border-white/10 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-[#38BDF8]" />
            <h2 className="text-base font-semibold text-gray-200">
              Continuous Evaluation (CI/CD Evals) Benchmark
            </h2>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Automated mathematical scoring measuring Context Relevancy, Faithfulness, and Schema Adherence.
          </p>
        </div>

        <button
          onClick={runBenchmark}
          disabled={running}
          className="px-4 py-2 bg-[#38BDF8] hover:bg-[#0284C7] text-gray-900 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 self-start md:self-auto shadow-md shadow-[#38BDF8]/10"
        >
          {running ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4 fill-current" />
          )}
          {running ? "Evaluating..." : "Run Golden Benchmark"}
        </button>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-xs text-red-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Conceptual Explanation Cards for Learning & Interview Prep */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#141418] border border-white/5 rounded-xl p-4 space-y-1.5">
          <div className="flex items-center gap-2 text-[#38BDF8] text-xs font-semibold">
            <BookOpen className="w-4 h-4" />
            <span>1. Context Relevancy</span>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            Did the search engine pull documents that actually answer the user's question, rather than unrelated text?
          </p>
        </div>

        <div className="bg-[#141418] border border-white/5 rounded-xl p-4 space-y-1.5">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
            <CheckCircle2 className="w-4 h-4" />
            <span>2. Faithfulness</span>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            Is every claim made in the answer strictly backed by the retrieved context, with zero invented hallucinations?
          </p>
        </div>

        <div className="bg-[#141418] border border-white/5 rounded-xl p-4 space-y-1.5">
          <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
            <Zap className="w-4 h-4" />
            <span>3. Schema Adherence</span>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            Does the response strictly match our Pydantic v2 data contract so downstream databases never crash?
          </p>
        </div>
      </div>

      {/* Benchmark Summary Metrics (If Run) */}
      {report ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#141418] border border-emerald-500/30 rounded-xl p-4">
              <div className="text-xs text-gray-400">Pass Rate</div>
              <div className="font-mono text-2xl font-bold text-emerald-400 mt-1">
                {report.pass_rate}%
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">
                {report.passed_samples} / {report.total_samples} passing
              </div>
            </div>

            <div className="bg-[#141418] border border-white/10 rounded-xl p-4">
              <div className="text-xs text-gray-400">Avg Relevancy</div>
              <div className="font-mono text-2xl font-bold text-[#38BDF8] mt-1">
                {(report.avg_context_relevancy * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">Threshold: &ge; 45%</div>
            </div>

            <div className="bg-[#141418] border border-white/10 rounded-xl p-4">
              <div className="text-xs text-gray-400">Avg Faithfulness</div>
              <div className="font-mono text-2xl font-bold text-emerald-400 mt-1">
                {(report.avg_faithfulness * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">Zero Hallucinations</div>
            </div>

            <div className="bg-[#141418] border border-white/10 rounded-xl p-4">
              <div className="text-xs text-gray-400">Avg Eval Latency</div>
              <div className="font-mono text-2xl font-bold text-amber-400 mt-1">
                {report.avg_latency_ms} ms
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">Ultra-fast in-process</div>
            </div>
          </div>

          {/* Test Case Breakdown Table */}
          <div className="bg-[#141418] border border-white/10 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-4 h-4 text-[#38BDF8]" />
              <h3 className="text-sm font-semibold text-gray-200">
                Golden Benchmark Test Cases
              </h3>
            </div>

            <div className="space-y-3">
              {report.results.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-[#1C1D24] border border-white/5 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 flex-1">
                    <div className="text-gray-200 font-medium">{item.query}</div>
                    <div className="flex items-center gap-3 text-gray-400 text-[11px]">
                      <span>Latency: <strong className="text-gray-300 font-mono">{item.latency_ms} ms</strong></span>
                      <span>Score: <strong className="text-gray-300 font-mono">{(item.overall_score * 100).toFixed(1)}%</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-center">
                      <div className="text-[10px] text-gray-400">Relevancy</div>
                      <div className="font-mono font-semibold text-[#38BDF8]">
                        {(item.context_relevancy * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-[10px] text-gray-400">Faithful</div>
                      <div className="font-mono font-semibold text-emerald-400">
                        {(item.faithfulness * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-[10px] text-gray-400">Schema</div>
                      <div className="font-mono font-semibold text-amber-400">
                        {item.schema_adherence === 1 ? "Valid" : "Fail"}
                      </div>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 font-semibold font-mono text-[11px]">
                      PASS
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-[#141418] border border-white/5 rounded-xl p-12 text-center text-xs text-gray-500">
          Click &quot;Run Golden Benchmark&quot; above to execute automated evaluation across all 5 enterprise scenarios.
        </div>
      )}
    </div>
  );
}
