"use client";

import React from "react";
import { Sparkles, BookOpen, Video, FileText, Languages, ShieldCheck, Activity } from "lucide-react";

interface NavbarProps {
  hindiMode: boolean;
  setHindiMode: (val: boolean) => void;
  onOpenEvaluation: () => void;
  onRunDiagnostic: () => void;
}

export function Navbar({
  hindiMode,
  setHindiMode,
  onOpenEvaluation,
  onRunDiagnostic,
}: NavbarProps) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/[0.08] bg-[#06090e]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-indigo-400/30">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-lg text-white font-mono">SAARTHI</span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                Verified Grounded
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 hidden sm:block">
              Multimodal Adaptive Tutor · Track D
            </p>
          </div>
        </div>

        {/* Ingested Sources Status */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.06] text-xs text-zinc-300">
          <span className="text-[11px] text-zinc-400 font-medium">Workspace:</span>
          <span className="font-semibold text-white">Active Course Knowledge Base</span>
          <span className="text-zinc-600">|</span>
          <div className="flex items-center gap-1.5 text-zinc-400">
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            <span>Course Units</span>
          </div>
          <div className="flex items-center gap-1.5 text-zinc-400">
            <Video className="w-3.5 h-3.5 text-emerald-400" />
            <span>Multimodal</span>
          </div>
        </div>

        {/* Controls & Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          
          {/* Hindi Mode Toggle (Optional enhancement 2.20) */}
          <button
            onClick={() => setHindiMode(!hindiMode)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              hindiMode
                ? "bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-sm shadow-amber-500/20"
                : "bg-white/[0.04] text-zinc-400 border border-white/[0.08] hover:text-zinc-200"
            }`}
            title="Toggle Sarvam AI Hindi pedagogical explanations"
          >
            <Languages className="w-3.5 h-3.5" />
            <span>{hindiMode ? "🇮🇳 Hindi Mode (On)" : "Hindi Mode"}</span>
          </button>

          {/* Diagnostic Cold-Start Trigger */}
          <button
            onClick={onRunDiagnostic}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-white/[0.04] text-zinc-300 border border-white/[0.08] hover:bg-white/[0.08] hover:border-white/[0.15] transition-all"
          >
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Diagnostic</span>
          </button>

          {/* Benchmark / Evaluation Modal Trigger */}
          <button
            onClick={onOpenEvaluation}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-md shadow-indigo-500/25 hover:from-indigo-400 hover:to-indigo-500 transition-all cursor-pointer"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Ablation Bench</span>
          </button>

        </div>
      </div>
    </header>
  );
}
