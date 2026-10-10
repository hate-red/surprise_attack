"use client";

import { useState, type ReactNode } from "react";
import { Header } from "@/widgets/header/ui/header";
import { defaultNavigationId } from "@/widgets/navigation/model/navigation-items";
import { MobileNav } from "@/widgets/navigation/ui/mobile-nav";
import { Sidebar } from "@/widgets/navigation/ui/sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  const [activeNavigationId, setActiveNavigationId] = useState(defaultNavigationId);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <Sidebar activeId={activeNavigationId} onSelect={setActiveNavigationId} />
      <main className="ml-[256px] pt-16 max-md:ml-0 max-md:pb-[78px] max-md:pt-[60px]">
        <div className="mx-auto max-w-[1460px] px-7 py-7 max-lg:px-5 max-md:px-3.5 max-md:py-5">
          {children}
        </div>
      </main>
      <MobileNav activeId={activeNavigationId} onSelect={setActiveNavigationId} />
    </div>
  );
}
