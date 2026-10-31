import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "OmniContext Cockpit | Enterprise MCP Gateway & Real-Time Evals",
  description: "Enterprise Model Context Protocol gateway with real-time SSE streaming, hybrid RRF retrieval, and continuous evaluations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-[#0B0C10] text-[#F3F4F6] font-sans antialiased selection:bg-[#38BDF8]/20 selection:text-[#38BDF8]">
        {children}
      </body>
    </html>
  );
}
