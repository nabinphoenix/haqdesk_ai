"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users, UserPlus, Trash2, X,
  ChevronDown, Clock, MessageCircle,
  CheckCircle2, Zap, Bot, ShieldCheck, Copy, FileCheck2, ScanEye, Timer,
} from "lucide-react";
import { toast } from "sonner";
import { fetchWithAuth } from "@/lib/api";
import ConfirmModal from "@/components/ui/ConfirmModal";

interface TeamMember {
  id: number;
  name: string;
  email: string;
  role: "Admin" | "Agent" | "Supervisor";
  status: "online" | "offline" | "away";
  conversations: number;
  avgResponse: string;
  joinedAt: string;
  responses: number;
}

interface TeamSummary {
  avgResponseSeconds: number | null;
  autoAvgResponseSeconds: number | null;
  reviewAvgResponseSeconds: number | null;
  aiDraftsUsed: number;
  rolesActive: number;
}

const EMPTY_SUMMARY: TeamSummary = {
  avgResponseSeconds: null,
  autoAvgResponseSeconds: null,
  reviewAvgResponseSeconds: null,
  aiDraftsUsed: 0,
  rolesActive: 0,
};

const formatDuration = (seconds: number | null | undefined) => {
  if (seconds === null || seconds === undefined) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  return `${Math.floor(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`;
};

const STATUS_DOT: Record<TeamMember["status"], string> = {
  online: "bg-[var(--success)]",
  offline: "bg-background0",
  away: "bg-amber-400",
};

const STATUS_LABEL: Record<TeamMember["status"], string> = {
  online: "Online",
  offline: "Offline",
  away: "Away",
};

const ROLE_STYLE: Record<TeamMember["role"], string> = {
  Admin: "text-accent-glow bg-accent-glow/10 border-accent-glow/20",
  Supervisor: "text-accent-glow bg-accent/10 border-accent/20",
  Agent: "text-[var(--success-foreground)] bg-[var(--success-surface)] border-[var(--success-border)]",
};

// Map backend role strings to frontend display roles
const mapRole = (role: string): TeamMember["role"] => {
  const map: Record<string, TeamMember["role"]> = {
    business_admin: "Admin",
    super_admin: "Admin",
    supervisor: "Supervisor",
    agent: "Agent",
    Admin: "Admin",
    Supervisor: "Supervisor",
    Agent: "Agent",
  };
  return map[role] || "Agent";
};

export default function TeamPage() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<TeamMember["role"]>("Agent");
  const [inviteSent, setInviteSent] = useState(false);
  const [inviteUrl, setInviteUrl] = useState("");
  const [generatingLink, setGeneratingLink] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [memberToRemove, setMemberToRemove] = useState<TeamMember | null>(null);
  const [isRemovingMember, setIsRemovingMember] = useState(false);
  const [summary, setSummary] = useState<TeamSummary>(EMPTY_SUMMARY);
  const isBusinessAdmin = userRole === "business_admin";

  useEffect(() => {
    setUserRole(localStorage.getItem("userRole"));
  }, []);

  const fetchTeamMetrics = useCallback(async () => {
    try {
      const response = await fetchWithAuth("/api/v1/team/metrics", { cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      setMembers(data.members.map((m: {
        id: number; name?: string; email: string; role: string;
        status?: TeamMember["status"]; conversations?: number;
        avg_response_seconds?: number | null; responses?: number; created_at?: string;
      }) => ({
        id: m.id,
        name: m.name || "Unknown",
        email: m.email,
        role: mapRole(m.role),
        status: m.status || "offline",
        conversations: m.conversations || 0,
        avgResponse: formatDuration(m.avg_response_seconds),
        responses: m.responses || 0,
        joinedAt: m.created_at
          ? new Date(m.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" })
          : "—",
      })));
      const metrics = data.summary || {};
      setSummary({
        avgResponseSeconds: metrics.avg_response_seconds ?? null,
        autoAvgResponseSeconds: metrics.auto_avg_response_seconds ?? null,
        reviewAvgResponseSeconds: metrics.review_avg_response_seconds ?? null,
        aiDraftsUsed: metrics.ai_drafts_used || 0,
        rolesActive: metrics.roles_active || 0,
      });
    } catch (err) {
      console.error("Failed to fetch team metrics", err);
    }
  }, []);

  useEffect(() => {
    fetchTeamMetrics();
    const interval = window.setInterval(fetchTeamMetrics, 15000);
    return () => window.clearInterval(interval);
  }, [fetchTeamMetrics]);

  const onlineCount = members.filter((m) => m.status === "online").length;
  const handleRemove = (id: number) => {
    if (!isBusinessAdmin) return;
    const member = members.find((item) => item.id === id);
    if (member) setMemberToRemove(member);
  };

  const executeRemove = async () => {
    if (!memberToRemove) return;
    setIsRemovingMember(true);
    try {
      const res = await fetchWithAuth(`/api/v1/team/members/${memberToRemove.id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setMembers((prev) => prev.filter((member) => member.id !== memberToRemove.id));
        toast.success(`${memberToRemove.name} was permanently deleted.`);
        setMemberToRemove(null);
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to delete member.");
      }
    } catch {
      toast.error("Cannot connect to server.");
    } finally {
      setIsRemovingMember(false);
    }
  };

  const handleGenerateInviteLink = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inviteEmail.trim()) {
      toast.error("Please enter an email address");
      return;
    }
    setGeneratingLink(true);
    try {
      const res = await fetchWithAuth("/api/v1/team/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: inviteEmail, role: inviteRole.toLowerCase() }),
      });
      const data = await res.json();
      if (res.ok) {
        setInviteUrl(data.invite_url);
        setInviteSent(true);
        if (data.email_sent) {
          toast.success(`Invite email sent to ${inviteEmail}`);
        } else {
          toast.warning("Link generated, but email failed. Share the link manually.");
        }
      } else {
        toast.error(data.detail || "Failed to generate invite");
      }
    } catch {
      toast.error("Network error");
    } finally {
      setGeneratingLink(false);
    }
  };

  const handleCloseInviteModal = () => {
    setShowInviteModal(false);
    setInviteSent(false);
    setInviteEmail("");
    setInviteUrl("");
    setInviteRole("Agent");
  };

  const copyInviteUrl = () => {
    navigator.clipboard.writeText(inviteUrl);
    toast.success("Invite link copied!");
  };

  const stats = [
    { label: "Total Members", value: members.length.toString(), icon: Users, color: "var(--accent-glow)" },
    { label: "Online Now", value: onlineCount.toString(), icon: CheckCircle2, color: "var(--success)" },
    { label: "Avg Response", value: formatDuration(summary.avgResponseSeconds), icon: Timer, color: "var(--teal)" },
    { label: "Auto Mode Avg", value: formatDuration(summary.autoAvgResponseSeconds), icon: Bot, color: "var(--success)" },
    { label: "Review Mode Avg", value: formatDuration(summary.reviewAvgResponseSeconds), icon: ScanEye, color: "var(--warning)" },
    { label: "AI Drafts Used", value: summary.aiDraftsUsed.toLocaleString(), icon: FileCheck2, color: "var(--warning)" },
    { label: "Roles Active", value: summary.rolesActive.toString(), icon: ShieldCheck, color: "var(--accent-glow)" },
  ];

  return (
    <div className="page-padded font-body">
      <ConfirmModal
        isOpen={memberToRemove !== null}
        title="Delete Team Member"
        message={
          memberToRemove
            ? `${memberToRemove.name} will be permanently deleted from this business. Their account access will be removed and this cannot be undone.`
            : ""
        }
        confirmLabel={isRemovingMember ? "Deleting..." : "Delete account"}
        cancelLabel="Cancel"
        onConfirm={executeRemove}
        onCancel={() => setMemberToRemove(null)}
        isDangerous
        isPending={isRemovingMember}
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
                Live
              </motion.div>
              <h1 className="font-heading font-black tracking-tighter text-3xl sm:text-4xl text-foreground">Team</h1>
              <p className="text-sm font-medium mt-1.5" style={{ color: "var(--muted-foreground)" }}>
                Manage your support agents, roles, and access.
              </p>
            </div>
            {isBusinessAdmin && (
              <button
                onClick={() => setShowInviteModal(true)}
                className="flex items-center gap-2.5 px-6 py-3 bg-accent text-on-accent rounded-2xl text-[11px] font-black uppercase tracking-[0.15em] shadow-xl shadow-purple-950/20 hover-glow transition-all active:scale-95"
              >
                <UserPlus size={16} strokeWidth={2.5} />
                Invite Member
              </button>
            )}
          </div>
        </header>

        <div className="page-body custom-scrollbar">

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-7 gap-4 mb-8">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="p-4 rounded-2xl bg-surface-wash border border-surface-border hover:border-accent-glow/20 transition-all group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="p-2 bg-surface-wash border border-surface-border rounded-lg group-hover:bg-accent group-hover:text-on-accent transition-all"
                    style={{ color: stat.color }}
                  >
                    <stat.icon size={14} strokeWidth={2.5} />
                  </div>
                </div>
                <p className="text-[9px] font-black uppercase tracking-[0.25em] mb-1" style={{ color: "var(--muted-foreground)" }}>
                  {stat.label}
                </p>
                <div className="text-xl font-heading font-black tracking-tighter text-foreground">{stat.value}</div>
              </motion.div>
            ))}
          </div>

          {/* Table */}
          <div className="rounded-2xl border border-surface-border overflow-hidden">

            {/* Table header */}
            <div className="grid grid-cols-[2fr_2fr_1fr_1fr_1fr_40px] gap-4 px-6 py-3 bg-surface-wash border-b border-surface-border">
              {["Member", "Email", "Role", "Chats", "Avg. Response", ""].map((h) => (
                <span key={h} className="text-[9px] font-black uppercase tracking-[0.25em] text-muted-foreground">{h}</span>
              ))}
            </div>

            {/* Rows */}
            <AnimatePresence>
              {members.map((member, i) => (
                <motion.div
                  key={member.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 8 }}
                  transition={{ delay: i * 0.04 }}
                  className="grid grid-cols-[2fr_2fr_1fr_1fr_1fr_40px] gap-4 px-6 py-4 border-b border-border hover:bg-surface-wash transition-all items-center group"
                >
                  {/* Name */}
                  <div className="flex items-center gap-3">
                    <div className="relative shrink-0">
                      <div className="w-8 h-8 rounded-full bg-accent/20 border border-accent/30 flex items-center justify-center font-black text-[10px] text-accent-glow">
                        {member.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[var(--surface)] ${STATUS_DOT[member.status]}`} />
                    </div>
                    <div>
                      <p className="text-[13px] font-bold text-foreground leading-tight">{member.name}</p>
                      <p className="text-[9px] font-bold text-muted-foreground uppercase tracking-wider">{STATUS_LABEL[member.status]}</p>
                    </div>
                  </div>

                  {/* Email */}
                  <p className="text-[12px] truncate" style={{ color: "var(--muted-foreground)" }}>{member.email}</p>

                  {/* Role */}
                  <span className={`inline-flex items-center w-fit px-2.5 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-wider border ${ROLE_STYLE[member.role]}`}>
                    {member.role}
                  </span>

                  {/* Conversations */}
                  <div className="flex items-center gap-1.5">
                    <MessageCircle size={11} className="text-muted-foreground shrink-0" />
                    <span className="text-[13px] font-bold text-foreground">{member.conversations}</span>
                  </div>

                  {/* Avg Response */}
                  <div className="flex items-center gap-1.5">
                    <Clock size={11} className="text-muted-foreground shrink-0" />
                    <span className="text-[13px] font-medium text-muted-foreground">{member.avgResponse}</span>
                  </div>

                  {/* Permanent deletion is available only to the business admin and never for another admin. */}
                  {isBusinessAdmin && member.role !== "Admin" && (
                    <button
                      type="button"
                      onClick={() => handleRemove(member.id)}
                      aria-label={`Delete ${member.name}`}
                      title="Delete team member"
                      className="rounded-lg p-1.5 text-muted-foreground opacity-100 transition-all hover:bg-red-950/20 hover:text-[var(--error-foreground)] md:opacity-0 md:group-hover:opacity-100 md:focus-visible:opacity-100"
                    >
                      <Trash2 size={13} strokeWidth={2} aria-hidden="true" />
                    </button>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {members.length === 0 && (
              <div className="py-16 flex flex-col items-center gap-3 text-muted-foreground">
                <Users size={32} strokeWidth={1.5} />
                <p className="text-[11px] font-black uppercase tracking-widest">No team members yet</p>
              </div>
            )}
          </div>

        </div>
      </div>
      {/* Invite Modal */}
      <AnimatePresence>
        {showInviteModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
            onClick={(e) => { if (e.target === e.currentTarget) handleCloseInviteModal(); }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-md rounded-2xl border border-border bg-surface shadow-2xl p-8"
            >
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-lg font-black tracking-tight text-foreground">Invite Member</h2>
                  <p className="text-[12px] mt-0.5" style={{ color: "var(--muted-foreground)" }}>
                    Send an invite to join your support team.
                  </p>
                  <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-accent/20 bg-accent/10 px-3 py-2.5 text-[11px] leading-5 text-muted-foreground">
                    <ShieldCheck size={15} className="mt-0.5 shrink-0 text-accent-glow" />
                    <span><strong className="text-foreground">Secure access:</strong> teammates use their own HaqDesk login. Never share your Instagram, WhatsApp, or Messenger passwords.</span>
                  </div>
                </div>
                <button
                  onClick={handleCloseInviteModal}
                  className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-surface-wash rounded-lg transition-all"
                >
                  <X size={16} />
                </button>
              </div>

              {inviteSent ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="py-6 flex flex-col items-center gap-4 text-[var(--success-foreground)]"
                >
                  <CheckCircle2 size={40} strokeWidth={1.5} />
                  <p className="text-sm font-black uppercase tracking-widest">Invite Sent!</p>
                  {inviteUrl && (
                    <div className="w-full mt-2">
                      <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-2 text-center">Share this link</p>
                      <div className="flex items-center gap-2 p-3 rounded-xl border border-border bg-surface-wash">
                        <input
                          type="text"
                          value={inviteUrl}
                          readOnly
                          className="flex-1 bg-transparent text-[11px] text-muted-foreground outline-none truncate"
                        />
                        <button
                          onClick={copyInviteUrl}
                          className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-surface-wash rounded-lg transition-all"
                          title="Copy link"
                        >
                          <Copy size={14} />
                        </button>
                      </div>
                    </div>
                  )}
                  <button
                    onClick={handleCloseInviteModal}
                    className="mt-2 px-6 py-2 rounded-xl border border-border bg-surface-wash text-foreground text-[11px] font-black uppercase tracking-wider hover:bg-surface-wash transition-all"
                  >
                    Done
                  </button>
                </motion.div>
              ) : (
                <form onSubmit={handleGenerateInviteLink} className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-black text-accent-glow uppercase tracking-widest mb-1.5">Team member email</label>
                    <input
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-border bg-surface-wash text-foreground text-[13px] placeholder:text-muted-foreground focus:border-accent focus:outline-none transition-all"
                      placeholder="agent@example.com"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-black text-accent-glow uppercase tracking-widest mb-1.5">Role</label>
                    <div className="relative">
                      <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value as TeamMember["role"])}
                        className="w-full px-4 py-2.5 rounded-xl border border-border bg-surface-wash text-foreground text-[13px] focus:border-accent focus:outline-none transition-all appearance-none"
                      >
                        <option value="Agent">Agent</option>
                        <option value="Supervisor">Supervisor</option>
                        <option value="Admin">Admin</option>
                      </select>
                      <ChevronDown size={14} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                    </div>
                  </div>

                  <div className="flex gap-3 pt-2">
                    <button
                      type="button"
                      onClick={handleCloseInviteModal}
                      className="flex-1 py-2.5 rounded-xl border border-border bg-surface-wash text-foreground text-[11px] font-black uppercase tracking-wider hover:bg-surface-wash transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={generatingLink}
                      className="flex-1 py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-on-accent text-[11px] font-black uppercase tracking-wider transition-all active:scale-95 disabled:opacity-60 flex items-center justify-center gap-2"
                    >
                      {generatingLink ? (
                        <div className="w-3.5 h-3.5 border-2 border-on-accent border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <>
                          <UserPlus size={13} strokeWidth={2.5} />
                          Send Invite
                        </>
                      )}
                    </button>
                  </div>
                </form>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
