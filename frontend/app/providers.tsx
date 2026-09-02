"use client";
import { ThemeProvider } from "next-themes";
import React from "react";
import BackgroundNotificationProvider from "@/components/notifications/BackgroundNotificationProvider";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider 
      attribute="class" 
      defaultTheme="dark" 
      enableSystem={false}
      disableTransitionOnChange={false}
    >
      <BackgroundNotificationProvider>{children}</BackgroundNotificationProvider>
    </ThemeProvider>
  );
}



