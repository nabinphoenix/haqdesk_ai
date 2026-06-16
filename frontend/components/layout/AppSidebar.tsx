"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon, LogOut } from "lucide-react";

const navItems = [
  {
    name: "Inbox",
    path: "/inbox",
    icon: (props: any) => (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
        <path d="M2 11h3a1 1 0 0 0 2 0h2a1 1 0 0 0 2 0h3" />
        <path d="M1.5 11l1-6.5A1.5 1.5 0 0 1 4 3.2h8a1.5 1.5 0 0 1 1.5 1.3l1 6.5" />
        <path d="M1.5 11v2.5A1.5 1.5 0 0 0 3 15h10a1.5 1.5 0 0 0 1.5-1.5V11" />
      </svg>
    ),
  },
  {
    name: "Team",
    path: "/team",
    icon: (props: any) => (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
        <path d="M11.5 13.5v-1a2.5 2.5 0 0 0-2.5-2.5h-4a2.5 2.5 0 0 0-2.5 2.5v1" />
        <circle cx="7" cy="5" r="2.5" />
        <path d="M14 13.5v-1a2.5 2.5 0 0 0-1.5-2.3" />
        <path d="M11.5 3.1a2.5 2.5 0 0 1 0 3.8" />
      </svg>
    ),
  },
  {
    name: "Knowledge",
    path: "/knowledge",
    icon: (props: any) => (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
        <path d="M1.5 13.5V3a1.5 1.5 0 0 1 1.5-1.5h4.5a.5.5 0 0 1 .5.5v11.5a.5.5 0 0 1-.5.5H3a1.5 1.5 0 0 1-1.5-1.5z" />
        <path d="M14.5 13.5V3a1.5 1.5 0 0 0-1.5-1.5H8.5a.5.5 0 0 0-.5.5v11.5a.5.5 0 0 0 .5.5H13a1.5 1.5 0 0 0 1.5-1.5z" />
      </svg>
    ),
  },
  {
    name: "Analytics",
    path: "/analytics",
    icon: (props: any) => (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
        <path d="M1.5 13.5h13" />
        <path d="M4 13.5V8.5" />
        <path d="M8 13.5V4.5" />
        <path d="M12 13.5v-6" />
      </svg>
    ),
  },
  {
    name: "Settings",
    path: "/settings",
    icon: (props: any) => (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
        <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V12a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
  {
    name: "Super Admin",
    path: "/super-admin",
    icon: (props: any) => (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
        <path d="M8 1l1.5 3 3.5.5-2.5 2.5.5 3.5L8 9l-3 1.5.5-3.5L3 4.5 6.5 4z" />
      </svg>
    ),
  },
];

export default function AppNavbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [userName, setUserName] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileImage, setProfileImage] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    const savedImage = localStorage.getItem("profileImage");
    if (savedImage) setProfileImage(savedImage);
  }, []);

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
        setUserName(storedName);
        setUserRole(storedRole);
        setLoading(false);
      } else {
        setIsLoggedIn(false);
        setUserName(null);
        setUserRole(null);
        setLoading(false);

        const protectedRoutes = ["/inbox", "/team", "/knowledge", "/analytics", "/settings"];
        if (protectedRoutes.some((route) => pathname === route || pathname.startsWith(route + "/"))) {
          router.push("/login?redirect=" + pathname);
        }
      }
    };
    checkAuth();
    window.addEventListener("storage", checkAuth);
    return () => window.removeEventListener("storage", checkAuth);
  }, [pathname, router]);

  const handleLogout = () => {
    localStorage.clear();
    setIsLoggedIn(false);
    router.push("/login");
  };

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");
  const isDark = theme === "dark";

  if (pathname === "/login" || pathname === "/register") return null;

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
          <div className="w-9 h-9 rounded-lg overflow-hidden flex items-center justify-center transition-transform group-hover:scale-105 shrink-0">
            <img
              src="/images/HaqDesk.png"
              alt="HaqDesk AI"
              className="w-full h-full object-contain"
            />
          </div>
          <div className="flex flex-col leading-none">
            <span className="font-heading font-bold text-[15px] tracking-tight text-foreground">
              HaqDesk<span style={{ color: "var(--accent)" }}> AI</span>
            </span>
            <span className="text-[9.5px] font-medium uppercase tracking-widest text-muted-foreground mt-0.5 hidden sm:block">
              AI-Powered Support
            </span>
          </div>
        </Link>

        {/* Center Nav */}
        <nav className="hidden lg:flex items-center gap-2">
          {navItems
            .filter(item => {
              if (item.name === "Super Admin") {
                return userRole === "super_admin";
              }
              return true;
            })
            .map((item) => {
              const isActive = pathname === item.path;
              const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.path}
                className={`${
                  isActive
                    ? "font-medium text-foreground bg-black/5 dark:bg-white/10"
                    : "text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/5"
                } flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13.5px] transition-colors duration-150`}
              >
                <Icon className="shrink-0" />
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
                <button
                  onClick={toggleTheme}
                  className="rounded-lg p-2 text-gray-400 hover:bg-white/10 hover:text-white transition-all"
                  aria-label="Toggle theme"
                >
                  {isDark ? <Sun size={16} /> : <Moon size={16} />}
                </button>

                {/* Divider */}
                <div className="w-px h-5 bg-white/10 mx-1" />

                {/* Clickable profile */}
                <div className="relative" data-profile-menu>
                  <button
                    onClick={() => setShowProfileMenu(!showProfileMenu)}
                    className="flex items-center gap-2.5 rounded-xl px-2 py-1.5 hover:bg-white/10 transition-all"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#6D4AE2] text-white text-sm font-bold shrink-0 overflow-hidden">
                      {profileImage ? (
                        <img src={profileImage} alt="profile" className="w-full h-full object-cover" />
                      ) : (
                        userName ? userName.charAt(0).toUpperCase() : "N"
                      )}
                    </div>
                    <div className="flex flex-col leading-tight text-left">
                      <span className="text-[13px] font-semibold text-white">
                        {userName || "User"}
                      </span>
                      <span className="text-[10px] font-medium text-purple-400 uppercase tracking-wider">
                        {userRole || "Admin"}
                      </span>
                    </div>
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-gray-400 ml-1">
                      <path d="M2 4l4 4 4-4" />
                    </svg>
                  </button>

                  {/* Dropdown */}
                  {showProfileMenu && (
                    <div className="absolute right-0 top-full mt-2 w-48 rounded-xl border border-white/10 bg-[#1a1a2e] shadow-2xl overflow-hidden z-[100]">
                      <button
                        onClick={() => { setShowProfileModal(true); setShowProfileMenu(false); }}
                        className="w-full flex items-center gap-3 px-4 py-3 text-[13px] text-gray-300 hover:bg-white/10 hover:text-white transition-all text-left"
                      >
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                          <circle cx="8" cy="5" r="3" />
                          <path d="M2 14a6 6 0 0 1 12 0" />
                        </svg>
                        Edit Profile
                      </button>
                      <div className="h-px bg-white/10" />
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-3 text-[13px] text-red-400 hover:bg-red-500/10 transition-all text-left"
                      >
                        <LogOut size={14} />
                        Logout
                      </button>
                    </div>
                  )}
                </div>


              </div>
            ) : (
              <Link
                href="/login"
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-[13.5px] font-medium text-white transition-all duration-150 hover:-translate-y-px active:translate-y-0"
                style={{ background: "var(--accent)" }}
              >
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M10 3h3a1 1 0 011 1v8a1 1 0 01-1 1h-3M7 11l3-3-3-3M10 8H2" />
                </svg>
                Sign in
              </Link>
            )
          )}
        </div>

        {/* Mobile toggle */}
        <div className="flex lg:hidden items-center gap-2">
          <button
            onClick={toggleTheme}
            className="w-[34px] h-[34px] rounded-lg flex items-center justify-center text-muted-foreground border transition-colors duration-200 hover:text-foreground hover:bg-black/5 dark:hover:bg-white/5"
            style={{ borderColor: "var(--nav-border)" }}
            aria-label="Toggle theme"
          >
            {isDark ? <Sun size={15} /> : <Moon size={15} />}
          </button>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            {isMobileMenuOpen ? (
              <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 3l10 10M13 3L3 13" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 4h12M2 8h12M2 12h12" />
              </svg>
            )}
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
            className="lg:hidden overflow-hidden glass border-t border-white/10 px-6 py-4 flex flex-col gap-2"
          >
            {navItems
              .filter(item => {
                if (item.name === "Super Admin") {
                  return userRole === "super_admin";
                }
                return true;
              })
              .map((item) => {
                const isActive = pathname === item.path;
                const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`${
                    isActive
                      ? "font-medium text-foreground bg-black/5 dark:bg-white/10"
                      : "text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/5"
                  } flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13.5px] transition-colors duration-150`}
                >
                  <Icon className="shrink-0" />
                  <span className="font-heading font-medium tracking-tight">{item.name}</span>
                </Link>
              );
            })}

            <div className="h-px bg-white/10 my-2" />

            {!loading && isLoggedIn ? (
              <div className="flex items-center justify-between px-2 py-2">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#6D4AE2] text-white text-sm font-bold shrink-0">
                    {userName ? userName.charAt(0).toUpperCase() : "N"}
                  </div>
                  <div className="flex flex-col leading-tight">
                    <span className="text-[13px] font-semibold text-white">
                      {userName || "User"}
                    </span>
                    <span className="text-[10px] font-medium text-purple-400 uppercase tracking-wider">
                      {userRole || "Admin"}
                    </span>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="rounded-lg p-2 text-gray-400 hover:bg-white/10 hover:text-red-400 transition-all"
                >
                  <LogOut size={16} />
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                onClick={() => setIsMobileMenuOpen(false)}
                className="flex items-center justify-center gap-1.5 px-4 py-2.5 bg-[#6D4AE2] hover:bg-[#5B3BC7] text-white rounded-lg text-xs font-medium transition-all"
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
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#1a1a2e] shadow-2xl p-6">

            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-white">Edit Profile</h2>
              <button
                onClick={() => setShowProfileModal(false)}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-white/10 hover:text-white transition-all"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M3 3l10 10M13 3L3 13" />
                </svg>
              </button>
            </div>

            <div className="flex flex-col items-center mb-6">
              <div className="relative">
                <div className="h-20 w-20 rounded-full bg-[#6D4AE2] flex items-center justify-center text-white text-2xl font-bold overflow-hidden">
                  {profileImage ? (
                    <img src={profileImage} alt="profile" className="w-full h-full object-cover" />
                  ) : (
                    userName ? userName.charAt(0).toUpperCase() : "N"
                  )}
                </div>
                <label className="absolute bottom-0 right-0 flex h-7 w-7 cursor-pointer items-center justify-center rounded-full bg-[#6D4AE2] hover:bg-[#5B3BC7] transition-all">
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="white" strokeWidth="1.5">
                    <path d="M8 3v10M3 8h10" />
                  </svg>
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
                          localStorage.setItem("profileImage", result);
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                  />
                </label>
              </div>
              <p className="text-xs text-gray-400 mt-2">Click + to upload photo</p>
            </div>

            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Full Name</label>
              <input
                type="text"
                defaultValue={userName || ""}
                id="profile-name-input"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-[13px] text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all"
                placeholder="Your name"
              />
            </div>

            <div className="mb-6">
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Role</label>
              <input
                type="text"
                value={userRole || "Admin"}
                readOnly
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-[13px] text-gray-500 cursor-not-allowed"
              />
            </div>

            <button
              onClick={() => {
                const nameInput = document.getElementById("profile-name-input") as HTMLInputElement;
                if (nameInput?.value) {
                  setUserName(nameInput.value);
                  localStorage.setItem("userName", nameInput.value);
                }
                setShowProfileModal(false);
              }}
              className="w-full rounded-xl bg-[#6D4AE2] hover:bg-[#5B3BC7] py-2.5 text-[13px] font-semibold text-white transition-all"
            >
              Save Changes
            </button>

          </div>
        </div>
      )}
    </>
  );
}