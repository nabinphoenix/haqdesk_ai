"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { AlertCircle, Eye, EyeOff } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const formData = new URLSearchParams();
            formData.append("username", email);
            formData.append("password", password);

            const response = await fetch(`${API_URL}/api/v1/auth/token`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem("token", data.access_token);
                localStorage.setItem("userRole", data.user.role);
                localStorage.setItem("userName", data.user.name);
                localStorage.setItem("userEmail", data.user.email);
                if (data.user.business_id) {
                    localStorage.setItem("userBusinessId", data.user.business_id);
                }
                toast.success(`Welcome back, ${data.user.name}!`);
                if (data.user.role === "super_admin") {
                    router.push("/super-admin");
                } else {
                    router.push("/inbox");
                }
            } else {
                const errorMsg = data.detail || "Authentication failed. Please check your credentials.";
                setError(errorMsg);
                toast.error(errorMsg);
            }
        } catch (err) {
            setError("Cannot connect to server. Please try again.");
            toast.error("Cannot connect to server.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex bg-[#090514]">

            {/* LEFT PANEL — branding */}
            <div className="hidden lg:flex w-[45%] flex-col justify-between p-12 relative overflow-hidden">

                {/* Background glow */}
                <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-[#6D4AE2]/20 rounded-full blur-[120px] -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
                <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[100px] translate-x-1/2 translate-y-1/2 pointer-events-none" />

                {/* Logo */}
                <Link href="/" className="flex items-center gap-3 z-10">
                    <div className="w-9 h-9 rounded-xl bg-[#6D4AE2] flex items-center justify-center shrink-0">
                        <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
                            <path d="M8 2L13 5.5V10.5L8 14L3 10.5V5.5L8 2Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
                            <path d="M8 5.5L10.5 7V9L8 10.5L5.5 9V7L8 5.5Z" fill="white" />
                        </svg>
                    </div>
                    <span className="text-white font-bold text-[16px] tracking-tight">
                        HaqDesk<span className="text-[#818CF8]"> AI</span>
                    </span>
                </Link>

                {/* Center content */}
                <div className="z-10">
                    <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 mb-6">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                        <span className="text-[11px] font-medium text-gray-300 uppercase tracking-wider">AI-Powered Support Platform</span>
                    </div>
                    <h2 className="text-4xl font-black text-white leading-tight tracking-tight mb-4">
                        Your customers<br />
                        deserve faster<br />
                        <span className="text-[#818CF8]">answers.</span>
                    </h2>
                    <p className="text-gray-400 text-[14px] leading-relaxed max-w-sm">
                        HaqDesk AI unifies your Instagram, WhatsApp, and Messenger conversations with AI-powered reply suggestions.
                    </p>

                    {/* Feature pills */}
                    <div className="flex flex-wrap gap-2 mt-8">
                        {["Unified Inbox", "RAG Knowledge Base", "AI Draft Replies", "BERT Sentiment"].map((f) => (
                            <span key={f} className="text-[11px] font-medium text-gray-300 bg-white/5 border border-white/10 rounded-full px-3 py-1">
                                {f}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Bottom stat row */}
                <div className="grid grid-cols-3 gap-4 z-10">
                    {[
                        { value: "< 5s", label: "AI Response" },
                        { value: "80%+", label: "RAG Accuracy" },
                        { value: "3", label: "Platforms" },
                    ].map((s) => (
                        <div key={s.label} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-center">
                            <p className="text-lg font-black text-white">{s.value}</p>
                            <p className="text-[10px] text-gray-400 uppercase tracking-wider">{s.label}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* RIGHT PANEL — form */}
            <div className="flex-1 flex items-center justify-center p-6 relative">

                {/* Back to home — mobile only */}
                <Link
                    href="/"
                    className="absolute top-6 left-6 flex items-center gap-1.5 text-[12px] text-gray-400 hover:text-white transition-all lg:hidden"
                >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                        <path d="M10 3L5 8l5 5" />
                    </svg>
                    Home
                </Link>

                <div className="w-full max-w-[400px]">

                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-2xl font-black text-white tracking-tight mb-1">
                            Welcome back
                        </h1>
                        <p className="text-[13px] text-gray-400">
                            Sign in to your HaqDesk AI account
                        </p>
                    </div>

                    {/* Google button */}
                    <button
                        type="button"
                        onClick={() => { window.location.href = `${API_URL}/api/v1/auth/google`; }}
                        className="w-full flex items-center justify-center gap-3 py-2.5 rounded-xl border border-white/10 bg-white/5 text-[13px] font-medium text-white hover:bg-white/10 transition-all mb-5"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="18" height="18">
                            <path fill="#EA4335" d="M24 9.5c3.54 0 6.69 1.22 9.17 3.24l6.85-6.85C36.93 2.57 30.84 0 24 0 14.61 0 6.5 5.23 2.45 12.79l7.92 6.15C12.33 13.03 17.71 9.5 24 9.5z" />
                            <path fill="#4285F4" d="M46.54 24.58c0-1.63-.15-3.2-.42-4.71H24v9.03h12.74c-.55 2.95-2.2 5.46-4.71 7.15l7.45 5.78c4.33-4 6.86-9.89 6.86-17.25z" />
                            <path fill="#FBBC05" d="M10.37 28.94c-.53-1.53-.84-3.18-.84-4.94s.31-3.41.84-4.94l-7.92-6.15C1.08 16.12 0 19.96 0 24c0 4.04 1.08 7.88 2.45 11.29l7.92-6.15z" />
                            <path fill="#34A853" d="M24 48c6.84 0 12.93-2.27 17.22-6.15l-7.45-5.78c-2.07 1.39-4.71 2.22-7.77 2.22-6.29 0-11.66-3.53-14.36-8.66l-7.92 6.15C6.5 42.77 14.61 48 24 48z" />
                            <path fill="none" d="M0 0h48v48H0z" />
                        </svg>
                        Continue with Google
                    </button>

                    {/* Divider */}
                    <div className="flex items-center gap-3 mb-5">
                        <div className="flex-1 h-px bg-white/10" />
                        <span className="text-[11px] text-gray-500 uppercase tracking-wider">or</span>
                        <div className="flex-1 h-px bg-white/10" />
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-[12px] mb-4">
                            <AlertCircle size={14} className="shrink-0" />
                            {error}
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">

                        <div>
                            <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                                Email Address
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-600 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all"
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-1.5">
                                <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                                    Password
                                </label>
                                <button type="button" className="text-[11px] text-purple-400 hover:text-purple-300 transition-colors">
                                    Forgot password?
                                </button>
                            </div>
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-4 py-2.5 pr-10 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-600 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all"
                                    placeholder="••••••••"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                                >
                                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 rounded-xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[13px] font-semibold transition-all active:scale-95 disabled:opacity-60 disabled:cursor-wait flex items-center justify-center gap-2 mt-2"
                        >
                            {loading ? (
                                <>
                                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    Signing in...
                                </>
                            ) : (
                                "Sign In"
                            )}
                        </button>

                    </form>

                    {/* Register link */}
                    <p className="text-center text-[12px] text-gray-500 mt-5">
                        Don't have an account?{" "}
                        <Link href="/register" className="text-purple-400 hover:text-purple-300 font-medium transition-colors">
                            Register here
                        </Link>
                    </p>

                    {/* Demo credentials — collapsed by default */}
                    <details className="mt-6 group">
                        <summary className="text-[11px] text-gray-600 hover:text-gray-400 cursor-pointer transition-colors text-center list-none flex items-center justify-center gap-1.5">
                            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <circle cx="8" cy="8" r="6" />
                                <path d="M8 7v4M8 5.5v.5" />
                            </svg>
                            Demo credentials
                        </summary>
                        <div className="mt-3 p-3 rounded-xl border border-white/10 bg-white/[0.03] text-[11px] text-gray-400 space-y-1">
                            <div className="flex justify-between">
                                <span className="text-gray-500">Email</span>
                                <span className="font-mono text-gray-300">nabinepali012@gmail.com</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">Password</span>
                                <span className="font-mono text-gray-300">admin123</span>
                            </div>
                        </div>
                    </details>

                </div>
            </div>

        </div>
    );
}