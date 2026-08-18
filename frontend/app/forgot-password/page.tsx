"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Mail, CheckCircle2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (res.ok) {
        setSent(true);
        toast.success("Reset link sent if that email exists");
      }
    } catch {
      toast.error("Network error");
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <CheckCircle2 size={48} className="text-[var(--success-foreground)] mx-auto mb-4" />
          <h2 className="text-xl font-bold text-foreground mb-2">Check your email</h2>
          <p className="text-muted-foreground text-sm">
            If an account exists with that email, we've sent a password reset link.
          </p>
          <Link href="/login" className="text-accent-glow text-sm mt-4 inline-block hover:text-purple-300">
            Back to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="w-12 h-12 rounded-xl bg-accent flex items-center justify-center mx-auto mb-4">
            <Mail size={20} className="text-foreground" />
          </div>
          <h1 className="text-2xl font-black text-foreground tracking-tight">Forgot Password?</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Enter your email and we'll send you a reset link.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-border bg-surface-wash text-foreground text-[13px] placeholder:text-muted-foreground focus:border-accent focus:outline-none transition-all"
              placeholder="you@example.com"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-on-accent text-[13px] font-semibold transition-all active:scale-95 disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {loading ? <div className="w-3.5 h-3.5 border-2 border-on-accent border-t-transparent rounded-full animate-spin" /> : "Send Reset Link"}
          </button>
        </form>

        <p className="text-center text-[12px] text-muted-foreground mt-5">
          <Link href="/login" className="text-accent-glow hover:text-purple-300 transition-colors">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
