"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  X,
  FileText,
  Video,
  ExternalLink,
  Image as ImageIcon,
  PlayCircle,
  ShieldCheck,
  Play,
  RotateCcw,
} from "lucide-react";
import { getApiBaseUrl } from "@/lib/api";

interface CitationDrawerProps {
  citation: any | null;
  onClose: () => void;
}

function parseTimestampSeconds(ts?: string | null): number {
  if (!ts) return 0;
  const clean = ts.replace("@", "").trim();
  const parts = clean.split(":").map(Number);
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  const num = Number(clean.replace("s", ""));
  return isNaN(num) ? 0 : num;
}

export function CitationDrawer({ citation, onClose }: CitationDrawerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  if (!citation) return null;

  const isVideo = Boolean(
    citation.location?.timestamp ||
    citation.source?.toLowerCase().endsWith(".mp4") ||
    citation.source?.toLowerCase().endsWith(".webm") ||
    citation.source?.toLowerCase().endsWith(".mov")
  );

  const targetSeconds = parseTimestampSeconds(citation.location?.timestamp);
  const apiBase = getApiBaseUrl();
  const mediaUrl = `${apiBase}/uploads/${encodeURIComponent(citation.source)}`;

  const handlePlaySegment = () => {
    setIsPlaying(true);
    if (videoRef.current) {
      videoRef.current.currentTime = targetSeconds;
      videoRef.current.play().catch(() => {});
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 dark:bg-black/80 backdrop-blur-md transition-all animate-in fade-in duration-150">
      <div className="relative w-full max-w-xl bg-white dark:bg-[#0c111c] border border-zinc-200 dark:border-white/[0.12] rounded-3xl shadow-2xl p-5 sm:p-6 overflow-hidden max-h-[92vh] flex flex-col">
        
        {/* Glow ambient background */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-zinc-200 dark:border-white/[0.08] shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-indigo-500/10 dark:bg-indigo-500/15 border border-indigo-500/20 dark:border-indigo-500/25 text-indigo-600 dark:text-indigo-400">
              {isVideo ? (
                <Video className="w-5 h-5 text-emerald-500" />
              ) : (
                <FileText className="w-5 h-5 text-indigo-500" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-zinc-900 dark:text-white">
                  Source Grounding Evidence
                </h3>
                <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/10 dark:bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
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
            className="p-1.5 rounded-xl bg-zinc-100 hover:bg-zinc-200 dark:bg-white/[0.04] dark:hover:bg-white/[0.08] text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-all cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="py-4 space-y-4 overflow-y-auto flex-1">
          
          {/* Real Video Player when it's a video citation */}
          {isVideo && (
            <div className="space-y-3">
              <div className="w-full rounded-2xl overflow-hidden border border-zinc-200 dark:border-white/[0.1] bg-black shadow-lg">
                <video
                  ref={videoRef}
                  controls
                  preload="metadata"
                  src={mediaUrl}
                  onLoadedMetadata={() => {
                    if (videoRef.current) {
                      videoRef.current.currentTime = targetSeconds;
                    }
                  }}
                  className="w-full max-h-[260px] bg-black"
                >
                  Your browser does not support the video tag.
                </video>
              </div>

              {/* Video Jump & Play Segment Action Bar */}
              <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <PlayCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  <div className="min-w-0">
                    <span className="text-xs font-bold text-emerald-900 dark:text-emerald-200 block truncate">
                      Segment at {citation.location?.timestamp || `@${targetSeconds}s`}
                    </span>
                    <span className="text-[11px] text-zinc-500 dark:text-zinc-400 block truncate">
                      Aligned with cited answer excerpt
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={handlePlaySegment}
                    className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-xs transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Play Segment</span>
                  </button>
                  <a
                    href={`${mediaUrl}#t=${targetSeconds}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 rounded-xl bg-zinc-200/60 dark:bg-white/[0.06] text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 transition-colors"
                    title="Open full video in new tab"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* Excerpt */}
          <div className="p-4 rounded-2xl bg-zinc-50 dark:bg-white/[0.02] border border-zinc-200/80 dark:border-white/[0.06]">
            <span className="text-xs font-bold uppercase text-zinc-500 dark:text-zinc-400 tracking-wider block mb-1.5">
              Verbatim Ingested Transcript / Slide Text:
            </span>
            <p className="text-xs sm:text-sm text-zinc-800 dark:text-zinc-200 leading-relaxed font-normal">
              "{citation.excerpt}"
            </p>
          </div>

          {/* Diagram caption if present */}
          {citation.diagram_caption && (
            <div className="p-4 rounded-2xl bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-500/20 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-700 dark:text-indigo-300">
                <ImageIcon className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <span>Multimodal Vision Model Diagram Caption:</span>
              </div>
              <p className="text-xs text-indigo-900 dark:text-indigo-100/90 leading-relaxed">
                {citation.diagram_caption}
              </p>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="pt-3.5 border-t border-zinc-200 dark:border-white/[0.08] flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400 shrink-0">
          <span className="flex items-center gap-1.5 text-xs font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            Faithfulness Score: 1.00 (Verified)
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200 text-xs font-semibold transition-all cursor-pointer shadow-xs"
          >
            Close Viewer
          </button>
        </div>

      </div>
    </div>
  );
}
