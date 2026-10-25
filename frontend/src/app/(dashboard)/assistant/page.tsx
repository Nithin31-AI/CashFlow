"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  MessageSquare,
  Send,
  Sparkles,
  ShieldCheck,
  FileText,
  AlertCircle,
  Database,
  ArrowRight,
  RefreshCw,
  HelpCircle,
  TrendingUp,
  DollarSign,
  AlertTriangle
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, AssistantResponse } from "@/lib/api";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  citations?: string[];
  assumptionsNote?: string;
  timestamp: string;
}

export default function AssistantPage() {
  const { currentBusiness } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    "What is our actual cash balance?",
    "Which invoices are overdue?",
    "What is our 30-day forecast?",
    "What is our monthly expense breakdown?",
    "What recent customer payments were recorded?",
    "What is our reserve breach probability?",
    "What actions are recommended to optimize cash flow?",
  ];

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  // Initial welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: "welcome",
          sender: "assistant",
          text: "Hello! I am your cashFlow AI Financial Intelligence Assistant. I am directly grounded in your verified bank ledger, accounts receivable records, and predictive cash-flow models. I will never fabricate numbers or hallucinate financial balances. How can I assist your business today?",
          citations: ["Grounded Tool Architecture", "cashFlow Financial Engine"],
          assumptionsNote: "All figures cite cleared bank ledger transactions and validated database models.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }
  }, []);

  const handleSend = async (queryToSend?: string) => {
    const q = (queryToSend || inputQuery).trim();
    if (!q || !currentBusiness || isThinking) return;

    setError(null);
    setInputQuery("");

    const userMsg: ChatMessage = {
      id: "u-" + Date.now(),
      sender: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsThinking(true);

    try {
      const res: AssistantResponse = await api.askAssistant(currentBusiness.id, q);

      const assistantMsg: ChatMessage = {
        id: "a-" + Date.now(),
        sender: "assistant",
        text: res.answer,
        citations: res.citations,
        assumptionsNote: res.assumptions_note,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errMsg = err.message || "Failed to retrieve grounded assistant response.";
      setError(errMsg);

      let displayText = `Assistant query encountered an issue: ${errMsg}`;
      if (errMsg.includes("Unable to connect") || errMsg.includes("Failed to fetch")) {
        displayText = "Unable to connect to the cashFlow backend server at http://localhost:8000. Please ensure the backend container or service is running and accessible.";
      } else if (errMsg.includes("401") || errMsg.includes("authenticated")) {
        displayText = "Your session has expired. Please sign in again to access financial intelligence.";
      } else if (errMsg.includes("403") || errMsg.includes("Forbidden") || errMsg.includes("permission")) {
        displayText = "Access denied. You do not have permission to query financial records for this business workspace.";
      }

      const errorMsg: ChatMessage = {
        id: "e-" + Date.now(),
        sender: "assistant",
        text: displayText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="max-w-5xl mx-auto pb-12 flex flex-col h-[calc(100vh-140px)]">
      {/* Header */}
      <div className="flex-shrink-0 mb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-sage)]/10 text-[var(--color-sage)] border border-[var(--color-sage)]/20 flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            Grounded Financial Intelligence
          </span>
          <span className="text-xs text-[var(--foreground)]/50">Tool-Calling & Zero-Hallucination</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight">AI Conversational Assistant</h1>
        <p className="text-sm text-[var(--foreground)]/70 mt-0.5">
          Ask questions about liquidity, overdue invoices, simulations, and financial optimization.
        </p>
      </div>

      {/* Main Chat Box Container */}
      <div className="flex-1 spatial-card rounded-2xl border border-[var(--border)] flex flex-col overflow-hidden bg-[var(--card-bg)] shadow-sm">
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-5">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.sender === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-2xl rounded-2xl p-4 md:p-5 transition shadow-sm ${
                  msg.sender === "user"
                    ? "bg-[var(--color-sage)] text-white rounded-br-none"
                    : "bg-[var(--foreground)]/[0.03] border border-[var(--border)] text-[var(--foreground)] rounded-bl-none"
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-2">
                  <span className="text-[11px] font-semibold opacity-70 flex items-center gap-1">
                    {msg.sender === "user" ? (
                      "You"
                    ) : (
                      <>
                        <ShieldCheck className="w-3.5 h-3.5 text-[var(--color-sage)]" />
                        cashFlow Verified Assistant
                      </>
                    )}
                  </span>
                  <span className="text-[10px] opacity-50">{msg.timestamp}</span>
                </div>

                {/* Message Text with Line Break Formatting */}
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.text}
                </div>

                {/* Citations & Verified Badges */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-[var(--border)]/50 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] font-semibold text-[var(--foreground)]/50 flex items-center gap-1 mr-1">
                      <Database className="w-3 h-3 text-[var(--color-sage)]" />
                      Evidence:
                    </span>
                    {msg.citations.map((cite, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--color-sage)]/10 text-[var(--color-sage)] border border-[var(--color-sage)]/20"
                      >
                        {cite}
                      </span>
                    ))}
                  </div>
                )}

                {/* Assumptions Footnote */}
                {msg.assumptionsNote && (
                  <div className="mt-2 text-[11px] text-[var(--foreground)]/60 italic flex items-center gap-1">
                    <HelpCircle className="w-3 h-3 opacity-60 flex-shrink-0" />
                    <span>{msg.assumptionsNote}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isThinking && (
            <div className="flex items-start">
              <div className="bg-[var(--foreground)]/[0.03] border border-[var(--border)] rounded-2xl p-4 rounded-bl-none flex items-center gap-3">
                <RefreshCw className="w-4 h-4 animate-spin text-[var(--color-sage)]" />
                <span className="text-xs text-[var(--foreground)]/70">
                  Querying verified bank ledger & financial engines...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Pills */}
        <div className="p-3 border-t border-[var(--border)]/40 bg-[var(--foreground)]/[0.01] flex items-center gap-2 overflow-x-auto text-xs no-scrollbar">
          <span className="text-[var(--foreground)]/50 font-medium whitespace-nowrap pl-1">
            Suggested:
          </span>
          {quickPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              disabled={isThinking}
              className="px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--card-bg)] hover:border-[var(--color-sage)] hover:text-[var(--color-sage)] whitespace-nowrap transition text-xs text-[var(--foreground)]/80 disabled:opacity-50"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-[var(--border)] bg-[var(--card-bg)] flex items-center gap-3">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your cash balance, runway, or recommendations..."
            disabled={isThinking}
            className="flex-1 px-4 py-2.5 rounded-xl border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)] disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputQuery.trim() || isThinking}
            className="px-4 py-2.5 rounded-xl bg-[var(--color-sage)] text-white hover:opacity-95 transition flex items-center gap-2 text-sm font-semibold disabled:opacity-40"
          >
            <span>Send</span>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
