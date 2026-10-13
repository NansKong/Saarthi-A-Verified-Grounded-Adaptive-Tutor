"use client";

import React, { useState, useEffect } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { PrerequisiteGraph } from "@/components/PrerequisiteGraph";
import { MediaPreviewModal } from "@/components/MediaPreviewModal";
import { CourseUploadModal } from "@/components/CourseUploadModal";
import {
  GitBranch,
  ArrowRight,
  CheckCircle2,
  FileText,
  Video,
  Image as ImageIcon,
  Layers,
  Sparkles,
  Info,
  Network,
  FolderOpen,
  Eye,
  Download,
  Plus,
  UploadCloud,
  FileCode,
  ExternalLink,
} from "lucide-react";
import { MOCK_CONCEPTS, MOCK_CONTENT_UNITS, ConceptNode } from "@/lib/mockData";
import {
  fetchKnowledgeGraph,
  fetchUploadedMaterials,
  UploadedMaterial,
  ContentUnit,
} from "@/lib/api";

export default function GraphPage() {
  const [concepts, setConcepts] = useState<ConceptNode[]>(MOCK_CONCEPTS);
  const [selectedConcept, setSelectedConcept] = useState<ConceptNode>(MOCK_CONCEPTS[1]); // Chain rule
  const [isLiveGraph, setIsLiveGraph] = useState(false);
  const [uploadedMaterials, setUploadedMaterials] = useState<UploadedMaterial[]>([]);
  const [previewMaterial, setPreviewMaterial] = useState<UploadedMaterial | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"dag" | "media">("dag");

  async function loadData() {
    try {
      const [resGraph, resMaterials] = await Promise.all([
        fetchKnowledgeGraph(),
        fetchUploadedMaterials(),
      ]);

      if (resGraph.nodes && resGraph.nodes.length > 0) {
        const liveNodes: ConceptNode[] = resGraph.nodes.map((n, idx) => ({
          concept_id: n.id,
          name: n.name,
          topic: n.topic,
          prerequisites: n.prerequisites,
          evidence_units: n.evidence_units,
          mastery: 0.55 + (idx % 3) * 0.1,
          status: "learning",
          evidenceCount: n.evidence_count,
          description:
            n.description ||
            `Validated concept under ${n.topic}. Mined with ${n.evidence_count} evidence units from course materials.`,
          keyTakeaways:
            n.keyTakeaways && n.keyTakeaways.length > 0
              ? n.keyTakeaways
              : [
                  `Prerequisites: ${
                    n.prerequisites.length > 0
                      ? n.prerequisites.join(", ")
                      : "None (Foundational topic)"
                  }`,
                  `Linked to ${n.evidence_count} verified course excerpts.`,
                ],
          evidence_details: n.evidence_details,
        }));
        setConcepts(liveNodes);
        setSelectedConcept(liveNodes[0]);
        setIsLiveGraph(true);
      }

      if (resMaterials && resMaterials.length > 0) {
        setUploadedMaterials(resMaterials);
      }
    } catch (err) {
      console.warn("Using local fallback on graph page:", err);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function getMediaIcon(type: string) {
    switch (type) {
      case "pdf":
        return <FileText className="w-4 h-4 text-rose-500" />;
      case "pptx":
        return <Layers className="w-4 h-4 text-amber-500" />;
      case "video":
        return <Video className="w-4 h-4 text-emerald-500" />;
      case "image":
        return <ImageIcon className="w-4 h-4 text-purple-500" />;
      default:
        return <FileCode className="w-4 h-4 text-blue-500" />;
    }
  }

  function getMediaBadgeClass(type: string) {
    switch (type) {
      case "pdf":
        return "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20";
      case "pptx":
        return "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20";
      case "video":
        return "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20";
      case "image":
        return "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20";
      default:
        return "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20";
    }
  }

  const handleUploadSuccess = () => {
    loadData();
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#fafafa] dark:bg-[#07090e] text-zinc-900 dark:text-zinc-100 transition-colors">
      <SiteHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col space-y-6">
        
        {/* Page Title & View Switcher */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-zinc-200 dark:border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">
                Concept Knowledge Graph & Course Media
              </h1>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                Curriculum Graph
              </span>
              {uploadedMaterials.length > 0 && (
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                  {uploadedMaterials.length} Ingested Media File{uploadedMaterials.length > 1 ? "s" : ""}
                </span>
              )}
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
              Prerequisite dependencies and uploaded course files. Inspect evidence units that ground every concept node.
            </p>
          </div>

          {/* View Segmented Toggle + Upload Trigger */}
          <div className="flex items-center gap-2">
            <div className="flex items-center p-1 rounded-2xl bg-zinc-100 dark:bg-white/[0.05] border border-zinc-200/80 dark:border-white/[0.08]">
              <button
                onClick={() => setActiveTab("dag")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "dag"
                    ? "bg-white dark:bg-[#0c111c] text-zinc-950 dark:text-white shadow-xs"
                    : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
                }`}
              >
                <GitBranch className="w-3.5 h-3.5" />
                <span>Prerequisite DAG</span>
              </button>

              <button
                onClick={() => setActiveTab("media")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "media"
                    ? "bg-white dark:bg-[#0c111c] text-zinc-950 dark:text-white shadow-xs"
                    : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
                }`}
              >
                <FolderOpen className="w-3.5 h-3.5" />
                <span>Uploaded Media ({uploadedMaterials.length})</span>
              </button>
            </div>

            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Add Material</span>
            </button>
          </div>
        </div>

        {/* View 1: Prerequisite DAG View */}
        {activeTab === "dag" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[580px]">
              
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
                    <span
                      className={`text-2xl font-extrabold ${
                        selectedConcept.mastery < 0.5 ? "text-amber-500" : "text-emerald-500"
                      }`}
                    >
                      {Math.round(selectedConcept.mastery * 100)}%
                    </span>
                    <span className="block text-[10px] text-zinc-400 uppercase font-semibold">
                      Mastery
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
                            <span
                              className={`text-xs font-semibold ${
                                mastery < 50 ? "text-amber-500" : "text-emerald-500"
                              }`}
                            >
                              ({mastery}% Mastery)
                            </span>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

                {/* Pedagogical Backward-Walk Explanation */}
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
                </div>

                {/* Linked Evidence Units */}
                <div className="flex-1">
                  <h3 className="text-xs font-semibold text-zinc-900 dark:text-white mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-500" />
                      <span>
                        Grounding Evidence Units (
                        {selectedConcept.evidence_details?.length || selectedConcept.evidence_units.length})
                      </span>
                    </div>
                    <span className="text-[11px] text-zinc-400">
                      Click any card to preview full media
                    </span>
                  </h3>

                  <div className="space-y-2">
                    {selectedConcept.evidence_details && selectedConcept.evidence_details.length > 0 ? (
                      selectedConcept.evidence_details.map((detail, idx) => {
                        const matchedMedia = uploadedMaterials.find(
                          (m) => m.filename === detail.source_id
                        );
                        return (
                          <div
                            key={detail.unit_id || idx}
                            onClick={() => {
                              if (matchedMedia) setPreviewMaterial(matchedMedia);
                            }}
                            className={`p-3 rounded-xl bg-zinc-50 dark:bg-white/[0.02] border border-zinc-200/80 dark:border-white/[0.06] text-xs transition-all ${
                              matchedMedia
                                ? "hover:border-indigo-500/50 hover:bg-zinc-100/60 dark:hover:bg-white/[0.04] cursor-pointer"
                                : ""
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-semibold text-zinc-900 dark:text-white flex items-center gap-1.5">
                                {getMediaIcon(detail.source_id.split(".").pop() || "")}
                                <span>{detail.source_id}</span>
                              </span>
                              <div className="flex items-center gap-2">
                                <span className="text-zinc-500 text-xs font-medium">
                                  {detail.location?.slide
                                    ? `Slide ${detail.location.slide}`
                                    : detail.location?.page
                                    ? `Page ${detail.location.page}`
                                    : `Unit ${idx + 1}`}
                                </span>
                                {matchedMedia && (
                                  <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold flex items-center gap-0.5">
                                    <Eye className="w-3 h-3" /> Preview
                                  </span>
                                )}
                              </div>
                            </div>
                            <p className="text-zinc-600 dark:text-zinc-400 text-xs leading-relaxed">
                              "{detail.text}"
                            </p>
                          </div>
                        );
                      })
                    ) : (
                      selectedConcept.evidence_units.map((unitId) => {
                        const unit =
                          MOCK_CONTENT_UNITS.find((u) => u.unit_id === unitId) ||
                          MOCK_CONTENT_UNITS[0];
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

            {/* Bottom Ingested Media Strip */}
            {uploadedMaterials.length > 0 && (
              <div className="p-5 rounded-2xl bg-white dark:bg-[#0c111c] border border-zinc-200 dark:border-white/[0.08] shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                      <FolderOpen className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                        Ingested Media Grounding This Knowledge Graph ({uploadedMaterials.length})
                      </h3>
                      <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                        Every concept in the graph DAG links back to verified evidence units in these files. Click any media to inspect and preview.
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => setActiveTab("media")}
                    className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <span>View All Media</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {uploadedMaterials.slice(0, 4).map((mat) => (
                    <div
                      key={mat.filename}
                      onClick={() => setPreviewMaterial(mat)}
                      className="p-3.5 rounded-xl bg-zinc-50 dark:bg-white/[0.03] border border-zinc-200/80 dark:border-white/[0.06] hover:border-indigo-500/50 hover:bg-zinc-100/60 dark:hover:bg-white/[0.05] transition-all cursor-pointer flex flex-col justify-between group shadow-2xs"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span
                            className={`px-2 py-0.5 rounded-md text-[10px] font-bold border flex items-center gap-1 ${getMediaBadgeClass(
                              mat.file_type
                            )}`}
                          >
                            {getMediaIcon(mat.file_type)}
                            <span className="uppercase">{mat.file_type}</span>
                          </span>
                          <span className="text-[10px] font-mono text-zinc-400">
                            {formatBytes(mat.size_bytes)}
                          </span>
                        </div>

                        <h4
                          className="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors"
                          title={mat.filename}
                        >
                          {mat.filename}
                        </h4>
                      </div>

                      <div className="mt-3 pt-2.5 border-t border-zinc-200/60 dark:border-white/[0.04] flex items-center justify-between text-[11px] text-zinc-500">
                        <span>{mat.units_count} units indexed</span>
                        <span className="text-indigo-600 dark:text-indigo-400 font-semibold flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          Preview <Eye className="w-3 h-3" />
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* View 2: Full Uploaded Media Gallery */}
        {activeTab === "media" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-white dark:bg-[#0c111c] border border-zinc-200 dark:border-white/[0.08] shadow-sm space-y-5">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <h2 className="text-base font-bold text-zinc-900 dark:text-white">
                    Course Media Library & Grounding Sources
                  </h2>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Browse all uploaded textbooks, lecture slides, diagrams, and video recordings. Preview any document and inspect its grounded DAG concept nodes.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-zinc-500">
                    Total: {uploadedMaterials.length} materials
                  </span>
                </div>
              </div>

              {uploadedMaterials.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {uploadedMaterials.map((mat) => (
                    <div
                      key={mat.filename}
                      className="p-5 rounded-2xl bg-zinc-50 dark:bg-white/[0.02] border border-zinc-200/80 dark:border-white/[0.08] hover:border-indigo-500/40 hover:shadow-lg transition-all flex flex-col justify-between group"
                    >
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span
                            className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border flex items-center gap-1.5 ${getMediaBadgeClass(
                              mat.file_type
                            )}`}
                          >
                            {getMediaIcon(mat.file_type)}
                            <span className="uppercase">{mat.file_type}</span>
                          </span>
                          <span className="text-xs font-mono text-zinc-400">
                            {formatBytes(mat.size_bytes)}
                          </span>
                        </div>

                        <div>
                          <h3
                            className="text-sm font-bold text-zinc-900 dark:text-white truncate"
                            title={mat.filename}
                          >
                            {mat.filename}
                          </h3>
                          <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                            <span>{mat.units_count} knowledge units</span>
                            <span>•</span>
                            <span>
                              {mat.linked_concepts.length} concept{mat.linked_concepts.length === 1 ? "" : "s"} linked
                            </span>
                          </div>
                        </div>

                        {/* Linked Concepts Preview Tags */}
                        {mat.linked_concepts.length > 0 && (
                          <div className="pt-2 flex flex-wrap gap-1.5">
                            {mat.linked_concepts.slice(0, 3).map((c) => (
                              <span
                                key={c.concept_id}
                                className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 truncate max-w-[150px]"
                                title={c.name}
                              >
                                {c.name}
                              </span>
                            ))}
                            {mat.linked_concepts.length > 3 && (
                              <span className="px-1.5 py-0.5 text-[10px] font-mono text-zinc-400">
                                +{mat.linked_concepts.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="mt-5 pt-3.5 border-t border-zinc-200/80 dark:border-white/[0.06] flex items-center justify-between gap-2">
                        <button
                          onClick={() => setPreviewMaterial(mat)}
                          className="flex-1 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Preview Material</span>
                        </button>

                        <a
                          href={mat.download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 rounded-xl bg-zinc-200/60 hover:bg-zinc-200 dark:bg-white/[0.06] dark:hover:bg-white/[0.1] text-zinc-700 dark:text-zinc-300 transition-colors"
                          title="Open original file in new tab"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-12 text-center rounded-2xl border-2 border-dashed border-zinc-300 dark:border-white/[0.1] flex flex-col items-center justify-center space-y-3">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-500/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                    <FolderOpen className="w-6 h-6" />
                  </div>
                  <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                    No course materials uploaded yet
                  </h3>
                  <p className="text-xs text-zinc-500 max-w-sm">
                    Upload your course PDF textbooks, PPTX lecture slides, or video recordings to automatically populate the concept graph.
                  </p>
                  <button
                    onClick={() => setIsUploadModalOpen(true)}
                    className="px-4 py-2 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all cursor-pointer shadow-sm"
                  >
                    Upload First Course File
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

      </main>

      {/* Media Preview Modal */}
      <MediaPreviewModal
        material={previewMaterial}
        isOpen={!!previewMaterial}
        onClose={() => setPreviewMaterial(null)}
        onSelectConcept={(conceptId) => {
          const found = concepts.find((c) => c.concept_id === conceptId);
          if (found) {
            setSelectedConcept(found);
            setActiveTab("dag");
          }
        }}
      />

      {/* Course Upload Modal */}
      <CourseUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
}
