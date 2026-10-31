"use client";

import React, { useState } from "react";
import { MessageSquare, Terminal, Award, Layers, CheckCircle2, Shield } from "lucide-react";
import AskAssistant from "@/components/AskAssistant";
import ToolConnectors from "@/components/ToolConnectors";
import AccuracyBenchmark from "@/components/AccuracyBenchmark";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"ask" | "tools" | "accuracy">("ask");

  return (
    <div className="min-h-screen bg-[#0B0E14] text-[#F3F4F6] flex flex-col justify-between selection:bg-[#38BDF8]/20 selection:text-[#38BDF8]">
      {/* Top Navigation Bar */}
      <header className="border-b border-white/10 bg-[#0E121B]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Logo & Identity */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#38BDF8]/20 to-[#0284C7]/20 border border-[#38BDF8]/30 flex items-center justify-center text-[#38BDF8] shadow-md shadow-[#38BDF8]/10">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-tight">OmniContext</h1>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-medium border border-emerald-500/20 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Live Gateway
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#38BDF8]/10 text-[#38BDF8] font-medium border border-[#38BDF8]/20">
                  Anthropic MCP
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Company AI Knowledge Hub &amp; Tool Gateway
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex bg-[#141822] p-1 rounded-xl border border-white/10 self-start md:self-auto shadow-inner">
            <button
              onClick={() => setActiveTab("ask")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "ask"
                  ? "bg-[#38BDF8] text-gray-950 shadow-md shadow-[#38BDF8]/20"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Ask Company Brain</span>
            </button>
            <button
              onClick={() => setActiveTab("tools")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "tools"
                  ? "bg-[#38BDF8] text-gray-950 shadow-md shadow-[#38BDF8]/20"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>Tool Connectors (MCP)</span>
            </button>
            <button
              onClick={() => setActiveTab("accuracy")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "accuracy"
                  ? "bg-[#38BDF8] text-gray-950 shadow-md shadow-[#38BDF8]/20"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <Award className="w-4 h-4" />
              <span>Accuracy Benchmark</span>
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Body */}
      <main className="max-w-7xl mx-auto px-4 md:px-8 py-8 flex-1 w-full">
        {activeTab === "ask" && <AskAssistant />}
        {activeTab === "tools" && <ToolConnectors />}
        {activeTab === "accuracy" && <AccuracyBenchmark />}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-[#0E121B] py-6">
        <div className="max-w-7xl mx-auto px-4 md:px-8 flex flex-col md:flex-row items-center justify-between text-xs text-gray-500 gap-3">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 font-medium">Harshal Borse</span>
            <span>&bull;</span>
            <span>IIIT Guwahati CSE &apos;26 (`barshal-horse`)</span>
            <span>&bull;</span>
            <span>Forward Deployed Engineer (FDE) Portfolio</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-gray-400 font-mono">
            <span>Hybrid Search (RRF k=60)</span>
            <span>Pydantic v2 Contracts</span>
            <span>Real-Time SSE Stream</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
