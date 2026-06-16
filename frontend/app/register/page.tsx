"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: fullName,
          email,
          password,
          business_name: businessName,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success("Account created!");
        router.push("/login");
      } else {
        const errorMsg = data.detail || "Registration failed.";
        setError(errorMsg);
        toast.error(errorMsg);
      }
    } catch (err) {
      setError("Cannot connect to server.");
      toast.error("Cannot connect to server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background bg-mesh-gradient overflow-y-auto font-body antialiased">
      {/* Background elements */}
      <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-[#6D4AE208] blur-[100px] rounded-full -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-[#06B6D408] blur-[100px] rounded-full -z-10" />

      {/* Back to Home */}
      <Link
        href="/"
        className="absolute top-6 left-6 flex items-center gap-2 text-[11px] font-medium"
        style={{ color: "var(--muted-foreground)" }}
        onMouseEnter={e => (e.currentTarget.style.color = "var(--text-primary)")}
        onMouseLeave={e => (e.currentTarget.style.color = "var(--muted-foreground)")}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        >
          <path d="M10 3L5 8l5 5" />
        </svg>
        Back to home
      </Link>

      <div className="max-w-md w-full p-6 sm:p-10 rounded-[2.5rem] card-glossy relative">
        <div className="text-center mb-6">
          {/* Brand Hexagon Logo */}
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-xl mx-auto transition-transform hover:scale-105 duration-500 hover-glow"
            style={{ background: "var(--accent)" }}
          >
            <img src="/images/HaqDesk.png" alt="HaqDesk AI Logo" className="w-12 h-12 object-contain" />
          </div>
          <h1 className="text-3xl font-black mt-6 tracking-tighter text-slate-900 dark:text-white">
            HaqDesk<span style={{ color: "var(--accent)" }}>AI</span>
          </h1>
          <p className="text-[#818CF8]/60 text-[10px] font-black uppercase tracking-[0.2em] mt-2">
            Create your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-4 bg-red-950/40 border border-red-900/50 text-red-400 text-[11px] font-bold rounded-2xl text-center flex items-center justify-center gap-2">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest pl-2">
              Full Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              className="w-full px-5 py-3.5 rounded-2xl border border-surface-border bg-white/5 text-slate-900 dark:text-white placeholder-[#475569] focus:bg-white/[0.08] focus:ring-4 focus:ring-[#6D4AE220] focus:border-[#818CF8] outline-none transition-all text-sm font-medium"
              placeholder="Your full name"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest pl-2">
              Business Name
            </label>
            <input
              type="text"
              value={businessName}
              onChange={e => setBusinessName(e.target.value)}
              className="w-full px-5 py-3.5 rounded-2xl border border-surface-border bg-white/5 text-slate-900 dark:text-white placeholder-[#475569] focus:bg-white/[0.08] focus:ring-4 focus:ring-[#6D4AE220] focus:border-[#818CF8] outline-none transition-all text-sm font-medium"
              placeholder="Your business name"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest pl-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full px-5 py-3.5 rounded-2xl border border-surface-border bg-white/5 text-slate-900 dark:text-white placeholder-[#475569] focus:bg-white/[0.08] focus:ring-4 focus:ring-[#6D4AE220] focus:border-[#818CF8] outline-none transition-all text-sm font-medium"
              placeholder="you@example.com"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest pl-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-5 py-3.5 rounded-2xl border border-surface-border bg-white/5 text-slate-900 dark:text-white placeholder-[#475569] focus:bg-white/[0.08] focus:ring-4 focus:ring-[#6D4AE220] focus:border-[#818CF8] outline-none transition-all text-sm font-medium"
              placeholder="••••••••"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-[10px] font-black text-[#818CF8] uppercase tracking-widest pl-2">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              className="w-full px-5 py-3.5 rounded-2xl border border-surface-border bg-white/5 text-slate-900 dark:text-white placeholder-[#475569] focus:bg-white/[0.08] focus:ring-4 focus:ring-[#6D4AE220] focus:border-[#818CF8] outline-none transition-all text-sm font-medium"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full bg-[#6D4AE2] text-white py-4 rounded-2xl font-black text-[11px] uppercase tracking-[0.2em] hover:bg-[#5B3BC7] hover-glow transition-all active:scale-95 shadow-xl shadow-[#6D4AE2]/20 flex items-center justify-center ${loading ? "opacity-70 cursor-wait" : ""}`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Creating Account...
              </div>
            ) : (
              "Create Account"
            )}
          </button>

          {/* OR separator */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px" style={{ background: "var(--border)" }} />
            <span className="text-[9px] font-black uppercase tracking-widest" style={{ color: "var(--muted-foreground)" }}>
              or
            </span>
            <div className="flex-1 h-px" style={{ background: "var(--border)" }} />
          </div>

          {/* Google Sign‑In (coming soon) */}
          <button
            type="button"
            onClick={() => (window.location.href = `${API_URL}/api/v1/auth/google`)}
            className="w-full flex items-center justify-center gap-3 py-3.5 rounded-2xl border text-[12px] font-medium transition-all hover:bg-black/5 dark:hover:bg-white/5 active:scale-[0.98]"
            style={{
              borderColor: "var(--border)",
              color: "var(--text-primary)",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4" />
              <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853" />
              <path d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05" />
              <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 6.294C4.672 4.169 6.656 3.58 9 3.58z" fill="#EA4335" />
            </svg>
            Continue with Google
          </button>

          <p className="text-center text-[11px] mt-6" style={{ color: "var(--muted-foreground)" }}>
            Already have an account?{' '}
            <Link href="/login" className="font-semibold" style={{ color: "var(--accent)" }}>
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}




