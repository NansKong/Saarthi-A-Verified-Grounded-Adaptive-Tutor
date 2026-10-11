"use client";

import React from "react";
import { GitBranch, Layers, ArrowDown, CheckCircle2, AlertTriangle, FileCode } from "lucide-react";
import { ConceptNode } from "@/lib/mockData";

interface PrerequisiteGraphProps {
  concepts: ConceptNode[];
  selectedConcept: ConceptNode | null;
  onSelectConcept: (c: ConceptNode) => void;
}

export function PrerequisiteGraph({
  concepts,
  selectedConcept,
  onSelectConcept,
}: PrerequisiteGraphProps) {
  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#0c111c] border border-zinc-200 dark:border-white/[0.08] rounded-2xl overflow-hidden p-4 sm:p-5 shadow-sm">
      {/* Pane Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-zinc-200/80 dark:border-white/[0.06]">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          <h2 className="text-sm font-bold text-zinc-900 dark:text-white tracking-tight">
            Concept Knowledge Graph
          </h2>
        </div>
        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-zinc-100 dark:bg-white/[0.05] text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-white/[0.06]">
          DAG Topology
        </span>
      </div>

      <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-2 mb-3 leading-relaxed">
        NetworkX prerequisite DAG derived from lecture evidence. Mastering upstream concepts unlocks advanced topics.
      </p>

      {/* DAG Node Chain */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
        {concepts.map((concept, idx) => {
          const isSelected = selectedConcept?.concept_id === concept.concept_id;
          const isWeak = concept.mastery < 0.5;

          return (
            <React.Fragment key={concept.concept_id}>
              <div
                onClick={() => onSelectConcept(concept)}
                className={`relative group p-3.5 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? "bg-indigo-50/80 dark:bg-indigo-950/40 border-indigo-400 dark:border-indigo-500/60 shadow-sm ring-1 ring-indigo-400/30 dark:ring-indigo-500/30"
                    : "bg-zinc-50/70 dark:bg-white/[0.02] border-zinc-200/80 dark:border-white/[0.06] hover:bg-zinc-100 dark:hover:bg-white/[0.05] hover:border-zinc-300 dark:hover:border-white/[0.12]"
                }`}
              >
                {/* Node Status Badge */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {isWeak ? (
                      <AlertTriangle className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    )}
                    <div>
                      <h4 className="text-xs font-bold text-zinc-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors">
                        {concept.name}
                      </h4>
                      <p className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">
                        {concept.topic}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span
                      className={`text-xs font-bold ${
                        isWeak ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400"
                      }`}
                    >
                      {Math.round(concept.mastery * 100)}%
                    </span>
                    <span className="block text-[10px] text-zinc-500 dark:text-zinc-400 uppercase font-bold">
                      Mastery
                    </span>
                  </div>
                </div>

                {/* Progress bar inside node */}
                <div className="w-full bg-zinc-200 dark:bg-white/[0.05] h-1.5 rounded-full mt-2.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isWeak
                        ? "bg-gradient-to-r from-amber-500 to-orange-400"
                        : "bg-gradient-to-r from-emerald-500 to-teal-400"
                    }`}
                    style={{ width: `${Math.round(concept.mastery * 100)}%` }}
                  />
                </div>

                {/* Evidence units indicator */}
                <div className="mt-2.5 flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400 font-medium">
                  <span>
                    Prereqs: {concept.prerequisites.length === 0 ? "None (Root)" : `${concept.prerequisites.length} required`}
                  </span>
                  <span className="flex items-center gap-1 text-zinc-500 dark:text-zinc-400 group-hover:text-zinc-700 dark:group-hover:text-zinc-300">
                    <FileCode className="w-3 h-3 text-indigo-500 dark:text-indigo-400" />
                    {concept.evidence_units.length} Evidence Unit(s)
                  </span>
                </div>
              </div>

              {/* Arrow connector between prerequisite nodes */}
              {idx < concepts.length - 1 && (
                <div className="flex justify-center items-center py-0.5">
                  <div className="flex items-center gap-1 text-xs font-semibold text-zinc-500 dark:text-zinc-400">
                    <ArrowDown className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400 animate-pulse" />
                    <span>prerequisite</span>
                  </div>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Prerequisite rule callout */}
      <div className="mt-3 p-3 rounded-xl bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 text-xs text-amber-900 dark:text-amber-300/90 flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <p>
          <strong>Backward-walk Active:</strong> {selectedConcept ? `Remediates foundational prerequisites before unlocking ${selectedConcept.name}.` : "If a student struggles, the tutor targets weak prerequisites first."}
        </p>
      </div>
    </div>
  );
}
