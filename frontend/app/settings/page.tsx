"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Save, Building2, Link2, Bell, Shield, CheckCircle2, Zap } from "lucide-react";

const tabs = [
  { id: "business", label: "Business Profile", icon: Building2 },
  { id: "integrations", label: "Integrations", icon: Link2 },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "security", label: "Security", icon: Shield },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("business");
  const [saved, setSaved] = useState(false);
  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [website, setWebsite] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    setEmail(localStorage.getItem("userEmail") || "");
    setBusinessName(localStorage.getItem("businessName") || "");
  }, []);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="page-padded font-body">
      <div className="page-shell">
        <header className="page-header">
          <div className="page-header-row">
            <div>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-surface-border rounded-lg text-[#818CF8] text-[9px] font-black uppercase tracking-widest mb-4"
              >
                <Zap size={12} strokeWidth={3} />
                Configuration
              </motion.div>
              <h1 className="font-heading font-black tracking-tighter text-4xl sm:text-5xl text-foreground">Settings</h1>
              <p className="text-sm font-medium mt-2" style={{ color: "var(--muted-foreground)" }}>
                Manage your business profile, integrations, and preferences.
              </p>
            </div>
          </div>
        </header>

        <div className="page-body custom-scrollbar">
          <div className="flex flex-col lg:flex-row gap-8">

            {/* Sidebar */}
            <div className="lg:w-56 shrink-0">
              <div className="rounded-[2rem] border border-surface-border bg-white/[0.02] p-3 space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[12px] font-bold transition-all text-left ${
                        activeTab === tab.id
                          ? "bg-[#6D4AE2]/20 text-[#818CF8] border border-[#6D4AE2]/30"
                          : "text-slate-400 hover:bg-white/5 hover:text-white"
                      }`}
                    >
                      <Icon size={15} />
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Content panel */}
            <div className="flex-1 rounded-[2rem] border border-surface-border bg-white/[0.02] p-8">

              {activeTab === "business" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                  <h2 className="text-sm font-black uppercase tracking-widest text-foreground mb-6">Business Profile</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Business Name</label>
                      <input
                        type="text"
                        value={businessName}
                        onChange={(e) => setBusinessName(e.target.value)}
                        className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all"
                        placeholder="Your business name"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Business Email</label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all"
                        placeholder="business@example.com"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Website</label>
                      <input
                        type="text"
                        value={website}
                        onChange={(e) => setWebsite(e.target.value)}
                        className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all"
                        placeholder="https://yourwebsite.com"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Phone</label>
                      <input
                        type="text"
                        className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all"
                        placeholder="+977 98XXXXXXXX"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Description</label>
                    <textarea
                      rows={3}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all resize-none"
                      placeholder="Brief description of your business"
                    />
                  </div>
                  <button
                    onClick={handleSave}
                    className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[11px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-xl shadow-purple-950/20 hover-glow"
                  >
                    {saved ? <CheckCircle2 size={14} /> : <Save size={14} />}
                    {saved ? "Saved!" : "Save Changes"}
                  </button>
                </motion.div>
              )}

              {activeTab === "integrations" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                  <h2 className="text-sm font-black uppercase tracking-widest text-foreground mb-6">Connected Platforms</h2>
                  <div className="space-y-4">
                    {[
                      { name: "Facebook Messenger", icon: "📘", connected: true, desc: "Receive and reply to Messenger messages" },
                      { name: "Instagram Direct", icon: "📸", connected: true, desc: "Manage Instagram DMs from your inbox" },
                      { name: "WhatsApp Business", icon: "📱", connected: false, desc: "Connect your WhatsApp Business account" },
                    ].map((p) => (
                      <div key={p.name} className="flex items-center justify-between p-5 rounded-2xl border border-surface-border bg-white/[0.02] hover:bg-white/[0.04] transition-all">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-xl bg-white/5 border border-surface-border flex items-center justify-center text-xl">
                            {p.icon}
                          </div>
                          <div>
                            <p className="text-sm font-bold text-foreground">{p.name}</p>
                            <p className="text-[11px]" style={{ color: "var(--muted-foreground)" }}>{p.desc}</p>
                          </div>
                        </div>
                        <span className={`text-[10px] font-black px-3 py-1 rounded-full border ${
                          p.connected
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                        }`}>
                          {p.connected ? "Connected" : "Not connected"}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {activeTab === "notifications" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                  <h2 className="text-sm font-black uppercase tracking-widest text-foreground mb-6">Notification Preferences</h2>
                  <div className="space-y-3">
                    {[
                      { label: "New message received", desc: "Get notified when a customer sends a message", on: true },
                      { label: "Urgent sentiment detected", desc: "Alert when BERT detects frustrated customer", on: true },
                      { label: "AI draft generated", desc: "Notify when AI creates a reply suggestion", on: false },
                      { label: "Agent assigned", desc: "Notify when a conversation is assigned", on: true },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center justify-between p-4 rounded-2xl border border-surface-border bg-white/[0.02]">
                        <div>
                          <p className="text-sm font-bold text-foreground">{item.label}</p>
                          <p className="text-[11px]" style={{ color: "var(--muted-foreground)" }}>{item.desc}</p>
                        </div>
                        <div className={`w-10 h-5 rounded-full relative cursor-pointer transition-all ${item.on ? "bg-[#6D4AE2]" : "bg-white/10"}`}>
                          <div className={`w-3.5 h-3.5 bg-white rounded-full absolute top-0.5 transition-all ${item.on ? "right-0.5" : "left-0.5"}`} />
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {activeTab === "security" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
                  <h2 className="text-sm font-black uppercase tracking-widest text-foreground mb-6">Security</h2>
                  <div>
                    <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Current Password</label>
                    <input type="password" className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 outline-none transition-all" placeholder="••••••••" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">New Password</label>
                    <input type="password" className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 outline-none transition-all" placeholder="••••••••" />
                  </div>
                  <div>
                    <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Confirm New Password</label>
                    <input type="password" className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 outline-none transition-all" placeholder="••••••••" />
                  </div>
                  <button className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[11px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-xl shadow-purple-950/20 hover-glow">
                    <Shield size={14} />
                    Update Password
                  </button>
                </motion.div>
              )}

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}