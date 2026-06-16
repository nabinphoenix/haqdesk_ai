"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Zap,
  ArrowRight,
  MessageSquare,
  BookOpen,
  Cpu,
  Database,
  LineChart,
  User,
  UserRound,
} from "lucide-react";

export default function Home() {
  const mockConversations = [
    {
      id: 1,
      name: "Raman Shrestha",
      message: "Why the payment is failing?",
      time: "2m ago",
      gender: "male",
      unread: true,
    },
    {
      id: 2,
      name: "Sita Thapa",
      message: "Yo Kurta ko kati price ho?",
      time: "15m ago",
      gender: "female",
      unread: false,
    },
    {
      id: 3,
      name: "Hari Maharjan",
      message: "Thank you for fast assist!",
      time: "1h ago",
      gender: "male",
      unread: false,
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto font-body custom-scrollbar bg-white dark:bg-[#090514]">

      {/* HERO SECTION */}
      <section className="w-full min-h-screen flex items-center">
        <div className="mx-auto w-full max-w-screen-xl px-[10%]">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-12 relative">

            {/* Background orbs */}
            <div className="absolute top-0 right-0 w-72 h-72 bg-[#6D4AE2]/10 rounded-full blur-3xl -z-10 translate-x-1/2 -translate-y-1/2" />
            <div className="absolute bottom-0 left-0 w-56 h-56 bg-cyan-400/8 rounded-full blur-3xl -z-10 -translate-x-1/2 translate-y-1/2" />

            {/* LEFT COLUMN */}
            <div className="w-full lg:w-[55%] flex flex-col space-y-6">
              <span className="inline-block bg-[#EDE9FE] dark:bg-[#6D4AE2]/20 text-[#6D4AE2] dark:text-[#818CF8] rounded-full px-4 py-1 text-sm font-medium self-start">
                ✦ AI-POWERED SUPPORT
              </span>
              <h1
                className="font-heading font-extrabold tracking-tight leading-[1.06] text-slate-900 dark:text-white"
                style={{ fontSize: "clamp(38px, 4.5vw, 56px)", letterSpacing: "-0.03em" }}
              >
                All Your Customer Chats.
                <span className="block">
                  <span style={{ color: "var(--accent)" }}>One</span>
                  {" "}Smart{" "}
                  <span style={{ color: "var(--teal, #0f9b72)" }}>Inbox.</span>
                </span>
              </h1>
              <p
                className="text-[15.5px] font-light leading-[1.75] max-w-[440px] mt-5 mb-8"
                style={{ color: "var(--muted-foreground)" }}
              >
                HaqDesk AI brings together all your conversations from Instagram, WhatsApp,
                and Messenger into a single, intelligent inbox. Respond faster with
                AI-powered suggestions — no credit card required.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
                <Link
                  href="/inbox"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-[9px] text-[14px] font-medium text-white transition-all duration-150 hover:-translate-y-px active:translate-y-0 shadow-lg shadow-purple-900/10"
                  style={{ background: "var(--accent)" }}
                >
                  Open Inbox
                  <ArrowRight size={16} />
                </Link>
                <Link
                  href="/demo"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-[9px] text-[14px] font-normal transition-all duration-150 hover:bg-black/5 dark:hover:bg-white/5"
                  style={{ color: "var(--foreground)", border: "0.5px solid var(--nav-border)" }}
                >
                  Watch Demo
                </Link>
              </div>
              <div className="flex items-center gap-5 mt-5 flex-wrap">
                {["Free to start", "No credit card", "Setup in 2 min"].map((label) => (
                  <span
                    key={label}
                    className="flex items-center gap-1.5 text-[12.5px]"
                    style={{ color: "var(--muted-foreground)" }}
                  >
                    <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.8" style={{ color: "var(--teal)" }}>
                      <path d="M2 6.5L5.5 10 11 3" />
                    </svg>
                    {label}
                  </span>
                ))}
              </div>
            </div>

            {/* RIGHT COLUMN - inbox preview card */}
            <div className="w-full lg:w-[45%] flex justify-center lg:justify-end">
              <div className="w-full max-w-md rounded-2xl border border-gray-200 dark:border-white/10 bg-white dark:bg-[#1a1a2e] shadow-2xl overflow-hidden">
                {/* Card header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-white/10">
                  <span className="text-xs font-bold uppercase tracking-widest text-gray-500 dark:text-gray-400">
                    INBOX
                  </span>
                  <span className="text-xs font-semibold text-white bg-[#6D4AE2] rounded-full px-2 py-0.5">
                    3 new
                  </span>
                </div>

                {/* Conversation list */}
                {mockConversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`flex items-center gap-3 px-4 py-3 border-b border-gray-100 dark:border-white/5 ${
                      conv.unread ? "bg-purple-50 dark:bg-purple-900/10 border-l-2 border-l-[#6D4AE2]" : ""
                    }`}
                  >
                    <div
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                        conv.gender === "female"
                          ? "bg-pink-500/20 text-pink-400"
                          : "bg-blue-500/20 text-blue-400"
                      }`}
                    >
                      {conv.gender === "female" ? <UserRound size={18} /> : <User size={18} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                          {conv.name}
                        </span>
                        <span className="text-[10px] text-gray-400 ml-2 shrink-0">{conv.time}</span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                        {conv.message}
                      </p>
                    </div>
                  </div>
                ))}

                {/* AI suggestion row */}
                <div className="flex items-center justify-between px-4 py-2.5 bg-purple-50 dark:bg-purple-900/10">
                  <span className="text-[11px] font-semibold text-purple-500">
                    ✦ AI Suggestion
                  </span>
                  <span className="text-[11px] text-gray-400 italic truncate ml-2">
                    Try: "Here's your tracking link..."
                  </span>
                </div>

                {/* Response time row */}
                <div className="flex items-center gap-2 px-4 py-2.5 border-t border-gray-100 dark:border-white/5">
                  <LineChart size={14} className="text-green-500" />
                  <div className="flex flex-col">
                    <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-300">
                      Response time
                    </span>
                    <span className="text-[10px] text-gray-400">↓ 68% faster with AI</span>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* STATS ROW */}
      <section className="py-16" style={{ background: "var(--surface)" }}>
        <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            { value: "0.4ms", label: "Response Time", color: "text-[#06B6D4]" },
            { value: "98.2%", label: "AI Accuracy", color: "text-[#6D4AE2]" },
            { value: "∞", label: "Connected Channels", color: "text-green-600" },
            { value: "24/7", label: "Uptime", color: "text-[#1E293B] dark:text-white" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="border rounded-xl p-5 shadow-[0_4px_24px_rgba(109,74,226,0.04)]"
              style={{ background: "var(--surface)", borderColor: "var(--border)" }}
            >
              <p className={`text-3xl font-black ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-gray-500 uppercase tracking-wider">{stat.label}</p>
              <p className="text-sm text-green-600 mt-2">↑ Active</p>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES SECTION */}
      <section className="py-24 relative">
        <div className="max-w-7xl mx-auto px-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter mb-4">
              Everything You Need
            </h2>
            <p className="text-lg max-w-2xl mx-auto font-medium" style={{ color: "var(--muted-foreground)" }}>
              Powerful features designed to help your team deliver fast, accurate support across every channel.
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: MessageSquare,
                title: "Unified Inbox",
                description: "All messages from Instagram, WhatsApp, and Messenger flow into one unified inbox. No more switching between apps.",
                color: "#818CF8",
              },
              {
                icon: Zap,
                title: "AI Smart Replies",
                description: "Get instant AI-generated reply suggestions based on your knowledge base and conversation context.",
                color: "#06B6D4",
              },
              {
                icon: BookOpen,
                title: "Knowledge Base",
                description: "Upload your product docs, FAQs, and guides. The AI uses them to generate accurate, on-brand responses.",
                color: "#10B981",
              },
            ].map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="p-10 rounded-[2.5rem] bg-white/5 border hover:border-[#818CF8]/20 transition-all group hover:bg-white/[0.08]"
                style={{ borderColor: "var(--border)" }}
              >
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-8 border bg-white/5 group-hover:bg-[#6D4AE2] group-hover:text-white transition-all"
                  style={{ color: feature.color, borderColor: "var(--border)" }}
                >
                  <feature.icon size={28} strokeWidth={2} />
                </div>
                <h3 className="text-xl font-black text-slate-900 dark:text-white tracking-tight mb-3">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed font-medium">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* STATS GRID */}
      <section className="py-20 border-y bg-white/[0.01] backdrop-blur-3xl relative" style={{ borderColor: "var(--border)" }}>
        <div className="max-w-7xl mx-auto px-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-16 text-center">
            {[
              { value: "0.4ms", label: "Response Time", color: "text-[#06B6D4]" },
              { value: "98.2%", label: "AI Accuracy", color: "text-[#818CF8]" },
              { value: "Unlimited", label: "Connected Channels", color: "text-slate-900 dark:text-white" },
              { value: "24/7", label: "Uptime", color: "text-[#10B981]" },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="space-y-3"
              >
                <div className={`text-4xl md:text-5xl font-black ${stat.color} tracking-tighter`}>
                  {stat.value}
                </div>
                <div className="text-[10px] text-[#64748B] font-black uppercase tracking-[0.4em]">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA SECTION */}
      <section className="relative pb-24 pt-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4 w-full justify-center px-6"
        >
          <Link
            href="/inbox"
            className="w-full sm:w-auto bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white px-12 py-5 rounded-2xl text-[12px] font-black uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-4 active:scale-95 shadow-xl shadow-[#6D4AE2]/30 group"
          >
            Open Inbox
            <ArrowRight size={20} strokeWidth={3} className="group-hover:translate-x-2 transition-transform" />
          </Link>
          <Link
            href="/demo"
            className="w-full sm:w-auto bg-white/5 border-2 border-white/10 text-slate-900 dark:text-white hover:bg-white/10 px-12 py-5 rounded-2xl text-[12px] font-black uppercase tracking-[0.3em] transition-all active:scale-95 flex items-center justify-center"
          >
            Watch Demo
          </Link>
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="hidden lg:flex justify-center gap-16 pt-16 border-t mt-16"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex items-center gap-4 group">
            <Database size={18} className="text-[#818CF8] opacity-60 group-hover:opacity-100 transition-opacity" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#64748B] group-hover:text-slate-300 transition-colors">
              AI Powered
            </span>
          </div>
          <div className="flex items-center gap-4 group">
            <LineChart size={18} className="text-[#06B6D4] opacity-60 group-hover:opacity-100 transition-opacity" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#64748B] group-hover:text-slate-300 transition-colors">
              Live Analytics
            </span>
          </div>
          <div className="flex items-center gap-4 group">
            <Cpu size={18} className="text-[#818CF8] opacity-60 group-hover:opacity-100 transition-opacity" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#64748B] group-hover:text-slate-300 transition-colors">
              Smart Automation
            </span>
          </div>
        </motion.div>
      </section>

      {/* FOOTER */}
      <footer className="py-10 border-t bg-white/[0.01]" style={{ borderColor: "var(--border)" }}>
        <div className="max-w-7xl mx-auto px-10 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: "var(--accent)" }}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 2L13 5.5V10.5L8 14L3 10.5V5.5L8 2Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
                <path d="M8 5.5L10.5 7V9L8 10.5L5.5 9V7L8 5.5Z" fill="white" />
              </svg>
            </div>
            <span className="text-sm font-bold tracking-tight text-foreground font-heading">
              HaqDesk<span style={{ color: "var(--accent)" }}> AI</span>
            </span>
          </div>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            © {new Date().getFullYear()} HaqDesk AI. All rights reserved.
          </p>
        </div>
      </footer>

    </div>
  );
}