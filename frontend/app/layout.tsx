import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXMOVE: Autonomous Multi-Agent Relocation Assistant",
  description: "AI-powered relocation platform orchestrated by LangGraph and n8n with three-tier INR financial modeling.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
