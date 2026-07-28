"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Eye, EyeOff, CheckCircle2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const resetToken = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!resetToken) setError("Invalid or missing reset link.");
  }, [resetToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (!resetToken) return;

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reset_token: resetToken, new_password: password }),
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess(true);
        toast.success("Password reset successfully!");
        setTimeout(() => router.push("/login"), 2000);
      } else {
        setError(data.detail || "Failed to reset password.");
      }
    } catch {
      setError("Cannot connect to server.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#090514] flex items-center justify-center">
        <div className="text-center">
          <CheckCircle2 size={48} className="text-emerald-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Password Reset!</h2>
          <p className="text-gray-400 text-sm">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090514] flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-black text-white tracking-tight">Reset Your Password</h1>
          <p className="text-gray-400 text-sm mt-1">Enter your new password below.</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">New Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 pr-10 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-600 focus:border-purple-500 focus:outline-none transition-all"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Confirm Password</label>
            <input
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-600 focus:border-purple-500 focus:outline-none transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !!error}
            className="w-full py-2.5 rounded-xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[13px] font-semibold transition-all active:scale-95 disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {loading ? <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : "Reset Password"}
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

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#090514] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}
