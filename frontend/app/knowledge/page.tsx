"use client";

import { useState, useEffect, useRef } from "react";
import { fetchWithAuth } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import ConfirmModal from "@/components/ui/ConfirmModal";
import { toast } from "sonner";
import {
  FileText, Search, Upload, Database, Plus,
  CheckCircle2, Trash2, X, Bot, AlertCircle,
  BookOpen, ChevronRight, Zap, Eye, Edit3, Save
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
  const [confirmDeleteDocId, setConfirmDeleteDocId] = useState<number | null>(null);
  const [isDeletingDoc, setIsDeletingDoc] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null);
  const isAdmin = userRole === "business_admin" || userRole === "super_admin";

  const [editingDoc, setEditingDoc] = useState<KnowledgeDoc | null>(null);
  const [editingChunks, setEditingChunks] = useState<any[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [savingChunk, setSavingChunk] = useState<number | null>(null);

  const loadDocumentChunks = async (docId: number) => {
    setLoadingChunks(true);
    try {
      const res = await fetchWithAuth(`/api/v1/knowledge/documents/${docId}/chunks`);
      if (res.ok) {
        const data = await res.json();
        setEditingChunks(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingChunks(false);
    }
  };

  const saveChunk = async (chunkId: number, newContent: string) => {
    setSavingChunk(chunkId);
    try {
      const res = await fetchWithAuth(`/api/v1/knowledge/chunks/${chunkId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: newContent }),
      });
      if (res.ok) {
        setEditingChunks((prev) =>
          prev.map((c) => (c.id === chunkId ? { ...c, content: newContent } : c))
        );
        toast.success("Chunk saved and re-indexed");
      } else {
        toast.error("Failed to save chunk");
      }
    } catch (e) {
      toast.error("Network error");
    } finally {
      setSavingChunk(null);
    }
  };

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
    setUserRole(localStorage.getItem("userRole"));
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  const uploadFile = async (file: File) => {
    if (!isAdmin) {
      toast.error("Administrator access required");
      return;
    }
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

  const handleDelete = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setConfirmDeleteDocId(id);
  };

  const executeDeleteDoc = async () => {
    if (confirmDeleteDocId === null) return;
    setIsDeletingDoc(true);
    try {
      const response = await fetchWithAuth(`/api/v1/knowledge/documents/${confirmDeleteDocId}`, { method: "DELETE" });
      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== confirmDeleteDocId));
        if (selectedDoc?.id === confirmDeleteDocId) setSelectedDoc(null);
        toast.success("Document deleted successfully");
      } else {
        toast.error("Failed to delete document.");
      }
    } catch {
      toast.error("Error deleting document. Please try again.");
    } finally {
      setIsDeletingDoc(false);
      setConfirmDeleteDocId(null);
    }
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

      <ConfirmModal
        isOpen={confirmDeleteDocId !== null}
        title="Delete Document"
        message="This document and all its indexed knowledge data will be permanently deleted. This cannot be undone."
        confirmLabel={isDeletingDoc ? "Deleting…" : "Delete Document"}
        cancelLabel="Cancel"
        onConfirm={executeDeleteDoc}
        onCancel={() => setConfirmDeleteDocId(null)}
        isDangerous={true}
        isPending={isDeletingDoc}
      />

      <div className="page-shell">
        {/* Header */}
        <header className="page-header">
          <div className="page-header-row">
            <div>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="inline-flex items-center gap-2 px-3 py-1 bg-surface-wash border border-surface-border rounded-lg text-accent-glow text-[9px] font-black uppercase tracking-widest mb-3"
              >
                <Zap size={12} strokeWidth={3} />
                RAG Knowledge Base
              </motion.div>
              <h1 className="font-heading font-black tracking-tighter text-3xl sm:text-4xl text-foreground">Knowledge Base</h1>
              <p className="text-sm font-medium mt-1.5" style={{ color: "var(--muted-foreground)" }}>
                Upload documents to power your AI reply suggestions.
              </p>
            </div>
            {isAdmin && (
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="flex items-center gap-2.5 px-6 py-3 bg-accent text-on-accent rounded-2xl text-[11px] font-black uppercase tracking-[0.15em] shadow-xl shadow-purple-950/20 hover-glow transition-all active:scale-95 disabled:opacity-50"
              >
                <Upload size={16} strokeWidth={2.5} />
                Upload Document
              </button>
            )}
          </div>

          {/* Search bar */}
          <form onSubmit={handleQuerySubmit} className="relative mt-4 group">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-accent-glow transition-colors" />
            <input
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Ask a question to test your knowledge base..."
              className="w-full bg-surface-wash border border-surface-border pl-10 pr-32 py-3 rounded-2xl text-sm font-medium text-foreground placeholder-slate-500 outline-none transition-all focus:border-accent-glow/40 focus:bg-surface/[0.08]"
            />
            <button
              type="submit"
              disabled={queryLoading || !queryText.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-accent hover:bg-accent-hover text-on-accent rounded-xl text-[10px] font-black uppercase tracking-wider disabled:opacity-40 transition-all flex items-center gap-1.5"
            >
              {queryLoading ? <div className="w-3 h-3 border-2 border-on-accent border-t-transparent rounded-full animate-spin" /> : <Bot size={11} />}
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
                className="mb-5 p-4 bg-red-950/30 border border-red-900/50 text-[var(--error-foreground)] rounded-2xl flex items-center gap-3 text-xs font-semibold"
              >
                <AlertCircle size={15} />
                <span>{uploadError}</span>
                <button onClick={() => setUploadError(null)} className="ml-auto"><X size={15} /></button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Drag overlay */}
          {dragActive && (
            <div className="mb-6 p-10 border-2 border-dashed border-accent-glow/40 bg-accent-glow/5 rounded-[2rem] flex flex-col items-center justify-center text-accent-glow animate-pulse">
              <Upload size={40} className="mb-3" />
              <span className="text-sm font-bold uppercase tracking-wider">Drop file to upload</span>
            </div>
          )}

          {/* Upload progress */}
          {uploading && (
            <div className="mb-6 p-5 bg-surface-wash border border-surface-border rounded-2xl">
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-accent-glow animate-ping" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Uploading and indexing...</span>
                </div>
                <span className="text-xs font-bold text-accent-glow">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-surface-wash h-1.5 rounded-full overflow-hidden">
                <div className="bg-accent h-full rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}

          {/* Two column layout: document list + detail/query panel */}
          <div className="flex flex-col lg:flex-row gap-6">

            {/* LEFT: Document list */}
            <div className="lg:w-[340px] shrink-0 space-y-3">

              {/* Stats bar */}
              <div className="flex items-center justify-between px-1 mb-2">
                <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
                  {documents.length} document{documents.length !== 1 ? "s" : ""}
                </span>
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
                  <span className="text-[10px] font-bold text-[var(--success-foreground)] uppercase tracking-wider">Connected</span>
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
                      ? "border-accent/60 bg-accent/10"
                      : "border-surface-border bg-surface-wash hover:bg-surface/[0.05] hover:border-border"
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    doc.status === "processing" ? "bg-accent/20 text-accent-glow" :
                    doc.status === "failed" ? "bg-[var(--error-surface)] text-[var(--error-foreground)]" :
                    "bg-[var(--success-surface)] text-[var(--success-foreground)]"
                  }`}>
                    <FileText size={18} strokeWidth={2} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-bold text-foreground truncate">{doc.filename}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold">{doc.file_type}</span>
                      <span className="text-muted-foreground">·</span>
                      <span className="text-[10px] text-muted-foreground">{doc.chunks} chunks</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.status === "processing" && <div className="w-3 h-3 border-2 border-accent-glow border-t-transparent rounded-full animate-spin" />}
                    {doc.status === "ready" && <CheckCircle2 size={14} className="text-[var(--success-foreground)]" />}
                    {doc.status === "failed" && <div className="w-3 h-3 rounded-full bg-[var(--error)]" />}
                    {isAdmin && (
                      <button
                        onClick={(e) => handleDelete(doc.id, e)}
                        className="p-1.5 text-muted-foreground hover:text-[var(--error-foreground)] transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                    <ChevronRight size={14} className="text-muted-foreground" />
                  </div>
                </motion.div>
              ))}

              {/* Upload placeholder */}
              {isAdmin && <div
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-4 p-4 rounded-2xl border border-dashed border-surface-border bg-surface/[0.01] hover:border-accent-glow/30 hover:bg-surface/[0.04] transition-all cursor-pointer group"
              >
                <div className="w-10 h-10 rounded-xl border border-surface-border bg-surface-wash flex items-center justify-center text-muted-foreground group-hover:text-accent-glow group-hover:border-accent-glow/30 transition-all">
                  <Plus size={18} />
                </div>
                <span className="text-[12px] font-bold text-muted-foreground group-hover:text-accent-glow transition-colors uppercase tracking-wider">Upload new document</span>
              </div>}
            </div>

            {/* RIGHT: Detail panel or Query result */}
            <div className="flex-1">
              {selectedDoc ? (
                <motion.div
                  key={selectedDoc.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-[2rem] border border-surface-border bg-surface-wash p-7 h-full"
                >
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-accent/20 flex items-center justify-center text-accent-glow">
                        <FileText size={22} strokeWidth={2} />
                      </div>
                      <div>
                        <h2 className="text-base font-black text-foreground">{selectedDoc.filename}</h2>
                        <p className="text-[11px] text-muted-foreground mt-0.5">Uploaded {formatDate(selectedDoc.created_at)}</p>
                      </div>
                    </div>
                    <button onClick={() => setSelectedDoc(null)} className="p-1.5 text-muted-foreground hover:text-foreground transition-colors">
                      <X size={16} />
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mb-6">
                    {[
                      { label: "Status", value: selectedDoc.status, color: selectedDoc.status === "ready" ? "text-[var(--success-foreground)]" : "text-accent-glow" },
                      { label: "Chunks", value: selectedDoc.chunks?.toString() || "—", color: "text-foreground" },
                      { label: "File type", value: selectedDoc.file_type?.toUpperCase() || "—", color: "text-foreground" },
                    ].map((s) => (
                      <div key={s.label} className="p-4 rounded-xl bg-surface-wash border border-surface-border text-center">
                        <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground mb-1">{s.label}</p>
                        <p className={`text-sm font-black ${s.color} capitalize`}>{s.value}</p>
                      </div>
                    ))}
                  </div>

                  <div className="p-4 rounded-xl bg-surface-wash border border-surface-border mb-5">
                    <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-2">File Size</p>
                    <p className="text-sm font-bold text-foreground">{formatFileSize(selectedDoc.file_size)}</p>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() => { setQueryText(""); setSelectedDoc(null); }}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-accent/20 hover:bg-accent/30 text-accent-glow text-[11px] font-black uppercase tracking-wider transition-all"
                    >
                      <Bot size={13} />
                      Test with AI
                    </button>
                    {isAdmin && (
                      <>
                        <button
                          onClick={() => { setEditingDoc(selectedDoc); loadDocumentChunks(selectedDoc.id); }}
                          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-wash hover:bg-surface-wash border border-border text-foreground text-[11px] font-black uppercase tracking-wider transition-all"
                        >
                          <Edit3 size={13} />
                          Edit Content
                        </button>
                        <button
                          onClick={(e) => handleDelete(selectedDoc.id, e)}
                          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[var(--error-surface)] hover:bg-[var(--error-surface)] text-[var(--error-foreground)] text-[11px] font-black uppercase tracking-wider transition-all"
                        >
                          <Trash2 size={13} />
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </motion.div>
              ) : queryResult ? (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-[2rem] border border-surface-border bg-surface-wash p-7"
                >
                  <div className="flex items-center justify-between mb-5">
                    <h3 className="text-sm font-black uppercase tracking-widest text-foreground">AI Response</h3>
                    <button onClick={() => setQueryResult(null)} className="p-1.5 text-muted-foreground hover:text-foreground transition-colors">
                      <X size={15} />
                    </button>
                  </div>
                  <div className="flex items-center gap-3 mb-5">
                    <span className="text-[10px] font-black px-2.5 py-1 bg-[var(--success-surface)] border border-[var(--success-border)] text-[var(--success-foreground)] rounded-lg uppercase tracking-wider">
                      Confidence: {Math.round(queryResult.confidence * 100)}%
                    </span>
                    <span className="text-[10px] font-black px-2.5 py-1 bg-accent/10 border border-accent-glow/20 text-accent-glow rounded-lg uppercase tracking-wider">
                      {queryResult.chunks_used} chunks matched
                    </span>
                  </div>
                  <div className="p-5 bg-gradient-to-br from-accent/10 to-transparent border border-accent/20 rounded-2xl text-sm leading-relaxed text-on-accent mb-5">
                    {queryResult.answer}
                  </div>
                  {queryResult.sources.length > 0 && (
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-2">Sources</p>
                      <div className="flex flex-wrap gap-2">
                        {queryResult.sources.map((src, i) => (
                          <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-wash border border-surface-border rounded-lg text-[10px] font-bold text-muted-foreground">
                            <BookOpen size={10} className="text-accent-glow" />
                            {src}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              ) : (
                <div className="h-full min-h-[300px] rounded-[2rem] border border-dashed border-surface-border flex flex-col items-center justify-center gap-4 text-muted-foreground">
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
            <div className="mt-6 p-6 rounded-2xl border border-surface-border bg-surface-wash flex items-center gap-4">
              <div className="w-6 h-6 border-2 border-accent-glow border-t-transparent rounded-full animate-spin shrink-0" />
              <span className="text-[11px] font-black uppercase tracking-widest text-muted-foreground">Searching knowledge base...</span>
            </div>
          )}

        </div>
      </div>

      {/* Chunk Editor Modal */}
      <AnimatePresence>
        {editingDoc && (
          <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
            <div className="w-full max-w-3xl max-h-[85vh] rounded-2xl border border-border bg-surface shadow-2xl flex flex-col overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-5 border-b border-border">
                <div>
                  <h2 className="text-base font-black text-foreground">Edit Document Content</h2>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{editingDoc.filename} — {editingChunks.length} chunks</p>
                </div>
                <button
                  onClick={() => { setEditingDoc(null); setEditingChunks([]); }}
                  className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-surface-wash rounded-lg transition-all"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Chunk list */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                {loadingChunks ? (
                  <div className="flex justify-center py-12">
                    <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : editingChunks.length === 0 ? (
                  <p className="text-xs text-center text-muted-foreground py-8">No chunks found in this document.</p>
                ) : (
                  editingChunks.map((chunk, idx) => (
                    <ChunkEditor
                      key={chunk.id}
                      chunk={chunk}
                      index={idx}
                      saving={savingChunk === chunk.id}
                      onSave={(newContent) => saveChunk(chunk.id, newContent)}
                    />
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ChunkEditor({ chunk, index, saving, onSave }: {
  chunk: any;
  index: number;
  saving: boolean;
  onSave: (content: string) => void;
}) {
  const [content, setContent] = useState(chunk.content);
  const [isDirty, setIsDirty] = useState(false);

  return (
    <div className="rounded-xl border border-border bg-surface-wash p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
          Chunk {index + 1} · Page {chunk.page_number || "?"}
        </span>
        {isDirty && (
          <button
            onClick={() => { onSave(content); setIsDirty(false); }}
            disabled={saving}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-accent hover:bg-accent-hover text-on-accent text-[10px] font-black uppercase tracking-wider transition-all disabled:opacity-60"
          >
            {saving ? (
              <div className="w-3 h-3 border-2 border-on-accent border-t-transparent rounded-full animate-spin" />
            ) : (
              <Save size={11} />
            )}
            {saving ? "Saving..." : "Save & Re-index"}
          </button>
        )}
      </div>
      <textarea
        value={content}
        onChange={(e) => { setContent(e.target.value); setIsDirty(e.target.value !== chunk.content); }}
        rows={4}
        className="w-full bg-surface-wash border border-border rounded-lg px-3 py-2 text-[12px] text-foreground focus:border-accent focus:outline-none resize-y transition-all"
      />
      {isDirty && (
        <p className="text-[10px] text-[var(--warning)] mt-1">
          ⚠ Unsaved changes — save to re-index this chunk in the RAG system
        </p>
      )}
    </div>
  );
}
