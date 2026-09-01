"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  Zap,
  ArrowRight,
  MessageSquare,
  BookOpen,
  Cpu,
  Database,
  LineChart,
  Users,
  ShieldCheck,
} from "lucide-react";
import InboxPreview from "@/components/marketing/InboxPreview";
import ParticleWave from "@/components/marketing/ParticleWave";
import { useTheme } from "next-themes";

const customerLabels = ["Chats.", "Messages.", "Inquiries."] as const;

function RotatingCustomerLabel() {
  const shouldReduceMotion = useReducedMotion();
  const [labelIndex, setLabelIndex] = useState(0);
  const [visibleLength, setVisibleLength] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const label = customerLabels[labelIndex];

  useEffect(() => {
    if (shouldReduceMotion) {
      setVisibleLength(label.length);
      setIsDeleting(false);
      return;
    }

    const delay = isDeleting ? 45 : visibleLength === label.length ? 1500 : 85;
    const timeoutId = window.setTimeout(() => {
      if (!isDeleting && visibleLength < label.length) {
        setVisibleLength((length) => length + 1);
      } else if (!isDeleting) {
        setIsDeleting(true);
      } else if (visibleLength > 0) {
        setVisibleLength((length) => length - 1);
      } else {
        setLabelIndex((index) => (index + 1) % customerLabels.length);
        setIsDeleting(false);
      }
    }, delay);

    return () => window.clearTimeout(timeoutId);
  }, [isDeleting, label.length, shouldReduceMotion, visibleLength]);

  return (
    <span className="inline-flex min-w-[10ch]" aria-label={label}>
      <span aria-hidden="true">
        {label.slice(0, visibleLength)}
        {!shouldReduceMotion && (
          <span className="ml-1 inline-block h-[0.82em] w-[3px] animate-pulse bg-[#6D4AE2] align-[-0.06em]" />
        )}
      </span>
      <span className="sr-only">{label}</span>
    </span>
  );
}
export default function Home() {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const footerLogoSrc = mounted && resolvedTheme === "dark"
    ? "/images/Haqdesk_AI_Dark.png"
    : "/images/Haqdesk_AI_Light.png";
  return (
    <div className="flex-1 overflow-y-auto font-body custom-scrollbar bg-surface dark:bg-background">

      {/* HERO SECTION */}
      <section className="relative flex min-h-[max(700px,calc(100dvh-60px))] w-full items-center overflow-hidden bg-white dark:bg-background">
        <ParticleWave />
        <div className="relative z-10 mx-auto w-full max-w-7xl px-6 py-24 sm:px-10 lg:px-12">
          <div className="flex flex-col items-center justify-between gap-14 lg:flex-row lg:gap-10">
            {/* LEFT COLUMN */}
            <div className="flex w-full max-w-2xl flex-col space-y-7 lg:w-[54%]">

              <h1 className="font-heading text-[clamp(2.75rem,4.1vw,4.5rem)] font-black leading-[0.94] tracking-[-0.06em] text-[#0F172A] dark:text-[#F8FAFC]">
                <span className="block">All Your Customer</span>
                <span className="block min-h-[0.95em]"><RotatingCustomerLabel /></span>
                <span className="brand-gradient-text block">One Smart Inbox.</span>
              </h1>
              <p className="max-w-xl text-[15px] font-medium leading-7 text-[#64748B] dark:text-[#94A3B8] sm:text-base">
                HaqDesk AI brings Instagram, WhatsApp, and Messenger into one intelligent inbox,
                so your team can respond faster with thoughtful, AI-powered help.
              </p>
              <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center">
                <Link
                  href="/inbox"
                  className="inline-flex min-h-[58px] items-center justify-center gap-3 rounded-[28px] bg-[#6D4AE2] px-8 py-4 font-body text-base font-bold text-white shadow-[0_14px_30px_rgba(109,74,226,0.28)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#5B3BC7] hover:shadow-[0_17px_34px_rgba(109,74,226,0.34)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#6D4AE2]"
                >
                  Open Inbox
                  <ArrowRight size={17} aria-hidden="true" />
                </Link>
                <Link
                  href="#features"
                  className="inline-flex min-h-[58px] items-center justify-center gap-3 rounded-[28px] border-2 border-[#6D4AE2] bg-white px-8 py-4 font-body text-base font-bold text-[#6D4AE2] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#F8FAFF] hover:border-[#5B3BC7] hover:text-[#5B3BC7] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#6D4AE2] dark:border-[#9D85FF] dark:bg-[#130E22] dark:text-[#9D85FF] dark:hover:bg-[#21183b]"
                >
                  Explore features
                </Link>
              </div>
              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 pt-1">
                {["Free to start", "No credit card", "Channels connected in up to 2 days"].map((label) => (
                  <span key={label} className="flex items-center gap-1.5 text-xs font-semibold text-[#64748B] dark:text-[#94A3B8]">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                      <path d="m2.5 7.2 2.7 2.7L11.7 3.7" stroke="#6D4AE2" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {label}
                  </span>
                ))}
              </div>
            </div>

            {/* RIGHT COLUMN - sequential inbox preview */}
            <div className="flex w-full justify-center lg:w-[42%] lg:justify-end">
              <InboxPreview />
            </div>

          </div>
        </div>
      </section>

      {/* FEATURES SECTION */}
      <section id="features" className="relative overflow-hidden bg-[#F8FAFF] py-24 dark:bg-background">
        <div className="pointer-events-none absolute -left-40 top-20 h-80 w-80 rounded-full bg-[#6D4AE2]/10 blur-3xl" />
        <div className="pointer-events-none absolute -right-40 bottom-0 h-96 w-96 rounded-full bg-[#2563EB]/10 blur-3xl" />
        <div className="relative mx-auto max-w-7xl px-6 sm:px-10 lg:px-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mx-auto mb-14 max-w-3xl text-center"
          >
            <p className="mb-4 font-body text-[11px] font-bold uppercase tracking-[0.24em] text-[#6D4AE2]">Explore features</p>
            <h2 className="font-heading text-4xl font-black leading-tight tracking-[-0.04em] text-[#0F172A] dark:text-[#F8FAFC] sm:text-5xl">
              Everything your team needs to move faster.
            </h2>
            <p className="mx-auto mt-5 max-w-2xl font-body text-base leading-7 text-[#64748B] dark:text-[#94A3B8]">
              One calm workspace for every customer conversation, with AI that understands your business.
            </p>
          </motion.div>

          <div className="grid gap-5 lg:grid-cols-12">
            <motion.article
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              whileHover={{ y: -6 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4 }}
              className="group relative min-h-[350px] overflow-hidden rounded-[2rem] bg-[#6D4AE2] p-7 text-white shadow-[0_18px_50px_rgba(109,74,226,0.22)] sm:p-9 lg:col-span-7"
            >
              <div className="pointer-events-none absolute -right-16 -top-16 h-52 w-52 rounded-full border-[26px] border-white/10 transition-transform duration-500 group-hover:scale-110" />
              <div className="relative flex h-full flex-col justify-between">
                <div>
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 text-white">
                    <MessageSquare size={27} strokeWidth={1.8} />
                  </div>
                  <p className="mt-8 font-body text-[10px] font-bold uppercase tracking-[0.2em] text-white/70">One workspace</p>
                  <h3 className="mt-2 font-heading text-3xl font-black tracking-[-0.04em]">Unified Inbox</h3>
                  <p className="mt-4 max-w-xl font-body text-sm leading-6 text-white/85">
                    All messages from Instagram, WhatsApp, and Messenger flow into one unified inbox. No more switching between apps.
                  </p>
                </div>
                <div className="mt-8 flex flex-wrap gap-2 font-body text-[11px] font-semibold text-white/90">
                  {["Instagram", "WhatsApp", "Messenger"].map((channel) => (
                    <span key={channel} className="rounded-full border border-white/20 bg-white/10 px-3 py-1.5">{channel}</span>
                  ))}
                </div>
              </div>
            </motion.article>

            <motion.article
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              whileHover={{ y: -6 }}
              viewport={{ once: true }}
              transition={{ delay: 0.08, duration: 0.4 }}
              className="group relative min-h-[350px] overflow-hidden rounded-[2rem] border border-[#BFDBFE] bg-white p-7 text-[#0F172A] shadow-[0_18px_50px_rgba(37,99,235,0.10)] sm:p-9 lg:col-span-5 dark:border-white/10 dark:bg-[#130E22] dark:text-[#F8FAFC]"
            >
              <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#2563EB]/10 transition-transform duration-500 group-hover:scale-125" />
              <div className="relative flex h-full flex-col justify-between">
                <div>
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#DBEAFE] text-[#2563EB] dark:bg-[#2563EB]/20 dark:text-[#93C5FD]">
                    <Zap size={27} strokeWidth={2} />
                  </div>
                  <p className="mt-8 font-body text-[10px] font-bold uppercase tracking-[0.2em] text-[#2563EB]">Context-aware assistance</p>
                  <h3 className="mt-2 font-heading text-3xl font-black tracking-[-0.04em]">AI Smart Replies</h3>
                  <p className="mt-4 font-body text-sm leading-6 text-[#64748B] dark:text-[#94A3B8]">
                    Get instant AI-generated reply suggestions based on your knowledge base and conversation context.
                  </p>
                </div>
                <div className="mt-8 flex items-center gap-3 rounded-2xl border border-[#BFDBFE] bg-[#EFF6FF] p-3 font-body text-xs font-semibold text-[#334155] dark:border-white/10 dark:bg-white/5 dark:text-[#CBD5E1]">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#6D4AE2] shadow-[0_0_0_5px_rgba(109,74,226,0.12)]" />
                  Suggested reply ready to review
                  <span className="ml-auto text-[#6D4AE2]">AI</span>
                </div>
              </div>
            </motion.article>

            <motion.article
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              whileHover={{ y: -6 }}
              viewport={{ once: true }}
              transition={{ delay: 0.16, duration: 0.4 }}
              className="group relative min-h-[310px] overflow-hidden rounded-[2rem] border border-[#C7D2FE] bg-[#EEF2FF] p-7 text-[#0F172A] shadow-[0_18px_50px_rgba(79,70,229,0.10)] sm:p-9 lg:col-span-5 dark:border-white/10 dark:bg-[#1A1630] dark:text-[#F8FAFC]"
            >
              <div className="pointer-events-none absolute -bottom-12 -right-10 h-44 w-44 rounded-full bg-[#9D85FF]/20 blur-2xl transition-transform duration-500 group-hover:scale-125" />
              <div className="relative flex h-full flex-col justify-between">
                <div>
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/70 text-[#4F46E5] dark:bg-white/10 dark:text-[#A5B4FC]">
                    <BookOpen size={27} strokeWidth={1.8} />
                  </div>
                  <p className="mt-8 font-body text-[10px] font-bold uppercase tracking-[0.2em] text-[#4F46E5] dark:text-[#A5B4FC]">Your source of truth</p>
                  <h3 className="mt-2 font-heading text-3xl font-black tracking-[-0.04em]">Knowledge Base</h3>
                  <p className="mt-4 font-body text-sm leading-6 text-[#475569] dark:text-[#CBD5E1]">
                    Upload your product docs, FAQs, and guides. The AI uses them to generate accurate, on-brand responses.
                  </p>
                </div>
                <div className="mt-7 flex flex-wrap gap-2 font-body text-[11px] font-semibold text-[#4F46E5] dark:text-[#C7D2FE]">
                  {["Product docs", "FAQs", "Guides"].map((item) => (
                    <span key={item} className="rounded-xl border border-[#C7D2FE] bg-white/60 px-3 py-2 dark:border-white/10 dark:bg-white/5">{item}</span>
                  ))}
                </div>
              </div>
            </motion.article>

            <motion.article
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              whileHover={{ y: -6 }}
              viewport={{ once: true }}
              transition={{ delay: 0.24, duration: 0.4 }}
              className="group relative min-h-[310px] overflow-hidden rounded-[2rem] bg-[#2563EB] p-7 text-white shadow-[0_18px_50px_rgba(37,99,235,0.22)] sm:p-9 lg:col-span-7"
            >
              <div className="pointer-events-none absolute -bottom-24 -right-14 h-72 w-72 rounded-full border-[30px] border-white/10 transition-transform duration-500 group-hover:scale-110" />
              <div className="relative grid h-full gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
                <div>
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 text-white">
                    <Users size={27} strokeWidth={1.8} />
                  </div>
                  <p className="mt-8 font-body text-[10px] font-bold uppercase tracking-[0.2em] text-white/70">Secure collaboration</p>
                  <h3 className="mt-2 font-heading text-3xl font-black tracking-[-0.04em]">Invite Team</h3>
                </div>
                <div>
                  <p className="max-w-xl font-body text-sm leading-6 text-white/85">
                    Invite teammates with role-based access. They use their own HaqDesk login, so you never share social media credentials.
                  </p>
                  <div className="mt-7 flex items-center justify-between rounded-2xl border border-white/20 bg-white/10 p-3 backdrop-blur-sm">
                    <div className="flex -space-x-2">
                      {["#9D85FF", "#C7D2FE", "#FFFFFF"].map((color, index) => (
                        <span key={color} className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-[#2563EB] text-[10px] font-bold text-[#2563EB]" style={{ backgroundColor: color }}>{index === 2 ? "+" : ""}</span>
                      ))}
                    </div>
                    <span className="flex items-center gap-2 font-body text-[11px] font-semibold text-white/90"><ShieldCheck size={15} /> Credentials stay private</span>
                  </div>
                </div>
              </div>
            </motion.article>
          </div>
        </div>
      </section>

      {/* STATS GRID */}
      <section className="py-20 border-y bg-surface/[0.01] backdrop-blur-3xl relative" style={{ borderColor: "var(--border)" }}>
        <div className="max-w-7xl mx-auto px-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-16 text-center">
            {[
              { value: "0.4ms", label: "Response Time", color: "text-[#06B6D4]" },
              { value: "98.2%", label: "AI Accuracy", color: "text-accent-glow" },
              { value: "Unlimited", label: "Connected Channels", color: "text-foreground dark:text-foreground" },
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
                <div className="text-[10px] text-muted-foreground font-black uppercase tracking-[0.4em]">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[#E2E8F0] bg-white py-0 dark:border-white/10 dark:bg-background">
        <div className="mx-auto max-w-7xl px-6 py-12 sm:px-10 lg:px-12">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center gap-8 border-b border-[#E2E8F0] pb-10 dark:border-white/10"
          >
            <div className="flex w-full flex-col items-stretch justify-center gap-4 sm:w-auto sm:flex-row">
              <Link
                href="/inbox"
                className="inline-flex min-h-[58px] items-center justify-center gap-3 rounded-[28px] bg-[#6D4AE2] px-8 py-4 font-body text-base font-bold text-white shadow-[0_14px_30px_rgba(109,74,226,0.28)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#5B3BC7] hover:shadow-[0_17px_34px_rgba(109,74,226,0.34)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#6D4AE2]"
              >
                Open Inbox
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
              <Link
                href="#features"
                className="inline-flex min-h-[58px] items-center justify-center gap-3 rounded-[28px] border-2 border-[#6D4AE2] bg-white px-8 py-4 font-body text-base font-bold text-[#6D4AE2] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#F8FAFF] hover:border-[#5B3BC7] hover:text-[#5B3BC7] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#6D4AE2] dark:border-[#9D85FF] dark:bg-[#130E22] dark:text-[#9D85FF] dark:hover:bg-[#21183b]"
              >
                Explore Features
              </Link>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
              <div className="flex items-center gap-3 font-body text-xs font-bold uppercase tracking-[0.18em] text-[#64748B] dark:text-[#94A3B8]">
                <Database size={17} className="text-[#6D4AE2]" aria-hidden="true" />
                AI Powered
              </div>
              <div className="flex items-center gap-3 font-body text-xs font-bold uppercase tracking-[0.18em] text-[#64748B] dark:text-[#94A3B8]">
                <LineChart size={17} className="text-[#2563EB]" aria-hidden="true" />
                Live Analytics
              </div>
              <div className="flex items-center gap-3 font-body text-xs font-bold uppercase tracking-[0.18em] text-[#64748B] dark:text-[#94A3B8]">
                <Cpu size={17} className="text-[#4F46E5]" aria-hidden="true" />
                Smart Automation
              </div>
            </div>
          </motion.div>
        </div>
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-5 px-6 py-8 sm:px-10 md:flex-row lg:px-12">
          <Link href="/" className="group flex items-center gap-3" aria-label="HaqDesk AI home">
            <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-lg transition-transform duration-200 group-hover:scale-105">
              <img
                src={footerLogoSrc}
                alt=""
                className="h-full w-full object-contain"
              />
            </div>
            <div className="leading-tight">
              <span className="font-heading text-sm font-bold tracking-tight text-[#0F172A] dark:text-[#F8FAFC]">
                HaqDesk<span className="text-[#6D4AE2]"> AI</span>
              </span>
              <p className="mt-0.5 text-[10px] font-medium text-[#64748B] dark:text-[#94A3B8]">
                AI-powered customer support
              </p>
            </div>
          </Link>
          <p className="text-center text-[10px] font-semibold uppercase tracking-[0.16em] text-[#64748B] dark:text-[#94A3B8]">
            Copyright 2026 HaqDesk AI. All rights reserved.
          </p>
        </div>
      </footer>

    </div>
  );
}