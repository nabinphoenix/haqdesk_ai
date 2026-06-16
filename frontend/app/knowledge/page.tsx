"use client";

import { useState, useEffect, useRef } from "react";
import { fetchWithAuth } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText, Search, Upload, Database, Plus,
  CheckCircle2, Trash2, X, Bot, AlertCircle,
  BookOpen, ChevronRight, Zap, Eye,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface KnowledgeDoc {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: "processing" | "ready" | "failed";
  chunks: number;
  created_at: string;
}

interface QueryResult {
  answer: string;
  confidence: number;
  sources: string[];
  chunks_used: number;
}

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState<KnowledgeDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDoc | null>(null);
  const [queryText, setQueryText] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    try {
      const response = await fetchWithAuth("/api/v1/knowledge/documents");
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (error) {
      console.error("Failed to fetch documents:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  const uploadFile = async (file: File) => {
    const allowedExtensions = ["pdf", "docx", "txt"];
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !allowedExtensions.includes(ext)) {
      setUploadError("Unsupported file type. Please upload a PDF, DOCX, or TXT file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("File too large. Maximum size is 10 MB.");
      return;
    }
    setUploading(true);
    setUploadProgress(10);
    setUploadError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      setUploadProgress(30);
      const response = await fetchWithAuth(
        "/api/v1/knowledge/upload",
        { method: "POST", body: formData }
      );
      setUploadProgress(70);
      if (response.ok) {
        setUploadProgress(100);
        setTimeout(() => { setUploading(false); setUploadProgress(0); fetchDocuments(); }, 800);
      } else {
        const errData = await response.json();
        setUploadError(errData.detail || "Failed to upload document.");
        setUploading(false);
      }
    } catch {
      setUploadError("Network error. Failed to reach server.");
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) uploadFile(e.target.files[0]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) uploadFile(e.dataTransfer.files[0]);
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this document and all its indexed data?")) return;
    try {
      const response = await fetchWithAuth(`/api/v1/knowledge/documents/${id}`, { method: "DELETE" });
      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== id));
        if (selectedDoc?.id === id) setSelectedDoc(null);
      }
    } catch { alert("Error deleting document."); }
  };

  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) return;
    setQueryLoading(true);
    setQueryResult(null);
    try {
      const response = await fetchWithAuth(`/api/v1/knowledge/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: queryText }),
      });
      if (response.ok) setQueryResult(await response.json());
    } catch { console.error("Query failed"); }
    finally { setQueryLoading(false); }
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return "—";
    const k = 1024;
    const sizes = ["B", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  return (
    <div className="page-padded font-body">
      <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".pdf,.docx,.txt" className="hidden" />

      <div className="page-shell">
        {/* Header */}
        <header className="page-header">
          <div className="page-header-row">
            <div>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-surface-border rounded-lg text-[#818CF8] text-[9px] font-black uppercase tracking-widest mb-3"
              >
                <Zap size={12} strokeWidth={3} />
                RAG Knowledge Base
              </motion.div>
              <h1 className="font-heading font-black tracking-tighter text-3xl sm:text-4xl text-foreground">Knowledge Base</h1>
              <p className="text-sm font-medium mt-1.5" style={{ color: "var(--muted-foreground)" }}>
                Upload documents to power your AI reply suggestions.
              </p>
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="flex items-center gap-2.5 px-6 py-3 bg-[#6D4AE2] text-white rounded-2xl text-[11px] font-black uppercase tracking-[0.15em] shadow-xl shadow-purple-950/20 hover-glow transition-all active:scale-95 disabled:opacity-50"
            >
              <Upload size={16} strokeWidth={2.5} />
              Upload Document
            </button>
          </div>

          {/* Search bar */}
          <form onSubmit={handleQuerySubmit} className="relative mt-4 group">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#818CF8] transition-colors" />
            <input
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Ask a question to test your knowledge base..."
              className="w-full bg-white/5 border border-surface-border pl-10 pr-32 py-3 rounded-2xl text-sm font-medium text-foreground placeholder-slate-500 outline-none transition-all focus:border-[#818CF8]/40 focus:bg-white/[0.08]"
            />
            <button
              type="submit"
              disabled={queryLoading || !queryText.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white rounded-xl text-[10px] font-black uppercase tracking-wider disabled:opacity-40 transition-all flex items-center gap-1.5"
            >
              {queryLoading ? <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Bot size={11} />}
              {queryLoading ? "..." : "Test"}
            </button>
          </form>
        </header>

        <div
          className="page-body custom-scrollbar"
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
        >
          {/* Error */}
          <AnimatePresence>
            {uploadError && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-5 p-4 bg-red-950/30 border border-red-900/50 text-red-400 rounded-2xl flex items-center gap-3 text-xs font-semibold"
              >
                <AlertCircle size={15} />
                <span>{uploadError}</span>
                <button onClick={() => setUploadError(null)} className="ml-auto"><X size={15} /></button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Drag overlay */}
          {dragActive && (
            <div className="mb-6 p-10 border-2 border-dashed border-[#818CF8]/40 bg-[#818CF8]/5 rounded-[2rem] flex flex-col items-center justify-center text-[#818CF8] animate-pulse">
              <Upload size={40} className="mb-3" />
              <span className="text-sm font-bold uppercase tracking-wider">Drop file to upload</span>
            </div>
          )}

          {/* Upload progress */}
          {uploading && (
            <div className="mb-6 p-5 bg-white/5 border border-surface-border rounded-2xl">
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[#818CF8] animate-ping" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">Uploading and indexing...</span>
                </div>
                <span className="text-xs font-bold text-[#818CF8]">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#6D4AE2] h-full rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}

          {/* Two column layout: document list + detail/query panel */}
          <div className="flex flex-col lg:flex-row gap-6">

            {/* LEFT: Document list */}
            <div className="lg:w-[340px] shrink-0 space-y-3">

              {/* Stats bar */}
              <div className="flex items-center justify-between px-1 mb-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  {documents.length} document{documents.length !== 1 ? "s" : ""}
                </span>
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Connected</span>
                </div>
              </div>

              {/* Document cards */}
              {documents.map((doc, i) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => setSelectedDoc(doc)}
                  className={`flex items-center gap-4 p-4 rounded-2xl border cursor-pointer transition-all group ${
                    selectedDoc?.id === doc.id
                      ? "border-[#6D4AE2]/60 bg-[#6D4AE2]/10"
                      : "border-surface-border bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/20"
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    doc.status === "processing" ? "bg-[#6D4AE2]/20 text-[#818CF8]" :
                    doc.status === "failed" ? "bg-red-500/20 text-red-400" :
                    "bg-emerald-500/10 text-emerald-400"
                  }`}>
                    <FileText size={18} strokeWidth={2} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-bold text-foreground truncate">{doc.filename}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-slate-500 uppercase font-bold">{doc.file_type}</span>
                      <span className="text-slate-600">·</span>
                      <span className="text-[10px] text-slate-500">{doc.chunks} chunks</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.status === "processing" && <div className="w-3 h-3 border-2 border-[#818CF8] border-t-transparent rounded-full animate-spin" />}
                    {doc.status === "ready" && <CheckCircle2 size={14} className="text-emerald-400" />}
                    {doc.status === "failed" && <div className="w-3 h-3 rounded-full bg-red-500" />}
                    <button
                      onClick={(e) => handleDelete(doc.id, e)}
                      className="p-1.5 text-slate-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 size={13} />
                    </button>
                    <ChevronRight size={14} className="text-slate-600" />
                  </div>
                </motion.div>
              ))}

              {/* Upload placeholder */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-4 p-4 rounded-2xl border border-dashed border-surface-border bg-white/[0.01] hover:border-[#818CF8]/30 hover:bg-white/[0.04] transition-all cursor-pointer group"
              >
                <div className="w-10 h-10 rounded-xl border border-surface-border bg-white/5 flex items-center justify-center text-slate-500 group-hover:text-[#818CF8] group-hover:border-[#818CF8]/30 transition-all">
                  <Plus size={18} />
                </div>
                <span className="text-[12px] font-bold text-slate-500 group-hover:text-[#818CF8] transition-colors uppercase tracking-wider">Upload new document</span>
              </div>
            </div>

            {/* RIGHT: Detail panel or Query result */}
            <div className="flex-1">
              {selectedDoc ? (
                <motion.div
                  key={selectedDoc.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-[2rem] border border-surface-border bg-white/[0.02] p-7 h-full"
                >
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-[#6D4AE2]/20 flex items-center justify-center text-[#818CF8]">
                        <FileText size={22} strokeWidth={2} />
                      </div>
                      <div>
                        <h2 className="text-base font-black text-foreground">{selectedDoc.filename}</h2>
                        <p className="text-[11px] text-slate-500 mt-0.5">Uploaded {formatDate(selectedDoc.created_at)}</p>
                      </div>
                    </div>
                    <button onClick={() => setSelectedDoc(null)} className="p-1.5 text-slate-500 hover:text-white transition-colors">
                      <X size={16} />
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mb-6">
                    {[
                      { label: "Status", value: selectedDoc.status, color: selectedDoc.status === "ready" ? "text-emerald-400" : "text-[#818CF8]" },
                      { label: "Chunks", value: selectedDoc.chunks?.toString() || "—", color: "text-foreground" },
                      { label: "File type", value: selectedDoc.file_type?.toUpperCase() || "—", color: "text-foreground" },
                    ].map((s) => (
                      <div key={s.label} className="p-4 rounded-xl bg-white/[0.03] border border-surface-border text-center">
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-1">{s.label}</p>
                        <p className={`text-sm font-black ${s.color} capitalize`}>{s.value}</p>
                      </div>
                    ))}
                  </div>

                  <div className="p-4 rounded-xl bg-white/[0.02] border border-surface-border mb-5">
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">File Size</p>
                    <p className="text-sm font-bold text-foreground">{formatFileSize(selectedDoc.file_size)}</p>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() => { setQueryText(""); setSelectedDoc(null); }}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#6D4AE2]/20 hover:bg-[#6D4AE2]/30 text-[#818CF8] text-[11px] font-black uppercase tracking-wider transition-all"
                    >
                      <Bot size={13} />
                      Test with AI
                    </button>
                    <button
                      onClick={(e) => handleDelete(selectedDoc.id, e)}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[11px] font-black uppercase tracking-wider transition-all"
                    >
                      <Trash2 size={13} />
                      Delete
                    </button>
                  </div>
                </motion.div>
              ) : queryResult ? (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-[2rem] border border-surface-border bg-white/[0.02] p-7"
                >
                  <div className="flex items-center justify-between mb-5">
                    <h3 className="text-sm font-black uppercase tracking-widest text-foreground">AI Response</h3>
                    <button onClick={() => setQueryResult(null)} className="p-1.5 text-slate-500 hover:text-white transition-colors">
                      <X size={15} />
                    </button>
                  </div>
                  <div className="flex items-center gap-3 mb-5">
                    <span className="text-[10px] font-black px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg uppercase tracking-wider">
                      Confidence: {Math.round(queryResult.confidence * 100)}%
                    </span>
                    <span className="text-[10px] font-black px-2.5 py-1 bg-[#6D4AE2]/10 border border-[#818CF8]/20 text-[#818CF8] rounded-lg uppercase tracking-wider">
                      {queryResult.chunks_used} chunks matched
                    </span>
                  </div>
                  <div className="p-5 bg-gradient-to-br from-[#6D4AE2]/10 to-transparent border border-[#6D4AE2]/20 rounded-2xl text-sm leading-relaxed text-slate-200 mb-5">
                    {queryResult.answer}
                  </div>
                  {queryResult.sources.length > 0 && (
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Sources</p>
                      <div className="flex flex-wrap gap-2">
                        {queryResult.sources.map((src, i) => (
                          <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 border border-surface-border rounded-lg text-[10px] font-bold text-slate-300">
                            <BookOpen size={10} className="text-[#818CF8]" />
                            {src}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              ) : (
                <div className="h-full min-h-[300px] rounded-[2rem] border border-dashed border-surface-border flex flex-col items-center justify-center gap-4 text-slate-600">
                  <Eye size={36} strokeWidth={1.5} />
                  <div className="text-center">
                    <p className="text-[12px] font-black uppercase tracking-widest mb-1">Select a document</p>
                    <p className="text-[11px]">or ask a question to test the AI</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Query loading state */}
          {queryLoading && (
            <div className="mt-6 p-6 rounded-2xl border border-surface-border bg-white/[0.02] flex items-center gap-4">
              <div className="w-6 h-6 border-2 border-[#818CF8] border-t-transparent rounded-full animate-spin shrink-0" />
              <span className="text-[11px] font-black uppercase tracking-widest text-slate-400">Searching knowledge base...</span>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}