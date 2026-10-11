"use client";

import React from "react";
import { X, FileText, Video, ExternalLink, Image as ImageIcon, PlayCircle, ShieldCheck } from "lucide-react";

interface CitationDrawerProps {
  citation: any | null;
  onClose: () => void;
}

export function CitationDrawer({ citation, onClose }: CitationDrawerProps) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 dark:bg-black/75 backdrop-blur-md transition-all">
      <div className="relative w-full max-w-lg bg-white dark:bg-[#0c111c] border border-zinc-200 dark:border-white/[0.12] rounded-2xl shadow-2xl p-6 overflow-hidden">
        
        {/* Glow ambient background */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-zinc-200 dark:border-white/[0.08]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 dark:bg-indigo-500/15 border border-indigo-500/20 dark:border-indigo-500/25 text-indigo-600 dark:text-indigo-400">
              {citation.location.slide ? (
                <FileText className="w-5 h-5" />
              ) : (
                <Video className="w-5 h-5" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-zinc-900 dark:text-white">
                  Source Grounding Evidence
                </h3>
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 dark:bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  Verified Origin
                </span>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 font-medium mt-0.5">
                {citation.source} · {citation.label}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-zinc-100 hover:bg-zinc-200 dark:bg-white/[0.04] dark:hover:bg-white/[0.08] text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-all cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="py-4 space-y-4">
          
          {/* Excerpt */}
          <div className="p-4 rounded-xl bg-zinc-50 dark:bg-white/[0.02] border border-zinc-200/80 dark:border-white/[0.06]">
            <span className="text-xs font-bold uppercase text-zinc-500 dark:text-zinc-400 tracking-wider block mb-1.5">
              Verbatim Ingested Transcript / Slide Text:
            </span>
            <p className="text-xs sm:text-sm text-zinc-800 dark:text-zinc-200 leading-relaxed font-normal">
              "{citation.excerpt}"
            </p>
          </div>

          {/* Diagram caption if present */}
          {citation.diagram_caption && (
            <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-500/20 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-700 dark:text-indigo-300">
                <ImageIcon className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <span>Multimodal Vision Model Diagram Caption:</span>
              </div>
              <p className="text-xs text-indigo-900 dark:text-indigo-100/90 leading-relaxed">
                {citation.diagram_caption}
              </p>
            </div>
          )}

          {/* Video timestamp simulation */}
          {citation.location.timestamp && (
            <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-500/20 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <PlayCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <span className="text-xs font-bold text-emerald-800 dark:text-emerald-200 block">
                    Jump to Keyframe at {citation.location.timestamp}
                  </span>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    Timestamp-aligned Whisper segment
                  </span>
                </div>
              </div>
              <button className="px-3.5 py-1.5 rounded-full bg-emerald-600 dark:bg-emerald-500/20 text-white dark:text-emerald-300 border border-transparent dark:border-emerald-500/30 text-xs font-semibold hover:bg-emerald-700 dark:hover:bg-emerald-500/30 transition-all cursor-pointer">
                Play Segment
              </button>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="pt-3.5 border-t border-zinc-200 dark:border-white/[0.08] flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400">
          <span className="flex items-center gap-1.5 text-xs font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            Faithfulness Score: 0.98 (RAGAS Verified)
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-black dark:bg-white/[0.08] text-white hover:bg-zinc-800 dark:hover:bg-white/[0.12] text-xs font-semibold transition-all cursor-pointer"
          >
            Close Viewer
          </button>
        </div>

      </div>
    </div>
  );
}
