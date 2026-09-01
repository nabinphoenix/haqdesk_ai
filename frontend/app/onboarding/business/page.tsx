"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, CheckCircle2, LogOut } from "lucide-react";
import { toast } from "sonner";
import ThemeLogo from "@/components/ui/ThemeLogo";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { fetchWithAuth } from "@/lib/api";

type BusinessForm = {
  name: string;
  email: string;
  website: string;
  phone: string;
  description: string;
};

const EMPTY_FORM: BusinessForm = {
  name: "",
  email: "",
  website: "",
  phone: "",
  description: "",
};

export default function BusinessOnboardingPage() {
  const router = useRouter();
  const [form, setForm] = useState<BusinessForm>(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      if (!localStorage.getItem("token")) {
        router.replace("/login");
        return;
      }

      try {
        const profileResponse = await fetchWithAuth("/api/v1/auth/me");
        if (!profileResponse.ok) {
          localStorage.removeItem("token");
          router.replace("/login");
          return;
        }

        const profile = await profileResponse.json();
        if (profile.role !== "business_admin") {
          router.replace(profile.role === "supervisor" ? "/supervisor" : profile.role === "agent" ? "/agent" : "/inbox");
          return;
        }
        if (!profile.needs_onboarding) {
          router.replace("/inbox");
          return;
        }

        const businessResponse = await fetchWithAuth("/api/v1/settings/business");
        if (!businessResponse.ok) {
          throw new Error("We could not load your business profile.");
        }
        const business = await businessResponse.json();
        if (!cancelled) {
          setForm({
            name: business.name?.endsWith("'s Business") ? "" : business.name || "",
            email: business.email || profile.email || "",
            website: business.website || "",
            phone: business.phone || "",
            description: business.description || "",
          });
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "We could not load your business profile.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [router]);

  const update = (key: keyof BusinessForm, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
    if (error) setError("");
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    const required: Array<[keyof BusinessForm, string]> = [
      ["name", "Business name"],
      ["email", "Business email"],
      ["website", "Website"],
      ["phone", "Phone number"],
    ];
    const missing = required.find(([key]) => !form[key].trim());
    if (missing) {
      setError(`${missing[1]} is required.`);
      return;
    }

    setSaving(true);
    try {
      const website = /^https?:\/\//i.test(form.website.trim())
        ? form.website.trim()
        : `https://${form.website.trim()}`;
      const response = await fetchWithAuth("/api/v1/settings/business", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, website }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Please check your business details and try again.");
      }

      localStorage.setItem("businessOnboardingComplete", "true");
      toast.success("Business profile saved. Welcome to HaqDesk AI!");
      router.replace("/inbox");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save your business profile.");
    } finally {
      setSaving(false);
    }
  };

  const signOut = () => {
    localStorage.clear();
    router.replace("/login");
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          Preparing your workspace...
        </div>
      </main>
    );
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-background px-5 py-8 text-foreground sm:px-8 sm:py-10">
      <div className="pointer-events-none absolute -left-40 -top-40 h-96 w-96 rounded-full bg-accent/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-52 -right-24 h-[34rem] w-[34rem] rounded-full bg-blue-500/10 blur-3xl" />

      <div className="relative mx-auto flex w-full max-w-6xl items-center justify-between">
        <Link href="/" aria-label="HaqDesk AI home" className="flex items-center gap-3">
          <ThemeLogo width={50} height={50} alt="HaqDesk AI" className="h-[50px] w-[50px] object-contain" />
          <div className="leading-tight">
            <p className="font-heading text-base font-bold tracking-tight">HaqDesk<span className="text-accent-glow"> AI</span></p>
            <p className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">Workspace setup</p>
          </div>
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle className="h-10 w-10" iconSize={17} />
          <button type="button" onClick={signOut} className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface/70 px-3 py-2 text-xs font-semibold text-muted-foreground transition hover:border-accent/40 hover:text-foreground" aria-label="Sign out">
            <LogOut size={14} />
            <span className="hidden sm:inline">Sign out</span>
          </button>
        </div>
      </div>

      <section className="relative mx-auto mt-10 grid w-full max-w-6xl gap-8 lg:mt-16 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
        <div className="max-w-xl">
          <div className="mb-5 inline-flex items-center gap-2 rounded-xl border border-accent/25 bg-accent/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-accent-glow">
            <Building2 size={14} />
            One last step
          </div>
          <h1 className="font-heading text-4xl font-black leading-[1.05] tracking-[-0.04em] sm:text-5xl">
            Tell us about your <span className="brand-gradient-text">business.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-7 text-muted-foreground sm:text-base">
            This information personalizes your inbox, notifications, and connected channels. You can update it anytime from Settings.
          </p>
          <div className="mt-8 space-y-3 text-sm text-muted-foreground">
            {["Your team sees the right business identity", "Replies and notifications use your contact details", "Connect channels whenever you are ready"].map((item) => (
              <div key={item} className="flex items-center gap-3">
                <CheckCircle2 size={17} className="shrink-0 text-accent-glow" />
                {item}
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={submit} className="rounded-3xl border border-border bg-surface/90 p-6 shadow-2xl shadow-slate-950/10 backdrop-blur-xl sm:p-8">
          <div className="mb-6">
            <h2 className="font-heading text-xl font-bold tracking-tight">Business profile</h2>
            <p className="mt-1 text-xs text-muted-foreground">Required fields are marked with an asterisk.</p>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <label className="sm:col-span-2">
              <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Business name *</span>
              <input required value={form.name} onChange={(event) => update("name", event.target.value)} placeholder="e.g. Acme Support" autoComplete="organization" className="ds-input" />
            </label>
            <label>
              <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Business email *</span>
              <input required type="email" value={form.email} onChange={(event) => update("email", event.target.value)} placeholder="support@yourbusiness.com" autoComplete="email" className="ds-input" />
            </label>
            <label>
              <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Phone number *</span>
              <input required type="tel" value={form.phone} onChange={(event) => update("phone", event.target.value)} placeholder="+977 98XXXXXXXX" autoComplete="tel" className="ds-input" />
            </label>
            <label className="sm:col-span-2">
              <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Website *</span>
              <input required type="text" value={form.website} onChange={(event) => update("website", event.target.value)} placeholder="https://yourbusiness.com" autoComplete="url" className="ds-input" />
            </label>
            <label className="sm:col-span-2">
              <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground">Short description <span className="font-normal normal-case tracking-normal">(optional)</span></span>
              <textarea rows={3} value={form.description} onChange={(event) => update("description", event.target.value)} placeholder="What does your business help customers with?" className="ds-input resize-none" />
            </label>
          </div>

          {error && <p role="alert" className="mt-5 rounded-xl border border-[var(--error-border)] bg-[var(--error-surface)] px-3 py-2.5 text-xs font-medium text-[var(--error-foreground)]">{error}</p>}

          <button type="submit" disabled={saving} className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 py-3.5 text-sm font-bold text-on-accent shadow-lg shadow-accent/25 transition hover:bg-accent-hover disabled:cursor-wait disabled:opacity-60">
            {saving ? "Saving profile..." : "Save and enter HaqDesk"}
            {!saving && <ArrowRight size={17} />}
          </button>
        </form>
      </section>
    </main>
  );
}