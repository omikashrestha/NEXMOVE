import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/lib/theme";

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
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const storedTheme = localStorage.getItem('nexmove-theme');
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (storedTheme === 'dark' || (!storedTheme && prefersDark)) {
                  document.documentElement.classList.add('dark');
                } else {
                  document.documentElement.classList.remove('dark');
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className="min-h-screen bg-[#FAF8F3] dark:bg-[#101918] text-[#18312F] dark:text-[#F3F7F4] antialiased selection:bg-[#E8F3F0] dark:selection:bg-[#203D37] selection:text-[#115E59] dark:selection:text-[#5EEAD4] transition-colors duration-200">
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
