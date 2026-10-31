"use client";

import React, { useState, useEffect } from "react";
import { Terminal, Box, FileText, CheckCircle, Play, RefreshCw, AlertCircle } from "lucide-react";

interface MCPTool {
  name: string;
  description: string;
  inputSchema: any;
}

interface MCPResource {
  uri: string;
  name: string;
  mimeType: string;
  description: string;
}

export default function MCPExplorer() {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [resources, setResources] = useState<MCPResource[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"tools" | "resources">("tools");
  const [selectedTool, setSelectedTool] = useState<string>("query_hybrid_context");
  const [toolArgs, setToolArgs] = useState<string>(
    JSON.stringify({ query: "JWT token expiration", top_k: 2 }, null, 2)
  );
  const [toolResult, setToolResult] = useState<any>(null);
  const [executing, setExecuting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchMCPData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const [toolsRes, resRes] = await Promise.all([
        fetch("http://localhost:8000/mcp/tools"),
        fetch("http://localhost:8000/mcp/resources"),
      ]);

      if (toolsRes.ok) {
        const toolsData = await toolsRes.json();
        setTools(toolsData.tools || []);
      }
      if (resRes.ok) {
        const resData = await resRes.json();
        setResources(resData.resources || []);
      }
    } catch (e: any) {
      setErrorMsg("Failed to reach MCP Gateway at http://localhost:8000");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMCPData();
  }, []);

  const executeTool = async () => {
    setExecuting(true);
    setToolResult(null);
    setErrorMsg(null);
    try {
      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(toolArgs);
      } catch {
        throw new Error("Invalid JSON arguments");
      }

      const res = await fetch("http://localhost:8000/mcp/call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool_name: selectedTool,
          arguments: parsedArgs,
        }),
      });

      const data = await res.json();
      setToolResult(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Execution error");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-[#141418] border border-white/10 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-[#38BDF8]" />
            <h2 className="text-base font-semibold text-gray-200">
              Anthropic Model Context Protocol (MCP) Explorer
            </h2>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Universal standard connecting AI clients to internal tools & enterprise document resources.
          </p>
        </div>

        <button
          onClick={fetchMCPData}
          disabled={loading}
          className="text-xs px-3.5 py-2 rounded-lg bg-[#1C1D24] hover:bg-[#252732] border border-white/10 text-gray-300 transition-colors flex items-center gap-2 self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Registry
        </button>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-xs text-red-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Tabs Switcher */}
      <div className="flex border-b border-white/10 gap-6 text-sm">
        <button
          onClick={() => setActiveTab("tools")}
          className={`pb-3 font-medium transition-colors flex items-center gap-2 ${
            activeTab === "tools"
              ? "border-b-2 border-[#38BDF8] text-[#38BDF8]"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          <Box className="w-4 h-4" />
          Exposed Tools ({tools.length})
        </button>
        <button
          onClick={() => setActiveTab("resources")}
          className={`pb-3 font-medium transition-colors flex items-center gap-2 ${
            activeTab === "resources"
              ? "border-b-2 border-[#38BDF8] text-[#38BDF8]"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          <FileText className="w-4 h-4" />
          Enterprise Resources ({resources.length})
        </button>
      </div>

      {activeTab === "tools" ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Tool Definitions (5 cols) */}
          <div className="lg:col-span-5 space-y-3">
            {tools.map((t) => (
              <div
                key={t.name}
                onClick={() => {
                  setSelectedTool(t.name);
                  if (t.name === "query_hybrid_context") {
                    setToolArgs(JSON.stringify({ query: "JWT token expiration", top_k: 2 }, null, 2));
                  } else {
                    setToolArgs(
                      JSON.stringify(
                        {
                          payload: {
                            query: "What is the token expiration?",
                            answer: "Tokens expire in 3600 seconds.",
                            confidence_score: 0.95,
                          },
                        },
                        null,
                        2
                      )
                    );
                  }
                }}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  selectedTool === t.name
                    ? "bg-[#1C1D24] border-[#38BDF8]/40 shadow-sm"
                    : "bg-[#141418] border-white/5 hover:border-white/15"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-sm text-[#38BDF8] font-semibold">{t.name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-gray-400 font-mono">
                    MCP Tool
                  </span>
                </div>
                <p className="text-xs text-gray-300 leading-relaxed">{t.description}</p>
              </div>
            ))}
          </div>

          {/* Interactive Tool Runner (7 cols) */}
          <div className="lg:col-span-7 bg-[#141418] border border-white/10 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-200">
                Execute Tool: <span className="font-mono text-[#38BDF8]">{selectedTool}</span>
              </span>
              <button
                onClick={executeTool}
                disabled={executing}
                className="px-4 py-1.5 bg-[#38BDF8] hover:bg-[#0284C7] text-gray-900 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                {executing ? "Calling..." : "Execute"}
              </button>
            </div>

            <div>
              <label className="text-[11px] text-gray-400 font-medium block mb-1">
                JSON Arguments
              </label>
              <textarea
                value={toolArgs}
                onChange={(e) => setToolArgs(e.target.value)}
                rows={5}
                className="w-full bg-[#0B0C10] border border-white/10 rounded-lg p-3 font-mono text-xs text-gray-300 focus:outline-none focus:border-[#38BDF8]"
              />
            </div>

            {toolResult && (
              <div>
                <label className="text-[11px] text-gray-400 font-medium block mb-1">
                  MCP Tool Output
                </label>
                <pre className="p-3 bg-[#0B0C10] border border-white/5 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto max-h-64">
                  {JSON.stringify(toolResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Resources List */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {resources.map((r) => (
            <div
              key={r.uri}
              className="p-4 bg-[#141418] border border-white/10 rounded-xl space-y-2"
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-[#38BDF8] font-medium">{r.uri}</span>
                <span className="text-[10px] text-gray-400 bg-white/5 px-2 py-0.5 rounded">
                  {r.mimeType}
                </span>
              </div>
              <div className="text-sm font-medium text-gray-200">{r.name}</div>
              <div className="text-xs text-gray-400">{r.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
