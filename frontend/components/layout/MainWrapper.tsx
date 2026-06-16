import React from "react";

export default function MainWrapper({ children }: { children: React.ReactNode }) {
  return (
    <main
      className="flex-1 flex flex-col overflow-y-auto"
      style={{ marginTop: 60, height: "calc(100vh - 60px)" }}
    >
      {children}
    </main>
  );
}
