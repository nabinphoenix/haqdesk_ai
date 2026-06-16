"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { AlertCircle, Eye, EyeOff, CheckCircle2, UserPlus, Shield, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function AcceptInviteContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const token = searchParams.get("token") || "";

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [validating, setValidating] = useState(true);
    const [inviteData, setInviteData] = useState<{
        email: string;
        role: string;
        business_name: string;
        expires_at: string;
    } | null>(null);
    const [success, setSuccess] = useState(false);

    // Validate the invite token on mount
    useEffect(() => {
        if (!token) {
            setError("No invitation token provided. Please use the link from your invitation email.");
            setValidating(false);
            return;
        }

        const validateToken = async () => {
            try {
                const res = await fetch(
                    `${API_URL}/api/v1/team/validate-invite?token=${encodeURIComponent(token)}`
                );
                const data = await res.json();
                if (res.ok) {
                    setInviteData(data);
                    setEmail(data.email);
                } else {
                    setError(data.detail || "Invalid or expired invitation.");
                }
            } catch {
                setError("Cannot connect to server. Please try again later.");
            } finally {
                setValidating(false);
            }
        };

        validateToken();
    }, [token]);

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
            const res = await fetch(`${API_URL}/api/v1/team/accept-invite`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token, name, email, password }),
            });

            const data = await res.json();

            if (res.ok) {
                // Store auth data
                localStorage.setItem("token", data.access_token);
                localStorage.setItem("userRole", data.user.role);
                localStorage.setItem("userName", data.user.name);
                localStorage.setItem("userEmail", data.user.email);
                if (data.user.business_id) {
                    localStorage.setItem("userBusinessId", data.user.business_id);
                }

                setSuccess(true);
                toast.success("Welcome to the team!");

                setTimeout(() => {
                    router.push("/inbox");
                }, 2000);
            } else {
                const errorMsg = data.detail || "Failed to create account. Please try again.";
                setError(errorMsg);
                toast.error(errorMsg);
            }
        } catch {
            setError("Cannot connect to server. Please try again.");
            toast.error("Cannot connect to server.");
        } finally {
            setLoading(false);
        }
    };

    // ─── Role badge formatting ───
    const ROLE_STYLES: Record<string, string> = {
        agent: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
        supervisor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
        business_admin: "text-[#818CF8] bg-[#818CF8]/10 border-[#818CF8]/20",
        admin: "text-[#818CF8] bg-[#818CF8]/10 border-[#818CF8]/20",
    };

    const ROLE_LABELS: Record<string, string> = {
        agent: "Agent",
        supervisor: "Supervisor",
        business_admin: "Admin",
        admin: "Admin",
    };

    return (
        <div className="min-h-screen flex bg-[#090514]">

            {/* LEFT PANEL — branding */}
            <div className="hidden lg:flex w-[45%] flex-col justify-between p-12 relative overflow-hidden">

                {/* Background glows */}
                <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-[#6D4AE2]/20 rounded-full blur-[120px] -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
                <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-emerald-500/10 rounded-full blur-[100px] translate-x-1/2 translate-y-1/2 pointer-events-none" />

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
                        <UserPlus size={14} className="text-emerald-400" />
                        <span className="text-[11px] font-medium text-gray-300 uppercase tracking-wider">Team Invitation</span>
                    </div>
                    <h2 className="text-4xl font-black text-white leading-tight tracking-tight mb-4">
                        You&apos;ve been<br />
                        invited to<br />
                        <span className="text-emerald-400">join the team.</span>
                    </h2>
                    <p className="text-gray-400 text-[14px] leading-relaxed max-w-sm">
                        Create your account to start collaborating with your team on HaqDesk AI.
                        You&apos;ll have access to the unified inbox, AI-powered drafts, and more.
                    </p>

                    {/* Feature pills */}
                    <div className="flex flex-wrap gap-2 mt-8">
                        {["Unified Inbox", "AI Draft Replies", "Real-time Chat", "Team Collaboration"].map((f) => (
                            <span key={f} className="text-[11px] font-medium text-gray-300 bg-white/5 border border-white/10 rounded-full px-3 py-1">
                                {f}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Bottom info */}
                <div className="grid grid-cols-3 gap-4 z-10">
                    {[
                        { value: "Secure", label: "Encrypted" },
                        { value: "7 days", label: "Invite Expiry" },
                        { value: "Instant", label: "Access" },
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

                <div className="w-full max-w-[420px]">

                    {/* Loading state */}
                    {validating && (
                        <div className="flex flex-col items-center gap-4 py-20">
                            <Loader2 size={32} className="text-[#818CF8] animate-spin" />
                            <p className="text-[13px] text-gray-400">Validating your invitation...</p>
                        </div>
                    )}

                    {/* Error state (no valid invite) */}
                    {!validating && !inviteData && (
                        <div className="flex flex-col items-center gap-4 py-20 text-center">
                            <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                                <AlertCircle size={24} className="text-red-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-black text-white mb-2">Invalid Invitation</h2>
                                <p className="text-[13px] text-gray-400 max-w-xs">
                                    {error || "This invitation link is invalid or has expired."}
                                </p>
                            </div>
                            <Link
                                href="/login"
                                className="mt-4 px-6 py-2.5 rounded-xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[13px] font-semibold transition-all"
                            >
                                Go to Login
                            </Link>
                        </div>
                    )}

                    {/* Success state */}
                    {success && (
                        <div className="flex flex-col items-center gap-4 py-20 text-center">
                            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                                <CheckCircle2 size={28} className="text-emerald-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-black text-white mb-2">Welcome to the team!</h2>
                                <p className="text-[13px] text-gray-400">
                                    Your account has been created. Redirecting to inbox...
                                </p>
                            </div>
                            <div className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mt-2" />
                        </div>
                    )}

                    {/* Form state */}
                    {!validating && inviteData && !success && (
                        <>
                            {/* Header */}
                            <div className="mb-6">
                                <h1 className="text-2xl font-black text-white tracking-tight mb-1">
                                    Join {inviteData.business_name}
                                </h1>
                                <p className="text-[13px] text-gray-400">
                                    Create your account to accept the invitation
                                </p>
                            </div>

                            {/* Invite info card */}
                            <div className="p-4 rounded-xl border border-white/10 bg-white/[0.03] mb-6">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-[#6D4AE2]/20 border border-[#6D4AE2]/30 flex items-center justify-center">
                                        <Shield size={18} className="text-[#818CF8]" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-[12px] text-gray-400 mb-0.5">Invited as</p>
                                        <div className="flex items-center gap-2">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-lg text-[10px] font-black uppercase tracking-wider border ${ROLE_STYLES[inviteData.role] || ROLE_STYLES.agent}`}>
                                                {ROLE_LABELS[inviteData.role] || inviteData.role}
                                            </span>
                                            <span className="text-[11px] text-gray-500 truncate">
                                                at {inviteData.business_name}
                                            </span>
                                        </div>
                                    </div>
                                </div>
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

                                {/* Email (read-only) */}
                                <div>
                                    <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                                        Email Address
                                    </label>
                                    <input
                                        type="email"
                                        value={email}
                                        readOnly
                                        className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/[0.02] text-gray-400 text-[13px] cursor-not-allowed"
                                    />
                                    <p className="text-[10px] text-gray-600 mt-1">This email was set by the invitation</p>
                                </div>

                                {/* Full Name */}
                                <div>
                                    <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                                        Full Name
                                    </label>
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-600 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all"
                                        placeholder="Your full name"
                                        required
                                    />
                                </div>

                                {/* Password */}
                                <div>
                                    <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                                        Password
                                    </label>
                                    <div className="relative">
                                        <input
                                            type={showPassword ? "text" : "password"}
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="w-full px-4 py-2.5 pr-10 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-600 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all"
                                            placeholder="••••••••"
                                            required
                                            minLength={6}
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

                                {/* Confirm Password */}
                                <div>
                                    <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                                        Confirm Password
                                    </label>
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-[13px] placeholder-gray-600 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all"
                                        placeholder="••••••••"
                                        required
                                        minLength={6}
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-2.5 rounded-xl bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white text-[13px] font-semibold transition-all active:scale-95 disabled:opacity-60 disabled:cursor-wait flex items-center justify-center gap-2 mt-2"
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                            Creating account...
                                        </>
                                    ) : (
                                        <>
                                            <UserPlus size={14} />
                                            Create Account & Join
                                        </>
                                    )}
                                </button>
                            </form>

                            {/* Existing account link */}
                            <p className="text-center text-[12px] text-gray-500 mt-5">
                                Already have an account?{" "}
                                <Link href="/login" className="text-purple-400 hover:text-purple-300 font-medium transition-colors">
                                    Sign in instead
                                </Link>
                            </p>
                        </>
                    )}

                </div>
            </div>
        </div>
    );
}

export default function AcceptInvitePage() {
    return (
        <Suspense
            fallback={
                <div className="min-h-screen flex items-center justify-center bg-[#090514]">
                    <div className="w-6 h-6 border-2 border-[#818CF8] border-t-transparent rounded-full animate-spin" />
                </div>
            }
        >
            <AcceptInviteContent />
        </Suspense>
    );
}
