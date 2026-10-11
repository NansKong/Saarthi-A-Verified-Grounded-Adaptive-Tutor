"use client";

import React, { useState, useRef } from "react";
import {
  MessageSquare,
  Send,
  Sparkles,
  FileText,
  Video,
  ShieldAlert,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  Globe2,
  Paperclip,
  UploadCloud,
  X,
  Plus,
  Image as ImageIcon,
} from "lucide-react";
import { ChatMessage, AttachedFile } from "@/lib/mockData";

import { generatePdfThumbnail } from "@/lib/generatePdfThumbnail";

interface GroundedChatProps {
  messages: ChatMessage[];
  onSendMessage: (
    text: string,
    attachments?: AttachedFile[]
  ) => void;
  onCitationClick: (citation: any) => void;
  hindiMode: boolean;
  onOpenUploadModal?: () => void;
}

function getFormatDetails(file: AttachedFile) {
  let ext = (file.extension || "").toUpperCase();
  if (!ext) {
    const parts = file.name.split(".");
    ext = parts.length > 1 ? parts.pop()!.toUpperCase() : "FILE";
  }

  let badgeBg = "bg-zinc-700";
  const isImage =
    file.type === "image" ||
    ["PNG", "JPG", "JPEG", "WEBP", "GIF", "SVG"].includes(ext);
  const isVideo =
    file.type === "video" ||
    ["MP4", "MOV", "WEBM", "AVI", "MKV"].includes(ext);
  const isAudio = ["MP3", "WAV", "AAC", "M4A"].includes(ext);
  const isPdf = file.type === "pdf" || ext === "PDF";
  const isPpt = ["PPT", "PPTX"].includes(ext);

  switch (ext) {
    case "PDF":
      badgeBg = "bg-rose-600";
      break;
    case "PNG":
      badgeBg = "bg-blue-600";
      break;
    case "JPG":
    case "JPEG":
      badgeBg = "bg-amber-600";
      break;
    case "WEBP":
      badgeBg = "bg-teal-600";
      break;
    case "SVG":
      badgeBg = "bg-violet-600";
      break;
    case "MP4":
    case "MOV":
    case "WEBM":
      badgeBg = "bg-emerald-600";
      break;
    case "PPT":
    case "PPTX":
      badgeBg = "bg-orange-600";
      break;
    case "DOC":
    case "DOCX":
      badgeBg = "bg-sky-600";
      break;
    case "MP3":
    case "WAV":
      badgeBg = "bg-purple-600";
      break;
    default:
      badgeBg = "bg-zinc-600";
  }

  return { ext, badgeBg, isImage, isVideo, isAudio, isPdf, isPpt };
}

export function AttachmentPreviewCard({
  file,
  onRemove,
}: {
  file: AttachedFile;
  onRemove?: () => void;
}) {
  const { ext, badgeBg, isImage, isVideo } = getFormatDetails(file);

  // When an IMAGE is uploaded: show ONLY the image preview! No bottom filename bar!
  if (isImage) {
    return (
      <div className="relative group w-32 sm:w-36 h-28 rounded-2xl overflow-hidden border border-zinc-200 dark:border-white/[0.12] bg-white dark:bg-zinc-950 shadow-sm flex shrink-0 transition-all hover:shadow-md hover:scale-[1.02]">
        {/* Floating Remove Button */}
        {onRemove && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="absolute top-1.5 right-1.5 z-10 w-5 h-5 rounded-full bg-black/75 hover:bg-black text-white flex items-center justify-center transition-all opacity-80 group-hover:opacity-100 cursor-pointer shadow-md"
            title="Remove attachment"
          >
            <X className="w-3 h-3 stroke-[2.5]" />
          </button>
        )}

        {/* Pure Image Preview - fills entire card cleanly */}
        {file.previewUrl ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={file.previewUrl}
            alt={file.name}
            className="w-full h-full object-cover select-none"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-1.5 p-3 text-zinc-400 bg-zinc-900">
            <ImageIcon className="w-7 h-7 text-blue-400" />
            <span className="text-[9px] font-medium text-zinc-300 truncate max-w-[100px]">
              {file.name}
            </span>
          </div>
        )}
      </div>
    );
  }

  // When a DOCUMENT / PDF / PPT / VIDEO is uploaded: show document preview + bottom filename bar
  return (
    <div className="relative group w-36 sm:w-40 h-28 rounded-2xl overflow-hidden border border-zinc-200 dark:border-white/[0.12] bg-white dark:bg-zinc-900 shadow-sm flex flex-col shrink-0 transition-all hover:shadow-md hover:scale-[1.02]">
      {/* Floating Remove Button */}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="absolute top-1.5 right-1.5 z-10 w-5 h-5 rounded-full bg-black/75 hover:bg-black text-white flex items-center justify-center transition-all opacity-80 group-hover:opacity-100 cursor-pointer shadow-md"
          title="Remove attachment"
        >
          <X className="w-3 h-3 stroke-[2.5]" />
        </button>
      )}

      {/* Top Preview Section: Real Rendered Document Page Preview */}
      <div className="flex-1 bg-white select-none overflow-hidden relative">
        {file.previewUrl ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={file.previewUrl}
            alt={file.name}
            className="w-full h-full object-cover object-top"
          />
        ) : isVideo ? (
          <div className="w-full h-full bg-gradient-to-br from-emerald-950 via-zinc-950 to-black p-2.5 flex flex-col justify-between select-none">
            <div className="flex items-center justify-between text-emerald-400">
              <Video className="w-4 h-4 shrink-0" />
              <span className="text-[7px] font-mono px-1 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                Lecture Video
              </span>
            </div>
            <div className="space-y-0.5">
              <div className="text-[8.5px] font-bold text-white truncate">
                {file.previewHeading || file.name}
              </div>
              <div className="text-[7px] text-zinc-400 truncate">
                Whisper timestamp aligned
              </div>
            </div>
          </div>
        ) : (
          /* Document fallback layout */
          <div className="w-full h-full p-2.5 text-zinc-900 font-serif flex flex-col justify-between">
            <div>
              <div className="font-bold text-[8.5px] leading-tight mb-1 text-black font-sans border-b border-zinc-200/90 pb-0.5 truncate">
                {file.previewHeading || file.name.replace(/\.[^/.]+$/, "")}
              </div>
              <div className="text-[6.5px] leading-[1.25] text-zinc-600 space-y-0.5 font-serif">
                {file.previewLines && file.previewLines.length > 0 ? (
                  file.previewLines.map((line, idx) => (
                    <p key={idx} className="line-clamp-1">{line}</p>
                  ))
                ) : (
                  <>
                    <p className="line-clamp-1 font-semibold text-zinc-800">
                      {file.name}
                    </p>
                    <p className="line-clamp-2 text-zinc-500">
                      Extracted lecture content, syllabus definitions, and proofs.
                    </p>
                    <p className="line-clamp-1 text-zinc-400">
                      Verified ground evidence unit.
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Section: Sleek Dark Capsule Bar with Red PDF Badge & Truncated Filename */}
      <div className="bg-[#0b0e14] px-2.5 py-1.5 flex items-center gap-1.5 border-t border-zinc-200 dark:border-white/[0.08] shrink-0">
        <div
          className={`flex items-center justify-center min-w-[24px] px-1 h-3.5 rounded text-[6.5px] font-extrabold text-white uppercase shrink-0 tracking-wider ${badgeBg}`}
        >
          {ext}
        </div>
        <span
          className="text-[10px] font-medium text-white truncate max-w-[105px]"
          title={file.name}
        >
          {file.name}
        </span>
      </div>
    </div>
  );
}

export function GroundedChat({
  messages,
  onSendMessage,
  onCitationClick,
  hindiMode,
  onOpenUploadModal,
}: GroundedChatProps) {
  const [input, setInput] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && attachedFiles.length === 0) return;

    onSendMessage(
      input.trim() || `Analyze attached materials: ${attachedFiles.map((f) => f.name).join(", ")}`,
      attachedFiles.length > 0 ? attachedFiles : undefined
    );
    setInput("");
    setAttachedFiles([]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFiles = Array.from(e.target.files);
      const newFiles: AttachedFile[] = selectedFiles.map((file, idx) => {
        const extMatch = file.name.match(/\.([a-zA-Z0-9]+)$/);
        const ext = extMatch ? extMatch[1].toUpperCase() : "FILE";

        let type: "pdf" | "video" | "image" | "file" = "file";
        if (file.type.includes("pdf") || /\.pdf$/i.test(file.name) || /\.pptx?$/i.test(file.name)) {
          type = "pdf";
        } else if (file.type.includes("video") || /\.(mp4|mov|webm)$/i.test(file.name)) {
          type = "video";
        } else if (file.type.includes("image") || /\.(png|jpe?g|webp|gif|svg)$/i.test(file.name)) {
          type = "image";
        }

        const sizeStr = (file.size / (1024 * 1024)).toFixed(1) + " MB";
        const previewUrl =
          type === "image" || file.type.startsWith("image/")
            ? URL.createObjectURL(file)
            : undefined;

        const fileId = `att_${Date.now()}_${idx}`;

        // If it's a PDF, dynamically render the first page via client Canvas
        if (type === "pdf" || /\.pdf$/i.test(file.name)) {
          generatePdfThumbnail(file).then((thumbUrl) => {
            if (thumbUrl) {
              setAttachedFiles((prev) =>
                prev.map((f) => (f.id === fileId ? { ...f, previewUrl: thumbUrl } : f))
              );
            }
          });
        }

        return {
          id: fileId,
          name: file.name,
          type,
          extension: ext,
          previewUrl,
          size: sizeStr,
          previewHeading: file.name.replace(/\.[^/.]+$/, ""),
        };
      });

      setAttachedFiles((prev) => [...prev, ...newFiles]);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleRemoveFile = (id: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const samplePrompts = [
    "Summarize foundational concepts in this course",
    "What are the prerequisite dependencies for this topic?",
    "Test out-of-syllabus refusal",
  ];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#0c111c] border border-zinc-200 dark:border-white/[0.08] rounded-2xl overflow-hidden p-4 sm:p-5 shadow-sm">
      {/* Pane Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-zinc-200/80 dark:border-white/[0.06]">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          <h2 className="text-sm font-bold text-zinc-900 dark:text-white tracking-tight">
            Evidence-Grounded Tutor
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {onOpenUploadModal && (
            <button
              onClick={onOpenUploadModal}
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/40 dark:hover:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 transition-all cursor-pointer shadow-sm"
              title="Upload PDF, slides, or lecture videos"
            >
              <UploadCloud className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
              <span>Upload Materials</span>
            </button>
          )}

          <span className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
            100% Citation Grounded
          </span>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto space-y-4 my-3 pr-1">
        {messages.length === 0 ? (
          <div className="h-full min-h-[220px] flex flex-col items-center justify-center text-center p-6 border border-dashed border-zinc-200 dark:border-white/[0.08] rounded-xl bg-zinc-50/50 dark:bg-white/[0.01]">
            <div className="w-10 h-10 rounded-full bg-indigo-50 dark:bg-indigo-950/40 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mb-3">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
              Verified Grounded Course Tutor
            </h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 max-w-md mt-1 mb-4 leading-relaxed">
              Ask any question or upload course documents. Every explanation is strictly grounded in your syllabus with verifiable citation chips.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === "student" ? "items-end" : "items-start"
            }`}
          >
            {/* Header label */}
            <div className="flex items-center gap-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400 mb-1 px-1">
              {msg.sender === "student" ? (
                <span>Student · {msg.timestamp}</span>
              ) : (
                <span className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 font-semibold">
                  <Sparkles className="w-3.5 h-3.5" />
                  Saarthi Verified Tutor · {msg.timestamp}
                </span>
              )}
            </div>

            {/* Bubble */}
            {msg.isRefusal ? (
              /* TRANSPARENT REFUSAL CARD */
              <div className="max-w-[90%] p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-500/30 text-rose-900 dark:text-rose-200 shadow-sm">
                <div className="flex items-center gap-2 font-semibold text-xs text-rose-700 dark:text-rose-300 mb-1.5">
                  <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                  <span>Out-of-Scope Grounding Refusal</span>
                </div>
                <p className="text-xs text-rose-800 dark:text-rose-100 leading-relaxed">
                  {msg.text}
                </p>
                <div className="mt-3 pt-2.5 border-t border-rose-200 dark:border-rose-500/20 flex items-center justify-between text-xs text-rose-700 dark:text-rose-300/80">
                  <span>Outside knowledge is withheld to avoid hallucination.</span>
                  <button className="text-xs font-semibold underline hover:text-rose-950 dark:hover:text-white cursor-pointer">
                    Explain with General AI?
                  </button>
                </div>
              </div>
            ) : (
              /* STANDARD GROUNDED MESSAGE */
              <div
                className={`max-w-[90%] p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                  msg.sender === "student"
                    ? "bg-black dark:bg-indigo-600 text-white shadow-sm font-medium"
                    : "bg-zinc-100/90 dark:bg-white/[0.04] border border-zinc-200/80 dark:border-white/[0.08] text-zinc-800 dark:text-zinc-200"
                }`}
              >
                {/* Attached media display (Exact card style) */}
                {((msg.attachments && msg.attachments.length > 0) || msg.attachment) && (
                  <div className="mb-3 flex items-center gap-2 overflow-x-auto pb-1">
                    {(msg.attachments || (msg.attachment ? [msg.attachment] : [])).map((att) => (
                      <AttachmentPreviewCard key={att.id} file={att} />
                    ))}
                  </div>
                )}

                <div className="whitespace-pre-line leading-relaxed">{msg.text}</div>

                {/* Hindi Translation Pill if activated */}
                {hindiMode && msg.hindiTranslation && (
                  <div className="mt-3 pt-2.5 border-t border-zinc-200/80 dark:border-white/[0.08] bg-amber-500/10 -mx-2 -mb-2 p-2.5 rounded-xl text-amber-900 dark:text-amber-200/90 text-xs leading-relaxed">
                    <div className="flex items-center gap-1 text-xs text-amber-700 dark:text-amber-400 mb-1 font-semibold">
                      <Globe2 className="w-3.5 h-3.5" />
                      <span>Sarvam AI Hindi Translation:</span>
                    </div>
                    {msg.hindiTranslation}
                  </div>
                )}

                {/* Citation Chips */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-zinc-200/80 dark:border-white/[0.08]">
                    <span className="text-xs font-bold uppercase text-zinc-500 dark:text-zinc-400 tracking-wider block mb-1.5">
                      Grounding Citations (Click to inspect):
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.citations.map((c, i) => (
                        <button
                          key={i}
                          onClick={() => onCitationClick(c)}
                          className="citation-pill group"
                        >
                          {c.location.slide ? (
                            <FileText className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 group-hover:text-indigo-800 dark:group-hover:text-indigo-200" />
                          ) : (
                            <Video className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 group-hover:text-emerald-800 dark:group-hover:text-emerald-200" />
                          )}
                          <span>[{c.label}]</span>
                          <ExternalLink className="w-3 h-3 opacity-60 group-hover:opacity-100" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))
      )}
    </div>

      {/* Suggested Quick Prompts */}
      <div className="pt-2.5 pb-2 border-t border-zinc-200/80 dark:border-white/[0.06] flex items-center gap-2 overflow-x-auto text-xs text-zinc-500 dark:text-zinc-400">
        <span className="shrink-0 text-xs font-semibold">
          Try prompt:
        </span>
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => onSendMessage(p)}
            className="shrink-0 px-3 py-1 rounded-full bg-zinc-100 dark:bg-white/[0.03] border border-zinc-200/80 dark:border-white/[0.06] hover:bg-zinc-200 dark:hover:bg-white/[0.08] text-zinc-700 dark:text-zinc-300 hover:text-zinc-950 dark:hover:text-white transition-all text-xs font-medium cursor-pointer"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileChange}
        accept=".pdf,.pptx,.mp4,.mp3,.png,.jpg,.jpeg,.webp"
        className="hidden"
      />

      {/* UNIFIED CHATGPT-STYLE PROMPT BOX (With top document cards & bottom action controls) */}
      <form onSubmit={handleSubmit} className="relative mt-2">
        <div className="rounded-3xl border border-zinc-200/90 dark:border-white/[0.12] bg-zinc-100/90 dark:bg-[#111624] p-3 shadow-sm focus-within:border-zinc-400 dark:focus-within:border-indigo-500/50 focus-within:ring-1 focus-within:ring-indigo-500/20 transition-all">
          
          {/* Top Document Attachment Preview Cards Row */}
          {attachedFiles.length > 0 && (
            <div className="flex items-center gap-3 overflow-x-auto pb-3 pt-1 px-1">
              {attachedFiles.map((file) => (
                <AttachmentPreviewCard
                  key={file.id}
                  file={file}
                  onRemove={() => handleRemoveFile(file.id)}
                />
              ))}
            </div>
          )}

          {/* Text Input Area */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              attachedFiles.length > 0
                ? "Ask anything about the attached course materials..."
                : "Ask a question grounded in course materials..."
            }
            className="w-full bg-transparent border-0 text-xs sm:text-sm text-zinc-900 dark:text-white placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none px-1.5 py-1"
          />

          {/* Bottom Actions Row: + Attachment Button & Send */}
          <div className="flex items-center justify-between pt-2 mt-1 border-t border-zinc-200/60 dark:border-white/[0.04]">
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-8 h-8 rounded-full bg-zinc-200/90 hover:bg-zinc-300 dark:bg-white/[0.08] dark:hover:bg-white/[0.15] text-zinc-700 dark:text-zinc-200 flex items-center justify-center transition-all cursor-pointer shadow-sm hover:scale-105"
                title="Attach PDF syllabus, PNG/JPG diagram, or lecture video"
              >
                <Plus className="w-4 h-4 stroke-[2.5]" />
              </button>

              <span className="text-[11px] text-zinc-400 dark:text-zinc-500 hidden sm:inline pl-1">
                Attach PDF, PNG/JPG diagram, slides, or video
              </span>
            </div>

            <button
              type="submit"
              disabled={!input.trim() && attachedFiles.length === 0}
              className="w-8 h-8 rounded-full bg-black text-white hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 flex items-center justify-center transition-all cursor-pointer shadow-sm disabled:opacity-30 disabled:cursor-not-allowed hover:scale-105"
              title="Send Message"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>

        </div>
      </form>
    </div>
  );
}
