"use client";

import React from "react";
import { usePathname } from "next/navigation";

const PUBLIC_PAGES = ["/login", "/register", "/accept-invite", "/forgot-password", "/reset-password", "/onboarding/business"];

export default function MainWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublic = PUBLIC_PAGES.some((p) => pathname === p || pathname.startsWith(p + "?"));

  return (
    <main
      className="flex-1 flex flex-col overflow-y-auto"
      style={isPublic ? {} : { marginTop: 60, height: "calc(100vh - 60px)" }}
    >
      {children}
    </main>
  );
}
