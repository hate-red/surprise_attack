import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartСТЕ — интеллектуальный помощник",
  description: "Автоматическое заполнение характеристик и подбор КТРУ",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html className="dark" lang="ru" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
