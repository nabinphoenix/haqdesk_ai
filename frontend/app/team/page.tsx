"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users, UserPlus, Trash2, X, Mail,
  ChevronDown, Clock, MessageCircle,
  CheckCircle2, Zap, Bot, Shield, Copy, ExternalLink,
} from "lucide-react";
import { toast } from "sonner";

interface TeamMember {
  id: number;
  name: string;
  email: string;
  role: "Admin" | "Agent" | "Supervisor";
  status: "online" | "offline" | "away";
  conversations: number;
  avgResponse: string;
  joinedAt: string;
}

const STATUS_DOT: Record<TeamMember["status"], string> = {
  online: "bg-emerald-500",
  offline: "bg-slate-500",
  away: "bg-amber-400",
};

const STATUS_LABEL: Record<TeamMember["status"], string> = {
  online: "Online",
  offline: "Offline",
  away: "Away",
};

const ROLE_STYLE: Record<TeamMember["role"], string> = {
  Admin: "text-[#818CF8] bg-[#818CF8]/10 border-[#818CF8]/20",
  Supervisor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
  Agent: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
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

  // Fetch team members from API on mount
  useEffect(() => {
    const fetchMembers = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) return;
        const res = await fetch("http://localhost:8000/api/v1/team/members", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setMembers(
            data.map((m: any) => ({
              id: m.id,
              name: m.name || "Unknown",
              email: m.email,
              role: mapRole(m.role),
              status: (m.status as TeamMember["status"]) || "offline",
              conversations: 0,
              avgResponse: "—",
              joinedAt: m.created_at
                ? new Date(m.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" })
                : "—",
            }))
          );
        }
      } catch {
        // Silently fail — members will stay empty
      }
    };
    fetchMembers();
  }, []);

  const onlineCount = members.filter((m) => m.status === "online").length;

  const handleRemove = async (id: number) => {
    const member = members.find((m) => m.id === id);
    if (!member) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/api/v1/team/members/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setMembers((prev) => prev.filter((m) => m.id !== id));
        toast.success(`Removed ${member.name} from the team.`);
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to remove member.");
      }
    } catch {
      toast.error("Cannot connect to server.");
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/v1/team/invite", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
      });

      const data = await res.json();

      if (res.ok) {
        setInviteSent(true);
        setInviteUrl(data.invite_url || "");
        toast.success(`Invite sent to ${inviteEmail}`);
      } else {
        toast.error(data.detail || "Failed to send invitation.");
      }
    } catch {
      toast.error("Cannot connect to server.");
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

  const roleCount = new Set(members.map((m) => m.role)).size;

  const stats = [
    { label: "Total Members", value: members.length.toString(), icon: Users, color: "#818CF8" },
    { label: "Online Now", value: onlineCount.toString(), icon: CheckCircle2, color: "#10B981" },
    { label: "Avg Response", value: "—", icon: Clock, color: "#06B6D4" },
    { label: "AI Drafts Used", value: "—", icon: Bot, color: "#F59E0B" },
    { label: "Roles Active", value: roleCount.toString(), icon: Shield, color: "#818CF8" },
  ];

  return (
    <div className="page-padded font-body">
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
                Live
              </motion.div>
              <h1 className="font-heading font-black tracking-tighter text-3xl sm:text-4xl text-foreground">Team</h1>
              <p className="text-sm font-medium mt-1.5" style={{ color: "var(--muted-foreground)" }}>
                Manage your support agents, roles, and access.
              </p>
            </div>
            <button
              onClick={() => setShowInviteModal(true)}
              className="flex items-center gap-2.5 px-6 py-3 bg-[#6D4AE2] text-white rounded-2xl text-[11px] font-black uppercase tracking-[0.15em] shadow-xl shadow-purple-950/20 hover-glow transition-all active:scale-95"
            >
              <UserPlus size={16} strokeWidth={2.5} />
              Invite Member
            </button>
          </div>
        </header>

        <div className="page-body custom-scrollbar">

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="p-4 rounded-2xl bg-white/5 border border-surface-border hover:border-[#818CF8]/20 transition-all group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="p-2 bg-white/5 border border-surface-border rounded-lg group-hover:bg-[#6D4AE2] group-hover:text-white transition-all"
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
            <div className="grid grid-cols-[2fr_2fr_1fr_1fr_1fr_40px] gap-4 px-6 py-3 bg-white/[0.02] border-b border-surface-border">
              {["Member", "Email", "Role", "Chats", "Avg. Response", ""].map((h) => (
                <span key={h} className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500">{h}</span>
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
                  className="grid grid-cols-[2fr_2fr_1fr_1fr_1fr_40px] gap-4 px-6 py-4 border-b border-white/[0.04] hover:bg-white/[0.02] transition-all items-center group"
                >
                  {/* Name */}
                  <div className="flex items-center gap-3">
                    <div className="relative shrink-0">
                      <div className="w-8 h-8 rounded-full bg-[#6D4AE2]/20 border border-[#6D4AE2]/30 flex items-center justify-center font-black text-[10px] text-[#818CF8]">
                        {member.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[var(--surface)] ${STATUS_DOT[member.status]}`} />
                    </div>
                    <div>
                      <p className="text-[13px] font-bold text-foreground leading-tight">{member.name}</p>
                      <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">{STATUS_LABEL[member.status]}</p>
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
                    <MessageCircle size={11} className="text-slate-500 shrink-0" />
                    <span className="text-[13px] font-bold text-foreground">{member.conversations}</span>
                  </div>

                  {/* Avg Response */}
                  <div className="flex items-center gap-1.5">
                    <Clock size={11} className="text-slate-500 shrink-0" />
                    <span className="text-[13px] font-medium text-slate-300">{member.avgResponse}</span>
                  </div>

                  {/* Remove */}
                  <button
                    onClick={() => handleRemove(member.id)}
                    className="p-1.5 text-slate-600 hover:text-red-400 hover:bg-red-950/20 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={13} strokeWidth={2} />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>

            {members.length === 0 && (
              <div className="py-16 flex flex-col items-center gap-3 text-slate-500">
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
              className="w-full max-w-md rounded-2xl border border-white/10 bg-[#1a1a2e] shadow-2xl p-8"
            >
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-lg font-black tracking-tight text-white">Invite Member</h2>
                  <p className="text-[12px] mt-0.5" style={{ color: "var(--muted-foreground)" }}>
                    Send an invite to join your support team.
                  </p>
                </div>
                <button
                  onClick={handleCloseInviteModal}
                  className="p-1.5 text-slate-500 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                >
                  <X size={16} />
                </button>
              </div>

              {inviteSent ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="py-6 flex flex-col items-center gap-4 text-emerald-400"
                >
                  <CheckCircle2 size={40} strokeWidth={1.5} />
                  <p className="text-sm font-black uppercase tracking-widest">Invite Sent!</p>
                  {inviteUrl && (
                    <div className="w-full mt-2">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 text-center">Share this link</p>
                      <div className="flex items-center gap-2 p-3 rounded-xl border border-white/10 bg-white/5">
                        <input
                          type="text"
                          value={inviteUrl}
                          readOnly
                          className="flex-1 bg-transparent text-[11px] text-slate-300 outline-none truncate"
                        />
                        <button
                          onClick={copyInviteUrl}
                          className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                          title="Copy link"
                        >
                          <Copy size={14} />
                        </button>
                      </div>
                    </div>
                  )}
                  <button
                    onClick={handleCloseInviteModal}
                    className="mt-2 px-6 py-2 rounded-xl border border-white/10 bg-white/5 text-white text-[11px] font-black uppercase tracking-wider hover:bg-white/10 transition-all"
                  >
                    Done
                  </button>
                </motion.div>
              ) : (
                <form onSubmit={handleInvite} className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Email Address</label>
                    <div className="relative">
                      <Mail size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                      <input
                        type="email"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="colleague@example.com"
                        className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-slate-600 focus:border-purple-500 focus:outline-none transition-all"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Role</label>
                    <div className="relative">
                      <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value as TeamMember["role"])}
                        className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] focus:border-purple-500 focus:outline-none transition-all appearance-none"
                      >
                        <option value="Agent">Agent</option>
                        <option value="Supervisor">Supervisor</option>
                        <option value="Admin">Admin</option>
                      </select>
                      <ChevronDown size={14} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
                    </div>
                  </div>

                  <div className="flex gap-3 pt-2">
                    <button
                      type="button"
                      onClick={handleCloseInviteModal}
                      className="flex-1 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-[11px] font-black uppercase tracking-wider hover:bg-white/10 transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="flex-1 py-2.5 rounded-xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[11px] font-black uppercase tracking-wider transition-all active:scale-95 flex items-center justify-center gap-2"
                    >
                      <UserPlus size={13} strokeWidth={2.5} />
                      Send Invite
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
