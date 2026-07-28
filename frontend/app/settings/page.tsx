"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Save, Building2, Link2, Bell, Shield, CheckCircle2, Zap } from "lucide-react";
import { toast } from "sonner";
import { fetchWithAuth } from "@/lib/api";

const tabs = [
  { id: "business", label: "Business Profile", icon: Building2 },
  { id: "integrations", label: "Integrations", icon: Link2 },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "security", label: "Security", icon: Shield },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("business");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  
  const [businessData, setBusinessData] = useState({
    name: "",
    email: "",
    phone: "",
    website: "",
    description: "",
    ai_response_mode: "review",
  });

  const [integrations, setIntegrations] = useState<any[]>([]);
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null);
  const [showEmailSetup, setShowEmailSetup] = useState(false);
  const [emailSetup, setEmailSetup] = useState({
    email: "",
    app_password: "",
  });
  const [notifications, setNotifications] = useState({
    new_message: true,
    urgent_sentiment: true,
    ai_draft: false,
    agent_assigned: true,
  });

  // Load business settings
  useEffect(() => {
    const fetchBusiness = async () => {
      try {
        const res = await fetchWithAuth("/api/v1/settings/business");
        if (res.ok) {
          const data = await res.json();
          setBusinessData({
            name: data.name || "",
            email: data.email || "",
            phone: data.phone || "",
            website: data.website || "",
            description: data.description || "",
            ai_response_mode: data.ai_response_mode || "review",
          });
        }
      } catch (e) {
        console.error("Failed to load business profile", e);
      }
    };
    fetchBusiness();
  }, []);

  // Load notification preferences from localStorage
  useEffect(() => {
    const savedPrefs = localStorage.getItem("notificationPrefs");
    if (savedPrefs) {
      try {
        setNotifications(JSON.parse(savedPrefs));
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  // Fetch integrations when tab is active
  useEffect(() => {
    if (activeTab === "integrations") {
      const fetchIntegrations = async () => {
        try {
          const res = await fetchWithAuth("/api/v1/integrations");
          if (res.ok) {
            const data = await res.json();
            setIntegrations(Array.isArray(data.integrations) ? data.integrations : []);
          }
        } catch (e) {
          console.error("Failed to load integrations", e);
        }
      };
      fetchIntegrations();
    }
  }, [activeTab]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetchWithAuth("/api/v1/settings/business", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(businessData),
      });
      if (res.ok) {
        setSaved(true);
        toast.success("Business profile saved successfully");
        setTimeout(() => setSaved(false), 2000);
      } else {
        toast.error("Failed to save settings");
      }
    } catch (e) {
      toast.error("Network error saving settings");
    } finally {
      setSaving(false);
    }
  };

  const toggleNotification = (key: keyof typeof notifications) => {
    setNotifications((prev) => {
      const updated = { ...prev, [key]: !prev[key] };
      localStorage.setItem("notificationPrefs", JSON.stringify(updated));
      return updated;
    });
  };

  const connectPlatform = async (platform: string) => {
    if (platform === "email") {
      setShowEmailSetup(true);
      return;
    }
    setConnectingPlatform(platform);
    try {
      const res = await fetchWithAuth(`/api/v1/integrations/${platform}/connect`);
      const data = await res.json();
      if (!res.ok || !data.auth_url) {
        throw new Error(data.detail || `Could not connect ${platform}`);
      }
      window.location.href = data.auth_url;
    } catch (error: any) {
      toast.error(error.message || `Could not connect ${platform}`);
      setConnectingPlatform(null);
    }
  };

  const configureEmail = async () => {
    setConnectingPlatform("email");
    try {
      const res = await fetchWithAuth("/api/v1/integrations/email/configure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(emailSetup),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Email connection failed");
      setIntegrations(prev => [
        ...prev.filter(item => item.platform !== "email"),
        data,
      ]);
      setEmailSetup({ email: "", app_password: "" });
      setShowEmailSetup(false);
      toast.success("Support email connected");
    } catch (error: any) {
      toast.error(error.message || "Email connection failed");
    } finally {
      setConnectingPlatform(null);
    }
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
                Manage your business profile, AI response automation, and integrations.
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
                  
                  {/* AI Response Automation Mode Card */}
                  <div className="p-5 rounded-2xl border border-[#6D4AE2]/30 bg-gradient-to-r from-[#6D4AE2]/10 to-transparent space-y-3">
                    <div className="flex items-center gap-2">
                      <Zap size={16} className="text-[#818CF8]" />
                      <span className="text-[11px] font-black uppercase tracking-widest text-foreground">AI Response Automation Mode</span>
                    </div>
                    <p className="text-xs text-slate-300">Choose how AI handles incoming customer messages across connected social channels:</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                      <button
                        type="button"
                        onClick={() => setBusinessData(prev => ({ ...prev, ai_response_mode: "review" }))}
                        className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${
                          businessData.ai_response_mode === "review"
                            ? "bg-[#6D4AE2]/20 border-[#818CF8] text-white shadow-md shadow-purple-950/20"
                            : "bg-white/5 border-surface-border text-slate-400 hover:bg-white/10"
                        }`}
                      >
                        <div className="font-bold text-xs flex items-center justify-between">
                          <span>👁️ Review Mode (Manual)</span>
                          {businessData.ai_response_mode === "review" && <CheckCircle2 size={14} className="text-[#818CF8]" />}
                        </div>
                        <span className="text-[10px] text-slate-400 mt-2 block">AI generates draft suggestions. Agents review, edit, and click send.</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setBusinessData(prev => ({ ...prev, ai_response_mode: "auto" }))}
                        className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${
                          businessData.ai_response_mode === "auto"
                            ? "bg-emerald-500/20 border-emerald-400 text-white shadow-md shadow-emerald-950/20"
                            : "bg-white/5 border-surface-border text-slate-400 hover:bg-white/10"
                        }`}
                      >
                        <div className="font-bold text-xs flex items-center justify-between">
                          <span>🚀 Auto AI Mode (Instant)</span>
                          {businessData.ai_response_mode === "auto" && <CheckCircle2 size={14} className="text-emerald-400" />}
                        </div>
                        <span className="text-[10px] text-slate-400 mt-2 block">AI automatically responds to customer queries instantly 24/7 without agent approval.</span>
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Business Name</label>
                      <input
                        type="text"
                        value={businessData.name}
                        onChange={(e) => setBusinessData(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all"
                        placeholder="Your business name"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Business Email</label>
                      <input
                        type="email"
                        value={businessData.email}
                        onChange={(e) => setBusinessData(prev => ({ ...prev, email: e.target.value }))}
                        className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all"
                        placeholder="business@example.com"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Website</label>
                      <input
                        type="text"
                        value={businessData.website}
                        onChange={(e) => setBusinessData(prev => ({ ...prev, website: e.target.value }))}
                        className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all"
                        placeholder="https://yourwebsite.com"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Phone</label>
                      <input
                        type="text"
                        value={businessData.phone}
                        onChange={(e) => setBusinessData(prev => ({ ...prev, phone: e.target.value }))}
                        className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all"
                        placeholder="+977 98XXXXXXXX"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest mb-1.5">Description</label>
                    <textarea
                      rows={3}
                      value={businessData.description}
                      onChange={(e) => setBusinessData(prev => ({ ...prev, description: e.target.value }))}
                      className="w-full px-4 py-3 rounded-2xl border border-surface-border bg-white/5 text-foreground text-sm placeholder-slate-500 focus:border-[#818CF8]/50 focus:bg-white/[0.08] outline-none transition-all resize-none"
                      placeholder="Brief description of your business"
                    />
                  </div>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[11px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-xl shadow-purple-950/20 hover-glow"
                  >
                    {saving ? (
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : saved ? (
                      <CheckCircle2 size={14} />
                    ) : (
                      <Save size={14} />
                    )}
                    {saving ? "Saving..." : saved ? "Saved!" : "Save Changes"}
                  </button>
                </motion.div>
              )}

              {activeTab === "integrations" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                  <h2 className="text-sm font-black uppercase tracking-widest text-foreground mb-6">Connected Platforms</h2>
                  <div className="space-y-4">
                    {["facebook", "instagram", "whatsapp", "email"].map(platform => {
                      const integration = integrations.find(i => i.platform === platform);
                      const isConnected = !!integration && integration.status === "active";
                      const icons: any = {
                        facebook: "📘", instagram: "📸", whatsapp: "📱", email: "📧"
                      };
                      const names: any = {
                        facebook: "Facebook Messenger",
                        instagram: "Instagram Direct",
                        whatsapp: "WhatsApp Business",
                        email: "Email (Gmail IMAP)"
                      };
                      const descs: any = {
                        facebook: "Receive and reply to Messenger messages",
                        instagram: "Manage Instagram DMs from your inbox",
                        whatsapp: "Connect your WhatsApp Business account",
                        email: "Send and receive emails from your custom support address"
                      };
                      return (
                        <div key={platform} className="flex items-center justify-between p-5 rounded-2xl border border-surface-border bg-white/[0.02] hover:bg-white/[0.04] transition-all">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-white/5 border border-surface-border flex items-center justify-center text-xl">
                              {icons[platform]}
                            </div>
                            <div>
                              <p className="text-sm font-bold text-foreground">{names[platform]}</p>
                              {isConnected && integration.page_name ? (
                                <p className="text-[11px] text-gray-400">Connected: {integration.page_name}</p>
                              ) : (
                                <p className="text-[11px]" style={{ color: "var(--muted-foreground)" }}>{descs[platform]}</p>
                              )}
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => connectPlatform(platform)}
                            disabled={connectingPlatform === platform}
                            className={`text-[10px] font-black px-3 py-2 rounded-full border transition-all ${
                            isConnected
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : "bg-[#6D4AE2]/20 text-[#A5B4FC] border-[#6D4AE2]/40 hover:bg-[#6D4AE2]/30"
                          }`}>
                            {connectingPlatform === platform
                              ? "Connecting..."
                              : isConnected
                                ? "Reconnect"
                                : "Connect"}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                  {showEmailSetup && (
                    <div className="mt-5 p-5 rounded-2xl border border-[#6D4AE2]/30 bg-[#6D4AE2]/10 space-y-4">
                      <div>
                        <p className="text-sm font-bold text-foreground">Connect Gmail support inbox</p>
                        <p className="text-[11px] text-slate-400 mt-1">
                          Use a Google App Password, not your normal Gmail password.
                          IMAP must be enabled for this mailbox.
                        </p>
                      </div>
                      <input
                        type="email"
                        value={emailSetup.email}
                        onChange={event => setEmailSetup(prev => ({ ...prev, email: event.target.value }))}
                        placeholder="support@yourbusiness.com"
                        className="w-full px-4 py-3 rounded-xl border border-surface-border bg-white/5 text-sm text-foreground outline-none"
                      />
                      <input
                        type="password"
                        value={emailSetup.app_password}
                        onChange={event => setEmailSetup(prev => ({ ...prev, app_password: event.target.value }))}
                        placeholder="16-character Google App Password"
                        className="w-full px-4 py-3 rounded-xl border border-surface-border bg-white/5 text-sm text-foreground outline-none"
                      />
                      <div className="flex gap-3">
                        <button
                          type="button"
                          onClick={configureEmail}
                          disabled={!emailSetup.email || !emailSetup.app_password || connectingPlatform === "email"}
                          className="px-4 py-2 rounded-xl bg-[#6D4AE2] text-white text-[11px] font-bold disabled:opacity-50"
                        >
                          {connectingPlatform === "email" ? "Validating..." : "Validate & Connect"}
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowEmailSetup(false)}
                          className="px-4 py-2 rounded-xl bg-white/5 text-slate-300 text-[11px] font-bold"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === "notifications" && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                  <h2 className="text-sm font-black uppercase tracking-widest text-foreground mb-6">Notification Preferences</h2>
                  <div className="space-y-3">
                    {[
                      { key: "new_message", label: "New message received", desc: "Get notified when a customer sends a message" },
                      { key: "urgent_sentiment", label: "Urgent sentiment detected", desc: "Alert when BERT detects frustrated customer" },
                      { key: "ai_draft", label: "AI draft generated", desc: "Notify when AI creates a reply suggestion" },
                      { key: "agent_assigned", label: "Agent assigned", desc: "Notify when a conversation is assigned" },
                    ].map((item) => {
                      const isOn = notifications[item.key as keyof typeof notifications];
                      return (
                        <div key={item.key} className="flex items-center justify-between p-4 rounded-2xl border border-surface-border bg-white/[0.02]">
                          <div>
                            <p className="text-sm font-bold text-foreground">{item.label}</p>
                            <p className="text-[11px]" style={{ color: "var(--muted-foreground)" }}>{item.desc}</p>
                          </div>
                          <div
                            onClick={() => toggleNotification(item.key as keyof typeof notifications)}
                            className={`w-10 h-5 rounded-full relative cursor-pointer transition-all ${isOn ? "bg-[#6D4AE2]" : "bg-white/10"}`}
                          >
                            <div className={`w-3.5 h-3.5 bg-white rounded-full absolute top-0.5 transition-all ${isOn ? "right-0.5" : "left-0.5"}`} />
                          </div>
                        </div>
                      );
                    })}
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
