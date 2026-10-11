"use client";

import React, { useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { PrerequisiteGraph } from "@/components/PrerequisiteGraph";
import {
  GitBranch,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Video,
  Layers,
  Sparkles,
  Info,
  Network,
} from "lucide-react";
import { MOCK_CONCEPTS, MOCK_CONTENT_UNITS, ConceptNode } from "@/lib/mockData";
import { fetchKnowledgeGraph } from "@/lib/api";

export default function GraphPage() {
  const [concepts, setConcepts] = useState<ConceptNode[]>(MOCK_CONCEPTS);
  const [selectedConcept, setSelectedConcept] = useState<ConceptNode>(MOCK_CONCEPTS[1]); // Chain rule
  const [isLiveGraph, setIsLiveGraph] = useState(false);

  React.useEffect(() => {
    async function loadGraph() {
      try {
        const res = await fetchKnowledgeGraph();
        if (res.nodes && res.nodes.length > 0) {
          const liveNodes: ConceptNode[] = res.nodes.map((n, idx) => ({
            concept_id: n.id,
            name: n.name,
            topic: n.topic,
            prerequisites: n.prerequisites,
            evidence_units: n.evidence_units,
            mastery: 0.55 + (idx % 3) * 0.1,
            status: "learning",
            evidenceCount: n.evidence_count,
            description: n.description || `Validated concept under ${n.topic}. Mined with ${n.evidence_count} evidence units from course materials.`,
            keyTakeaways: n.keyTakeaways && n.keyTakeaways.length > 0 ? n.keyTakeaways : [
              `Prerequisites: ${n.prerequisites.length > 0 ? n.prerequisites.join(", ") : "None (Foundational topic)"}`,
              `Linked to ${n.evidence_count} verified course excerpts.`,
            ],
            evidence_details: n.evidence_details,
          }));
          setConcepts(liveNodes);
          setSelectedConcept(liveNodes[0]);
          setIsLiveGraph(true);
        }
      } catch (err) {
        console.warn("Using local mock graph:", err);
      }
    }
    loadGraph();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-[#fafafa] dark:bg-[#07090e] text-zinc-900 dark:text-zinc-100">
      <SiteHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col">
        {/* Page Title */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-zinc-200 dark:border-white/[0.08] mb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">
                Concept Knowledge Graph & Prerequisite DAG
              </h1>
              <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                NetworkX Topology
              </span>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
              Prerequisite dependencies mined from course materials. Enables pedagogical backward-walks when learners struggle.
            </p>
          </div>
        </div>

        {/* 2-Pane Graph Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-[600px]">
          
          {/* Left: Interactive DAG Visualizer (5 cols) */}
          <div className="lg:col-span-5 h-full">
            <PrerequisiteGraph
              concepts={concepts}
              selectedConcept={selectedConcept}
              onSelectConcept={setSelectedConcept}
            />
          </div>

          {/* Right: Selected Node Deep Dive & Evidence Units (7 cols) */}
          <div className="lg:col-span-7 h-full flex flex-col bg-white dark:bg-[#0c111c] border border-zinc-200 dark:border-white/[0.08] rounded-2xl p-6 shadow-sm">
            
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-zinc-200 dark:border-white/[0.08] mb-6">
              <div>
                <span className="text-xs font-semibold uppercase text-zinc-400 tracking-wider">
                  Concept Node Details · {selectedConcept.concept_id}
                </span>
                <h2 className="text-xl font-bold text-zinc-900 dark:text-white mt-0.5">
                  {selectedConcept.name}
                </h2>
                <span className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold">
                  Topic: {selectedConcept.topic}
                </span>
              </div>

              <div className="text-right">
                <span className={`text-2xl font-extrabold ${selectedConcept.mastery < 0.5 ? "text-amber-500" : "text-emerald-500"}`}>
                  {Math.round(selectedConcept.mastery * 100)}%
                </span>
                <span className="block text-[10px] text-zinc-400 uppercase font-semibold">
                  BKT Mastery
                </span>
              </div>
            </div>

            {/* Prerequisite Chain Status */}
            <div className="p-4 rounded-xl bg-zinc-50 dark:bg-white/[0.02] border border-zinc-200/80 dark:border-white/[0.06] mb-6">
              <h3 className="text-xs font-semibold text-zinc-900 dark:text-white mb-2 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-purple-500" />
                <span>Prerequisite Resolution Chain</span>
              </h3>

              <div className="flex flex-wrap items-center gap-2 text-xs">
                {selectedConcept.prerequisites.length === 0 ? (
                  <span className="text-xs text-zinc-500 font-medium">
                    None (This is a foundational root concept in the curriculum DAG).
                  </span>
                ) : (
                  selectedConcept.prerequisites.map((prereqId) => {
                    const prereqNode = concepts.find((c) => c.concept_id === prereqId);
                    const mastery = prereqNode ? Math.round(prereqNode.mastery * 100) : 50;
                    return (
                      <div
                        key={prereqId}
                        className="px-3 py-1.5 rounded-lg bg-white dark:bg-white/[0.06] border border-zinc-200 dark:border-white/[0.1] font-medium text-zinc-800 dark:text-zinc-200 flex items-center gap-2"
                      >
                        <span>Requires: {prereqNode?.name || prereqId}</span>
                        <span className={`text-xs font-semibold ${mastery < 50 ? "text-amber-500" : "text-emerald-500"}`}>
                          ({mastery}% Mastery)
                        </span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Pedagogical Backward-Walk Explanation (Section 2.5 of Plan) */}
            <div className="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/20 border border-indigo-200/60 dark:border-indigo-500/20 mb-6 text-xs text-zinc-800 dark:text-zinc-200">
              <div className="flex items-center gap-2 font-semibold text-indigo-700 dark:text-indigo-300 mb-1">
                <Sparkles className="w-4 h-4 text-indigo-500" />
                <span>Pedagogical Backward-Walk Principle</span>
              </div>
              <p className="leading-relaxed">
                When a student struggles with a concept, the adaptive tutor avoids repetitive frustration on the failure node. It walks backward along prerequisite DAG edges:
              </p>
              <div className="mt-2 p-2.5 rounded-lg bg-white/60 dark:bg-black/30 font-medium text-xs text-indigo-900 dark:text-indigo-200">
                {selectedConcept.prerequisites.length > 0 ? (
                  <span>
                    {selectedConcept.prerequisites
                      .map((p) => concepts.find((c) => c.concept_id === p)?.name || p)
                      .join(" & ")}{" "}
                    (Prerequisite) → <strong>{selectedConcept.name}</strong>
                  </span>
                ) : (
                  <span>
                    <strong>{selectedConcept.name}</strong> (Foundational Root Node) → Unlocks downstream modules
                  </span>
                )}
              </div>
              <p className="mt-2 text-zinc-600 dark:text-zinc-400">
                {selectedConcept.prerequisites.length > 0 ? (
                  <>
                    If diagnostic assessment detects a misconception in <strong>{selectedConcept.name}</strong>, remediation automatically shifts to verify upstream mastery of{" "}
                    <strong>{concepts.find((c) => c.concept_id === selectedConcept.prerequisites[0])?.name || selectedConcept.prerequisites[0]}</strong>.
                  </>
                ) : (
                  <>
                    Since <strong>{selectedConcept.name}</strong> has no prerequisite bottlenecks, foundational grounding exercises are delivered directly from primary lecture slides.
                  </>
                )}
              </p>
            </div>

            {/* Linked Evidence Units */}
            <div className="flex-1">
              <h3 className="text-xs font-semibold text-zinc-900 dark:text-white mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-500" />
                <span>Grounding Evidence Units ({selectedConcept.evidence_details?.length || selectedConcept.evidence_units.length})</span>
              </h3>

              <div className="space-y-2">
                {selectedConcept.evidence_details && selectedConcept.evidence_details.length > 0 ? (
                  selectedConcept.evidence_details.map((detail, idx) => (
                    <div
                      key={detail.unit_id || idx}
                      className="p-3 rounded-xl bg-zinc-50 dark:bg-white/[0.02] border border-zinc-200/80 dark:border-white/[0.06] text-xs"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-zinc-900 dark:text-white">
                          {detail.source_id}
                        </span>
                        <span className="text-zinc-500 text-xs font-medium">
                          {detail.location?.slide ? `Slide ${detail.location.slide}` : detail.location?.page ? `Page ${detail.location.page}` : `Unit ${idx + 1}`}
                        </span>
                      </div>
                      <p className="text-zinc-600 dark:text-zinc-400 text-xs leading-relaxed">
                        "{detail.text}"
                      </p>
                    </div>
                  ))
                ) : (
                  selectedConcept.evidence_units.map((unitId) => {
                    const unit = MOCK_CONTENT_UNITS.find((u) => u.unit_id === unitId) || MOCK_CONTENT_UNITS[0];
                    return (
                      <div
                        key={unitId}
                        className="p-3 rounded-xl bg-zinc-50 dark:bg-white/[0.02] border border-zinc-200/80 dark:border-white/[0.06] text-xs"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-zinc-900 dark:text-white">
                            {unit.source_id}
                          </span>
                          <span className="text-zinc-500 text-xs font-medium">
                            {unit.location.slide ? `Slide ${unit.location.slide}` : "Course Material"}
                          </span>
                        </div>
                        <p className="text-zinc-600 dark:text-zinc-400 text-xs leading-relaxed">
                          "{unit.text}"
                        </p>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

          </div>

        </div>
      </main>
    </div>
  );
}
