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
      <div className="min-h-screen bg-[#090514] flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <CheckCircle2 size={48} className="text-emerald-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Check your email</h2>
          <p className="text-gray-400 text-sm">
            If an account exists with that email, we've sent a password reset link.
          </p>
          <Link href="/login" className="text-purple-400 text-sm mt-4 inline-block hover:text-purple-300">
            Back to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090514] flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="w-12 h-12 rounded-xl bg-[#6D4AE2] flex items-center justify-center mx-auto mb-4">
            <Mail size={20} className="text-white" />
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">Forgot Password?</h1>
          <p className="text-gray-400 text-sm mt-1">
            Enter your email and we'll send you a reset link.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-600 focus:border-purple-500 focus:outline-none transition-all"
              placeholder="you@example.com"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[13px] font-semibold transition-all active:scale-95 disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {loading ? <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : "Send Reset Link"}
          </button>
        </form>

        <p className="text-center text-[12px] text-gray-500 mt-5">
          <Link href="/login" className="text-purple-400 hover:text-purple-300 transition-colors">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
