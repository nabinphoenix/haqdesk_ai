import type { Metadata } from "next";
import { Outfit, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
});

const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "HaqDesk AI | Unified Customer Support",
  description: "Because every customer has a right (हक) to timely, accurate, and respectful support.",
};

import AppSidebar from "@/components/layout/AppSidebar";
import Providers from "@/app/providers";
import { Toaster } from "sonner";
import MainWrapper from "@/components/layout/MainWrapper";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${outfit.variable} ${plusJakarta.variable}`} suppressHydrationWarning>
      <body
        className={`${outfit.variable} ${plusJakarta.variable} font-body antialiased flex flex-col h-screen overflow-hidden bg-background text-body-slate bg-mesh-gradient`}
        suppressHydrationWarning
      >
        <Providers>
          {/* Fixed Top Navbar */}
          <AppSidebar />

          {/* Centered Floating Content Wrapper */}
          <MainWrapper>{children}</MainWrapper>
          <Toaster theme="system" position="bottom-right" richColors toastOptions={{
            style: {
              background: 'var(--surface-wash)',
              border: '1px solid var(--surface-border)',
              color: 'var(--text-primary)',
            }
          }} />
        </Providers>
      </body>
    </html>
  );
}
