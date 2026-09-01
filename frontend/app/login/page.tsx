"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import ThemeToggle from "@/components/ui/ThemeToggle";
import ThemeLogo from "@/components/ui/ThemeLogo";
import { AlertCircle } from "lucide-react";
import PasswordField from "@/components/ui/PasswordField";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
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
                const role = data.user.role;
                if (role === "super_admin") {
                    router.push("/super-admin");
                } else if (role === "supervisor") {
                    router.push("/supervisor");
                } else if (role === "agent") {
                    router.push("/agent");
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
        <div className="relative min-h-screen overflow-hidden bg-background">
          <ThemeToggle className="absolute right-6 top-6 z-30 sm:right-10" />
          <div className="pointer-events-none absolute -left-64 -top-64 h-[520px] w-[520px] rounded-full bg-accent/20 blur-[120px]" />
          <div className="pointer-events-none absolute -bottom-52 left-[38%] h-[440px] w-[440px] rounded-full bg-accent/10 blur-[110px]" />
          <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-[1440px] px-6 sm:px-10 xl:px-14 2xl:px-16">

            {/* LEFT PANEL — branding */}
            <div className="relative hidden w-[52%] flex-col justify-between py-12 pr-12 lg:flex xl:pr-20">

                {/* Logo */}
                <Link href="/" className="flex items-center gap-3 z-10">
                    <div className="w-9 h-9 rounded-xl overflow-hidden flex items-center justify-center shrink-0 transition-transform hover:scale-105">
                        <ThemeLogo width={36} height={36} alt="HaqDesk AI" className="w-full h-full object-contain" />
                    </div>
                    <span className="text-foreground font-bold text-[16px] tracking-tight">
                        HaqDesk<span className="text-accent-glow"> AI</span>
                    </span>
                </Link>

                {/* Center content */}
                <div className="z-10">
                    <div className="inline-flex items-center gap-2 bg-surface-wash border border-border rounded-full px-4 py-1.5 mb-6">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                        <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">AI-Powered Support Platform</span>
                    </div>
                    <h2 className="text-4xl font-black text-foreground leading-tight tracking-tight mb-4">
                        Your customers<br />
                        deserve faster<br />
                        <span className="text-accent-glow">answers.</span>
                    </h2>
                    <p className="text-muted-foreground text-[14px] leading-relaxed max-w-sm">
                        HaqDesk AI unifies your Instagram, WhatsApp, and Messenger conversations with AI-powered reply suggestions.
                    </p>

                    {/* Feature pills */}
                    <div className="flex flex-wrap gap-2 mt-8">
                        {["Unified Inbox", "RAG Knowledge Base", "AI Draft Replies", "BERT Sentiment"].map((f) => (
                            <span key={f} className="text-[11px] font-medium text-muted-foreground bg-surface-wash border border-border rounded-full px-3 py-1">
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
                        <div key={s.label} className="rounded-xl border border-border bg-surface-wash p-3 text-center">
                            <p className="text-lg font-black text-foreground">{s.value}</p>
                            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{s.label}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* RIGHT PANEL — form */}
            <div className="relative flex w-full items-center justify-center py-12 lg:w-[48%] lg:pl-12 xl:pl-20">

                {/* Back to home — mobile only */}
                <Link
                    href="/"
                    className="absolute top-6 left-6 flex items-center gap-1.5 text-[12px] text-muted-foreground hover:text-foreground transition-all lg:hidden"
                >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                        <path d="M10 3L5 8l5 5" />
                    </svg>
                    Home
                </Link>

                <div className="w-full max-w-[400px]">

                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-2xl font-black text-foreground tracking-tight mb-1">
                            Welcome back
                        </h1>
                        <p className="text-[13px] text-muted-foreground">
                            Sign in to your HaqDesk AI account
                        </p>
                    </div>

                    {/* Google button */}
                    <button
                        type="button"
                        onClick={() => { window.location.href = `${API_URL}/api/v1/auth/google`; }}
                        className="w-full flex items-center justify-center gap-3 py-2.5 rounded-xl border border-border bg-surface-wash text-[13px] font-medium text-foreground hover:bg-surface-wash transition-all mb-5"
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
                        <div className="flex-1 h-px bg-surface-wash" />
                        <span className="text-[11px] text-muted-foreground uppercase tracking-wider">or</span>
                        <div className="flex-1 h-px bg-surface-wash" />
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="flex items-center gap-2 p-3 rounded-xl bg-[var(--error-surface)] border border-[var(--error-border)] text-[var(--error-foreground)] text-[12px] mb-4">
                            <AlertCircle size={14} className="shrink-0" />
                            {error}
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">

                        <div>
                            <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                                Email Address
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-xl border border-border bg-surface-wash text-foreground text-[13px] placeholder:text-muted-foreground focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        <PasswordField
                            id="login-password"
                            label="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            labelAction={
                                <Link href="/forgot-password" className="text-[11px] text-accent-glow hover:text-purple-300 transition-colors">
                                    Forgot password?
                                </Link>
                            }
                        />

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-on-accent text-[13px] font-semibold transition-all active:scale-95 disabled:opacity-60 disabled:cursor-wait flex items-center justify-center gap-2 mt-2"
                        >
                            {loading ? (
                                <>
                                    <div className="w-3.5 h-3.5 border-2 border-on-accent border-t-transparent rounded-full animate-spin" />
                                    Signing in...
                                </>
                            ) : (
                                "Sign In"
                            )}
                        </button>

                    </form>

                    {/* Register link */}
                    <p className="text-center text-[12px] text-muted-foreground mt-5">
                        Don't have an account?{" "}
                        <Link href="/register" className="text-accent-glow hover:text-purple-300 font-medium transition-colors">
                            Register here
                        </Link>
                    </p>

                </div>
            </div>
          </div>
        </div>
    );
}
