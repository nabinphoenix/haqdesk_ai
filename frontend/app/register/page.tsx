"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { AlertCircle, ArrowLeft } from "lucide-react";
import FormField from "@/components/ui/FormField";
import PasswordField from "@/components/ui/PasswordField";
import ValidationMessage from "@/components/ui/ValidationMessage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullNameTouched, setFullNameTouched] = useState(false);
  const [businessNameTouched, setBusinessNameTouched] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const emailIsValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const fullNameIsValid = fullName.trim().length > 0;
  const businessNameIsValid = businessName.trim().length > 0;
  const passwordMeetsMinimum = password.length >= 6;
  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;
  const strengthScore = [
    password.length >= 6,
    password.length >= 10,
    /[A-Z]/.test(password) && /[a-z]/.test(password),
    /\d/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ].filter(Boolean).length;
  const strength = strengthScore <= 1 ? "Weak" : strengthScore <= 3 ? "Fair" : "Strong";
  const strengthTone = strength === "Strong" ? "success" : strength === "Fair" ? "warning" : "error";
  const filledStrengthSegments = password ? Math.max(1, Math.ceil((strengthScore / 5) * 3)) : 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setFullNameTouched(true);
    setBusinessNameTouched(true);
    setEmailTouched(true);

    if (!fullNameIsValid) {
      setError("Full name is required.");
      return;
    }
    if (!businessNameIsValid) {
      setError("Business name is required.");
      return;
    }
    if (!emailIsValid) {
      setError("Enter a valid email address.");
      return;
    }
    if (!passwordMeetsMinimum) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (!passwordsMatch) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: fullName.trim(),
          email: email.trim(),
          password,
          business_name: businessName.trim(),
        }),
      });
      const data = await response.json();

      if (response.ok) {
        toast.success("Account created!");
        router.push("/login");
      } else {
        const errorMessage = data.detail || "Registration failed.";
        setError(errorMessage);
        toast.error(errorMessage);
      }
    } catch {
      setError("Cannot connect to server.");
      toast.error("Cannot connect to server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen overflow-y-auto bg-background bg-mesh-gradient px-6 py-16 font-body antialiased">
      <div className="fixed left-1/4 top-1/4 -z-10 h-[400px] w-[400px] rounded-full bg-[#6D4AE208] blur-[100px]" />
      <div className="fixed bottom-1/4 right-1/4 -z-10 h-[400px] w-[400px] rounded-full bg-[#06B6D408] blur-[100px]" />

      <Link
        href="/"
        className="fixed left-6 top-6 flex items-center gap-2 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
      >
        <ArrowLeft size={15} aria-hidden="true" />
        Back to home
      </Link>

      <main className="card-glossy relative mx-auto w-full max-w-md rounded-[var(--radius-card)] p-6 sm:p-10">
        <header className="mb-8 text-center">
          <div
            className="hover-glow mx-auto flex h-16 w-16 items-center justify-center rounded-[var(--radius-card)] shadow-xl transition-transform duration-500 hover:scale-105"
            style={{ background: "var(--accent)" }}
          >
            <img src="/images/HaqDesk.png" alt="HaqDesk AI" className="h-12 w-12 object-contain" />
          </div>
          <h1 className="mt-6 text-3xl font-black tracking-tighter text-[var(--text-primary)]">
            HaqDesk<span className="text-[var(--accent)]">AI</span>
          </h1>
          <p className="mt-2 text-[11px] font-bold uppercase tracking-[0.16em] text-[var(--text-secondary)]">
            Create your account
          </p>
        </header>

        <form onSubmit={handleSubmit} noValidate>
          {error ? (
            <div
              role="alert"
              className="mb-4 flex items-center justify-center gap-2 rounded-[var(--radius-card)] border border-[var(--error-border)] bg-[var(--error-surface)] p-4 text-center text-xs font-bold text-[var(--error-foreground)]"
            >
              <AlertCircle size={15} aria-hidden="true" />
              {error}
            </div>
          ) : null}

          <div className="space-y-4">
            <FormField
              id="register-full-name"
              label="Full Name"
              hint={
                fullNameTouched && !fullNameIsValid ? (
                  <ValidationMessage tone="error">Full name is required.</ValidationMessage>
                ) : undefined
              }
            >
              <input
                id="register-full-name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                onBlur={() => setFullNameTouched(true)}
                aria-invalid={fullNameTouched && !fullNameIsValid}
                data-valid={fullNameTouched && fullNameIsValid ? "true" : undefined}
                className="ds-input"
                placeholder="Your full name"
                required
              />
            </FormField>

            <FormField
              id="register-business-name"
              label="Business Name"
              hint={
                businessNameTouched && !businessNameIsValid ? (
                  <ValidationMessage tone="error">Business name is required.</ValidationMessage>
                ) : undefined
              }
            >
              <input
                id="register-business-name"
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                onBlur={() => setBusinessNameTouched(true)}
                aria-invalid={businessNameTouched && !businessNameIsValid}
                data-valid={businessNameTouched && businessNameIsValid ? "true" : undefined}
                className="ds-input"
                placeholder="Your business name"
                required
              />
            </FormField>

            <FormField
              id="register-email"
              label="Email"
              hint={
                emailTouched && email ? (
                  <ValidationMessage tone={emailIsValid ? "success" : "error"}>
                    {emailIsValid ? "Email format looks good." : "Enter a valid email address."}
                  </ValidationMessage>
                ) : undefined
              }
            >
              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => setEmailTouched(true)}
                aria-invalid={emailTouched && !!email && !emailIsValid}
                data-valid={emailTouched && emailIsValid ? "true" : undefined}
                className="ds-input"
                placeholder="you@example.com"
                required
              />
            </FormField>
          </div>

          <div className="mt-6 space-y-3" role="group" aria-label="Create a password">
            <PasswordField
              id="register-password"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={!!password && !passwordMeetsMinimum}
              data-valid={passwordMeetsMinimum ? "true" : undefined}
              placeholder="••••••••"
              required
              minLength={6}
              hint={
                <div className="space-y-2">
                  <div className="flex gap-1" aria-label={password ? `Password strength: ${strength}` : "Password strength"}>
                    {[1, 2, 3].map((level) => (
                      <span
                        key={level}
                        className="h-1.5 flex-1 rounded-full"
                        style={{
                          background:
                            level <= filledStrengthSegments
                              ? strength === "Strong"
                                ? "var(--success)"
                                : strength === "Fair"
                                  ? "var(--warning)"
                                  : "var(--error)"
                              : "var(--border)",
                        }}
                      />
                    ))}
                  </div>
                  <ValidationMessage tone={password ? strengthTone : "neutral"}>
                    {password ? `${strength} password · ` : ""}Use at least 6 characters.
                  </ValidationMessage>
                </div>
              }
            />

            <PasswordField
              id="register-confirm-password"
              label="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              aria-invalid={!!confirmPassword && !passwordsMatch}
              data-valid={passwordsMatch ? "true" : undefined}
              placeholder="••••••••"
              required
              minLength={6}
              hint={
                confirmPassword ? (
                  <ValidationMessage tone={passwordsMatch ? "success" : "error"}>
                    {passwordsMatch ? "Passwords match." : "Passwords do not match."}
                  </ValidationMessage>
                ) : undefined
              }
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="ds-button ds-button-primary mt-6 w-full uppercase tracking-[0.14em] shadow-xl shadow-[#6D4AE2]/20"
          >
            {loading ? (
              <>
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Creating account…
              </>
            ) : (
              "Create account"
            )}
          </button>

          <section className="mt-8 border-t border-[var(--border)] pt-8" aria-label="Alternative sign-up method">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-[var(--border)]" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-secondary)]">or</span>
              <div className="h-px flex-1 bg-[var(--border)]" />
            </div>
            <button
              type="button"
              onClick={() => (window.location.href = `${API_URL}/api/v1/auth/google`)}
              className="ds-button ds-button-secondary mt-4 w-full"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4" />
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853" />
                <path d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05" />
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 6.294C4.672 4.169 6.656 3.58 9 3.58z" fill="#EA4335" />
              </svg>
              Continue with Google
            </button>
          </section>

          <p className="mt-6 text-center text-xs text-[var(--text-secondary)]">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-[var(--accent)]">
              Sign in
            </Link>
          </p>
        </form>
      </main>
    </div>
  );
}
