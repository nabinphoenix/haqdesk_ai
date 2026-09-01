"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { AlertCircle, CheckCircle2, UserPlus, Shield, Loader2 } from "lucide-react";
import PasswordField from "@/components/ui/PasswordField";
import ThemeLogo from "@/components/ui/ThemeLogo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function AcceptInviteContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const token = searchParams.get("token") || "";
    const oauthError = searchParams.get("oauth_error");

    const OAUTH_ERROR_MESSAGES: Record<string, string> = {
        invite_email_mismatch: "Please choose the Google account that matches the email address in this invitation.",
        invalid_invitation: "This invitation is invalid, revoked, or has already been used.",
        expired_invitation: "This invitation has expired. Ask your business administrator for a new one.",
        email_already_registered: "An account already exists for this email. Sign in instead or ask your administrator for help.",
        unverified_email: "Your Google email address is not verified.",
        oauth_failed: "Google authentication could not be completed. Please try again.",
    };

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState(
        oauthError ? (OAUTH_ERROR_MESSAGES[oauthError] || "Google authentication could not be completed.") : ""
    );
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
                body: JSON.stringify({ invite_token: token, name, email, password }),
            });

            const data = await res.json();

            if (res.ok) {
                setSuccess(true);
                toast.success("Welcome to the team!");

                setTimeout(() => {
                    router.push("/login");
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
        agent: "text-[var(--success-foreground)] bg-[var(--success-surface)] border-[var(--success-border)]",
        supervisor: "text-accent-glow bg-accent/10 border-accent/20",
        business_admin: "text-accent-glow bg-accent-glow/10 border-accent-glow/20",
        admin: "text-accent-glow bg-accent-glow/10 border-accent-glow/20",
    };

    const ROLE_LABELS: Record<string, string> = {
        agent: "Agent",
        supervisor: "Supervisor",
        business_admin: "Admin",
        admin: "Admin",
    };

    return (
        <div className="min-h-screen flex bg-background">

            {/* LEFT PANEL — branding */}
            <div className="hidden lg:flex w-[45%] flex-col justify-between p-12 relative overflow-hidden">

                {/* Background glows */}
                <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-accent/20 rounded-full blur-[120px] -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
                <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-[var(--success-surface)] rounded-full blur-[100px] translate-x-1/2 translate-y-1/2 pointer-events-none" />

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
                        <UserPlus size={14} className="text-[var(--success-foreground)]" />
                        <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Team Invitation</span>
                    </div>
                    <h2 className="text-4xl font-black text-foreground leading-tight tracking-tight mb-4">
                        You&apos;ve been<br />
                        invited to<br />
                        <span className="text-[var(--success-foreground)]">join the team.</span>
                    </h2>
                    <p className="text-muted-foreground text-[14px] leading-relaxed max-w-sm">
                        Create your account to start collaborating with your team on HaqDesk AI.
                        You&apos;ll have access to the unified inbox, AI-powered drafts, and more.
                    </p>

                    {/* Feature pills */}
                    <div className="flex flex-wrap gap-2 mt-8">
                        {["Unified Inbox", "AI Draft Replies", "Real-time Chat", "Team Collaboration"].map((f) => (
                            <span key={f} className="text-[11px] font-medium text-muted-foreground bg-surface-wash border border-border rounded-full px-3 py-1">
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
                        <div key={s.label} className="rounded-xl border border-border bg-surface-wash p-3 text-center">
                            <p className="text-lg font-black text-foreground">{s.value}</p>
                            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{s.label}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* RIGHT PANEL — form */}
            <div className="flex-1 flex items-center justify-center p-6 relative">

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

                <div className="w-full max-w-[420px]">

                    {/* Loading state */}
                    {validating && (
                        <div className="flex flex-col items-center gap-4 py-20">
                            <Loader2 size={32} className="text-accent-glow animate-spin" />
                            <p className="text-[13px] text-muted-foreground">Validating your invitation...</p>
                        </div>
                    )}

                    {/* Error state (no valid invite) */}
                    {!validating && !inviteData && (
                        <div className="flex flex-col items-center gap-4 py-20 text-center">
                            <div className="w-14 h-14 rounded-2xl bg-[var(--error-surface)] border border-[var(--error-border)] flex items-center justify-center">
                                <AlertCircle size={24} className="text-[var(--error-foreground)]" />
                            </div>
                            <div>
                                <h2 className="text-xl font-black text-foreground mb-2">Invalid Invitation</h2>
                                <p className="text-[13px] text-muted-foreground max-w-xs">
                                    {error || "This invitation link is invalid or has expired."}
                                </p>
                            </div>
                            <Link
                                href="/login"
                                className="mt-4 px-6 py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-on-accent text-[13px] font-semibold transition-all"
                            >
                                Go to Login
                            </Link>
                        </div>
                    )}

                    {/* Success state */}
                    {success && (
                        <div className="flex flex-col items-center gap-4 py-20 text-center">
                            <div className="w-14 h-14 rounded-2xl bg-[var(--success-surface)] border border-[var(--success-border)] flex items-center justify-center">
                                <CheckCircle2 size={28} className="text-[var(--success-foreground)]" />
                            </div>
                            <div>
                                <h2 className="text-xl font-black text-foreground mb-2">Welcome to the team!</h2>
                                <p className="text-[13px] text-muted-foreground">
                                Your account has been created. Redirecting to login...
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
                                <h1 className="text-2xl font-black text-foreground tracking-tight mb-1">
                                    Join {inviteData.business_name}
                                </h1>
                                <p className="text-[13px] text-muted-foreground">
                                    Create your account to accept the invitation
                                </p>
                            </div>

                            {/* Invite info card */}
                            <div className="p-4 rounded-xl border border-border bg-surface-wash mb-6">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-accent/20 border border-accent/30 flex items-center justify-center">
                                        <Shield size={18} className="text-accent-glow" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-[12px] text-muted-foreground mb-0.5">Invited as</p>
                                        <div className="flex items-center gap-2">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-lg text-[10px] font-black uppercase tracking-wider border ${ROLE_STYLES[inviteData.role] || ROLE_STYLES.agent}`}>
                                                {ROLE_LABELS[inviteData.role] || inviteData.role}
                                            </span>
                                            <span className="text-[11px] text-muted-foreground truncate">
                                                at {inviteData.business_name}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Error */}
                            {error && (
                                <div className="flex items-center gap-2 p-3 rounded-xl bg-[var(--error-surface)] border border-[var(--error-border)] text-[var(--error-foreground)] text-[12px] mb-4">
                                    <AlertCircle size={14} className="shrink-0" />
                                    {error}
                                </div>
                            )}

                            {/* Google uses the same invitation token so the backend can
                                assign this member to the invited business and role. */}
                            <button
                                type="button"
                                onClick={() => {
                                    window.location.href = `${API_URL}/api/v1/auth/google?invite_token=${encodeURIComponent(token)}`;
                                }}
                                className="w-full flex items-center justify-center gap-3 py-2.5 rounded-xl border border-border bg-surface-wash text-[13px] font-medium text-foreground hover:bg-surface-wash transition-all mb-5"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="18" height="18" aria-hidden="true">
                                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.69 1.22 9.17 3.24l6.85-6.85C36.93 2.57 30.84 0 24 0 14.61 0 6.5 5.23 2.45 12.79l7.92 6.15C12.33 13.03 17.71 9.5 24 9.5z" />
                                    <path fill="#4285F4" d="M46.54 24.58c0-1.63-.15-3.2-.42-4.71H24v9.03h12.74c-.55 2.95-2.2 5.46-4.71 7.15l7.45 5.78c4.33-4 6.86-9.89 6.86-17.25z" />
                                    <path fill="#FBBC05" d="M10.37 28.94c-.53-1.53-.84-3.18-.84-4.94s.31-3.41.84-4.94l-7.92-6.15C1.08 16.12 0 19.96 0 24c0 4.04 1.08 7.88 2.45 11.29l7.92-6.15z" />
                                    <path fill="#34A853" d="M24 48c6.84 0 12.93-2.27 17.22-6.15l-7.45-5.78c-2.07 1.39-4.71 2.22-7.77 2.22-6.29 0-11.66-3.53-14.36-8.66l-7.92 6.15C6.5 42.77 14.61 48 24 48z" />
                                </svg>
                                Continue with Google
                            </button>

                            <div className="flex items-center gap-3 mb-5">
                                <div className="flex-1 h-px bg-surface-wash" />
                                <span className="text-[11px] text-muted-foreground uppercase tracking-wider">or create with password</span>
                                <div className="flex-1 h-px bg-surface-wash" />
                            </div>

                            {/* Form */}
                            <form onSubmit={handleSubmit} className="space-y-4">

                                {/* Email (read-only) */}
                                <div>
                                    <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                                        Email Address
                                    </label>
                                    <input
                                        type="email"
                                        value={email}
                                        readOnly
                                        className="w-full px-4 py-2.5 rounded-xl border border-border bg-surface-wash text-muted-foreground text-[13px] cursor-not-allowed"
                                    />
                                    <p className="text-[10px] text-muted-foreground mt-1">This email was set by the invitation</p>
                                </div>

                                {/* Full Name */}
                                <div>
                                    <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                                        Full Name
                                    </label>
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="w-full px-4 py-2.5 rounded-xl border border-border bg-surface-wash text-foreground text-[13px] placeholder:text-muted-foreground focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                                        placeholder="Your full name"
                                        required
                                    />
                                </div>

                                {/* Password */}
                                <PasswordField
                                    id="invite-password"
                                    label="Password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    minLength={6}
                                />

                                {/* Confirm Password */}
                                <PasswordField
                                    id="invite-confirm-password"
                                    label="Confirm Password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    minLength={6}
                                />

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-on-accent text-[13px] font-semibold transition-all active:scale-95 disabled:opacity-60 disabled:cursor-wait flex items-center justify-center gap-2 mt-2"
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-3.5 h-3.5 border-2 border-on-accent border-t-transparent rounded-full animate-spin" />
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
                            <p className="text-center text-[12px] text-muted-foreground mt-5">
                                Already have an account?{" "}
                                <Link href="/login" className="text-accent-glow hover:text-purple-300 font-medium transition-colors">
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
                <div className="min-h-screen flex items-center justify-center bg-background">
                    <div className="w-6 h-6 border-2 border-accent-glow border-t-transparent rounded-full animate-spin" />
                </div>
            }
        >
            <AcceptInviteContent />
        </Suspense>
    );
}
