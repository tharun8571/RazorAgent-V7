import "./globals.css";
import React from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";

export const metadata = {
  title: "RazorAgent V7 — Autonomous Payment Operations Platform",
  description: "Autonomous LLM-driven multi-agent payment operations and self-healing platform with LangGraph, Groq (qwen3.8-27b), LangSmith, and Razorpay.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background min-h-screen text-slate-100 flex flex-col">
        <Header />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
