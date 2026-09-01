"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { BarChart3, BookOpen, ChevronDown, Inbox, LogIn, LogOut, Menu, MessageSquare, Plus, Settings, Shield, UserRound, Users, X } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { useTheme } from "next-themes";

const PROFILE_IMAGE_CACHE_LIMIT = 256 * 1024;

function readCachedProfileImage(): string | null {
  try {
    const cached = localStorage.getItem("profileImage");
    if (!cached) return null;
    if (cached.length > PROFILE_IMAGE_CACHE_LIMIT) {
      localStorage.removeItem("profileImage");
      return null;
    }
    return cached;
  } catch {
    return null;
  }
}

function cacheProfileImage(image: string | null) {
  try {
    if (image && image.length <= PROFILE_IMAGE_CACHE_LIMIT) {
      localStorage.setItem("profileImage", image);
    } else {
      localStorage.removeItem("profileImage");
    }
  } catch {
    // A full/private storage area must not break profile updates or navigation.
    try { localStorage.removeItem("profileImage"); } catch { /* ignore */ }
  }
}
const ALL_NAV_ITEMS = [
  { name: "Inbox", path: "/inbox", roles: ["business_admin", "supervisor", "agent"], icon: Inbox },
  { name: "Messages", path: "/messages", roles: ["business_admin", "supervisor", "agent"], icon: MessageSquare },
  { name: "Knowledge", path: "/knowledge", roles: ["business_admin"], icon: BookOpen },
  { name: "Team", path: "/team", roles: ["business_admin", "supervisor"], icon: Users },
  { name: "Analytics", path: "/analytics", roles: ["business_admin", "supervisor"], icon: BarChart3 },
  { name: "Settings", path: "/settings", roles: ["business_admin"], icon: Settings },
  { name: "Super Admin", path: "/super-admin", roles: ["super_admin"], icon: Shield },
];

export default function AppNavbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [userName, setUserName] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const { resolvedTheme } = useTheme();
  const logoSrc = resolvedTheme === "dark"
    ? "/images/Haqdesk_AI_Dark.png"
    : "/images/Haqdesk_AI_Light.png";
  const navItems = ALL_NAV_ITEMS.filter(
    (item) => userRole !== null && item.roles.includes(userRole) && item.name !== 'Super Admin'
  );

  useEffect(() => {
    setMounted(true);
    const savedImage = readCachedProfileImage();
    if (savedImage) setProfileImage(savedImage);
  }, []);

  useEffect(() => {
    // Prefer the clean default avatar in the shared navigation. It avoids
    // broken remote images and stale cached image data on every account.
    if (profileImage) {
      setProfileImage(null);
      cacheProfileImage(null);
    }
  }, [profileImage]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest("[data-profile-menu]")) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("token");
      const storedName = localStorage.getItem("userName");
      const storedRole = localStorage.getItem("userRole");

      if (token) {
        setIsLoggedIn(true);
        if (storedName) setUserName(storedName);
        if (storedRole) setUserRole(storedRole);
        setLoading(false);

        // Fetch user profile from backend
        fetchWithAuth("/api/v1/auth/me")
          .then((res) => {
            if (res.ok) {
              res.json().then((data) => {
                if (data.role) {
                  setUserRole(data.role);
                  localStorage.setItem("userRole", data.role);
                }
                if (data.avatar_url) {
                  setProfileImage(data.avatar_url);
                  cacheProfileImage(data.avatar_url);
                }
                if (data.name) {
                  setUserName(data.name);
                  localStorage.setItem("userName", data.name);
                }
                // Onboarding is routed only by the one-time Google OAuth response.
              });
            }
          })
          .catch(() => {
            // Keep the navigation usable with cached local profile data when the API is restarting.
          });
      } else {
        setIsLoggedIn(false);
        setUserName(null);
        setUserRole(null);
        setLoading(false);

        const protectedRoutes = ["/inbox", "/messages", "/team", "/knowledge", "/analytics", "/settings", "/super-admin", "/supervisor", "/agent"];
        if (protectedRoutes.some((route) => pathname === route || pathname.startsWith(route + "/"))) {
          router.push("/login?redirect=" + pathname);
        }
      }
    };
    checkAuth();
    window.addEventListener("storage", checkAuth);
    return () => window.removeEventListener("storage", checkAuth);
  }, [pathname, router]);

  useEffect(() => {
    if (!isLoggedIn) return;
    const heartbeat = () => {
      if (document.visibilityState === "visible") {
        fetchWithAuth("/api/v1/auth/presence", { method: "POST" }).catch(() => undefined);
      }
    };
    heartbeat();
    const interval = window.setInterval(heartbeat, 30000);
    document.addEventListener("visibilitychange", heartbeat);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", heartbeat);
    };
  }, [isLoggedIn]);

  const handleLogout = async () => {
    try {
      await fetchWithAuth("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // Local logout must still complete if the API is temporarily unavailable.
    }
    localStorage.clear();
    setIsLoggedIn(false);
    router.push("/login");
  };

  const PUBLIC_PAGES = ["/login", "/register", "/accept-invite", "/forgot-password", "/reset-password", "/onboarding/business"];
  if (PUBLIC_PAGES.some((p) => pathname === p || pathname.startsWith(p + "?"))) return null;

  if (!mounted) {
    return <div className="fixed top-0 left-0 right-0 h-[60px] glass z-50" />;
  }

  return (
    <>
      <motion.nav
        initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 h-[60px] glass z-50"
    >
      <div className="max-w-[1120px] mx-auto px-4 sm:px-6 h-full flex items-center justify-between">

        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group shrink-0">
          <div className="h-[50px] w-[50px] overflow-hidden transition-transform group-hover:scale-105 shrink-0">
            <img
              src={logoSrc}
              alt="HaqDesk AI"
              className="w-full h-full object-contain"
            />
          </div>
          <div className="flex flex-col leading-none">
            <span className="font-heading font-bold text-[15px] tracking-tight text-black dark:text-foreground">
              HaqDesk<span style={{ color: "var(--accent)" }}> AI</span>
            </span>
            <span className="text-[9.5px] font-medium uppercase tracking-widest text-black dark:text-muted-foreground mt-0.5 hidden sm:block">
              AI-Powered Support
            </span>
          </div>
        </Link>

        {/* Center Nav */}
        <nav className="hidden lg:flex items-center gap-2">
          {navItems.map((item) => {
              const isActive = pathname === item.path;
              const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.path}
                className={`${
                  isActive
                    ? "font-medium text-black dark:text-foreground bg-surface-wash dark:bg-surface-wash"
                    : "text-black dark:text-muted-foreground hover:text-black dark:hover:text-foreground hover:bg-surface-wash dark:hover:bg-surface-wash"
                } flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13.5px] transition-colors duration-150`}
              >
                <Icon size={15} strokeWidth={1.5} className="shrink-0" />
                <span className="font-heading font-medium tracking-tight">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right side */}
        <div className="hidden lg:flex items-center gap-2 min-w-[180px] justify-end">
          {!loading && (
            isLoggedIn ? (
              <div className="flex items-center gap-2">

                {/* Theme toggle */}
                <ThemeToggle />

                {/* Divider */}
                <div className="w-px h-5 bg-surface-wash mx-1" />

                {/* Clickable profile */}
                <div className="relative" data-profile-menu>
                  <button
                    onClick={() => setShowProfileMenu(!showProfileMenu)}
                    className="flex items-center gap-2.5 rounded-xl px-2 py-1.5 hover:bg-surface-wash transition-all"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-on-accent text-sm font-bold shrink-0 overflow-hidden">
                      {profileImage ? (
                        <img src={profileImage} alt="profile" className="w-full h-full object-cover" />
                      ) : (
                        userName ? userName.charAt(0).toUpperCase() : "N"
                      )}
                    </div>
                    <div className="flex flex-col leading-tight text-left">
                      <span className="text-[13px] font-semibold text-black dark:text-foreground">
                        {userName || "User"}
                      </span>
                      <span className="text-[10px] font-medium text-black dark:text-accent-glow uppercase tracking-wider">
                        {userRole || "Admin"}
                      </span>
                    </div>
                    <ChevronDown size={12} className="text-black dark:text-muted-foreground ml-1" />
                  </button>

                  {/* Dropdown */}
                  {showProfileMenu && (
                    <div className="absolute right-0 top-full mt-2 w-48 rounded-xl border border-border bg-surface shadow-2xl overflow-hidden z-[100]">
                      <button
                        onClick={() => { setShowProfileModal(true); setShowProfileMenu(false); }}
                        className="w-full flex items-center gap-3 px-4 py-3 text-[13px] text-black dark:text-muted-foreground hover:bg-surface-wash hover:text-black dark:hover:text-foreground transition-all text-left"
                      >
                        <UserRound size={14} />
                        Edit Profile
                      </button>
                      <div className="h-px bg-surface-wash" />
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-3 text-[13px] text-[var(--error-foreground)] hover:bg-[var(--error-surface)] transition-all text-left"
                      >
                        <LogOut size={14} />
                        Logout
                      </button>
                    </div>
                  )}
                </div>

              </div>
            ) : (
              <div className="flex items-center gap-2"><ThemeToggle /><Link
                  href="/login"
                  className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-1.5 text-[13.5px] font-medium text-on-accent transition-all duration-150 hover:-translate-y-px hover:bg-accent-hover active:translate-y-0"
                ><LogIn size={14} />Sign in</Link></div>
            )
          )}
        </div>

        {/* Mobile toggle */}
        <div className="flex lg:hidden items-center gap-2">
          <ThemeToggle className="h-[34px] w-[34px]" iconSize={15} />
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-black dark:text-muted-foreground hover:text-black dark:hover:text-foreground transition-colors"
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="lg:hidden overflow-hidden glass border-t border-border px-6 py-4 flex flex-col gap-2"
          >
            {navItems.map((item) => {
                const isActive = pathname === item.path;
                const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`${
                    isActive
                      ? "font-medium text-black dark:text-foreground bg-surface-wash dark:bg-surface-wash"
                      : "text-black dark:text-muted-foreground hover:text-black dark:hover:text-foreground hover:bg-surface-wash dark:hover:bg-surface-wash"
                  } flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13.5px] transition-colors duration-150`}
                >
                  <Icon size={15} strokeWidth={1.5} className="shrink-0" />
                  <span className="font-heading font-medium tracking-tight">{item.name}</span>
                </Link>
              );
            })}

            <div className="h-px bg-surface-wash my-2" />

            {!loading && isLoggedIn ? (
              <div className="flex items-center justify-between px-2 py-2">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-on-accent text-sm font-bold shrink-0">
                    {userName ? userName.charAt(0).toUpperCase() : "N"}
                  </div>
                  <div className="flex flex-col leading-tight">
                    <span className="text-[13px] font-semibold text-black dark:text-foreground">
                      {userName || "User"}
                    </span>
                    <span className="text-[10px] font-medium text-black dark:text-accent-glow uppercase tracking-wider">
                      {userRole || "Admin"}
                    </span>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="rounded-lg p-2 text-black dark:text-muted-foreground hover:bg-surface-wash hover:text-[var(--error-foreground)] transition-all"
                >
                  <LogOut size={16} />
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                onClick={() => setIsMobileMenuOpen(false)}
                className="flex items-center justify-center gap-1.5 px-4 py-2.5 bg-accent hover:bg-accent-hover text-on-accent rounded-lg text-xs font-medium transition-all"
              >
                Sign In
              </Link>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      </motion.nav>

      {/* Profile Edit Modal — outside nav so it is not clipped */}
      {showProfileModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-border bg-surface shadow-2xl p-6">

            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-foreground">Edit Profile</h2>
              <button
                onClick={() => setShowProfileModal(false)}
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-surface-wash hover:text-foreground transition-all"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex flex-col items-center mb-6">
              <div className="relative">
                <div className="h-20 w-20 rounded-full bg-accent flex items-center justify-center text-on-accent text-2xl font-bold overflow-hidden">
                  {profileImage ? (
                    <img src={profileImage} alt="profile" className="w-full h-full object-cover" />
                  ) : (
                    userName ? userName.charAt(0).toUpperCase() : "N"
                  )}
                </div>
                <label className="absolute bottom-0 right-0 flex h-7 w-7 cursor-pointer items-center justify-center rounded-full bg-accent hover:bg-accent-hover transition-all">
                  <Plus size={12} className="text-on-accent" />
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        const reader = new FileReader();
                        reader.onload = () => {
                          const result = reader.result as string;
                          setProfileImage(result);
                          cacheProfileImage(result);
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                  />
                </label>
              </div>
              <p className="text-xs text-muted-foreground mt-2">Click + to upload photo</p>
            </div>

            <div className="mb-4">
              <label className="block text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wider">Full Name</label>
              <input
                type="text"
                defaultValue={userName || ""}
                id="profile-name-input"
                className="w-full rounded-xl border border-border bg-surface-wash px-4 py-2.5 text-[13px] text-foreground placeholder:text-muted-foreground focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                placeholder="Your name"
              />
            </div>

            <div className="mb-6">
              <label className="block text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wider">Role</label>
              <input
                type="text"
                value={userRole || "Admin"}
                readOnly
                className="w-full rounded-xl border border-border bg-surface-wash px-4 py-2.5 text-[13px] text-muted-foreground cursor-not-allowed"
              />
            </div>

            <button
              onClick={async () => {
                const nameInput = document.getElementById("profile-name-input") as HTMLInputElement;
                let newName = userName;
                if (nameInput?.value) {
                  newName = nameInput.value;
                  setUserName(newName);
                  localStorage.setItem("userName", newName);
                }

                try {
                  await fetchWithAuth("/api/v1/auth/me", {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      name: newName,
                      avatar_url: profileImage
                    }),
                  });
                } catch (e) {
                  console.error("Failed to update profile", e);
                }

                setShowProfileModal(false);
              }}
              className="w-full rounded-xl bg-accent hover:bg-accent-hover py-2.5 text-[13px] font-semibold text-on-accent transition-all"
            >
              Save Changes
            </button>

          </div>
        </div>
      )}
    </>
  );
}
