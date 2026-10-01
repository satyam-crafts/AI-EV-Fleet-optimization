import React, { useState } from 'react';
import {
  X,
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import { AgentQueryResponse, OptimizationResult } from '../types';

interface AIAssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  latestOptimization: OptimizationResult | null;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  provider?: string;
  timestamp: Date;
}

export const AIAssistantDrawer: React.FC<AIAssistantDrawerProps> = ({
  isOpen,
  onClose,
  latestOptimization,
}) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "👋 Hello! I am your AI Fleet Energy Optimization Copilot. I analyze fleet telemetry, explain deterministic optimization decisions, and evaluate TOU tariffs without inventing unverified numbers. How can I help you optimize your fleet today?",
      provider: 'deterministic_template',
      timestamp: new Date(),
    },
  ]);

  if (!isOpen) return null;

  const quickPrompts = [
    'How much did we save by load shifting?',
    'Which vehicles need battery attention?',
    'Why is EV-102 charging scheduled at night?',
    'Can EV-105 handle Route R-AIRPORT-02?',
  ];

  const handleSend = async (userPrompt?: string) => {
    const textToSend = userPrompt || query;
    if (!textToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res: AgentQueryResponse = await api.queryAgent(textToSend);
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: res.response_text,
        provider: res.provider_used,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `⚠️ Error contacting agent service: ${err.message}. The system continues to run using local deterministic rules.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col justify-between animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-white shadow-md shadow-emerald-950/30">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              AI Fleet Copilot
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Ground Truth
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">Deterministic Mathematical Reasoning</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Latest Optimization Summary Badge if exists */}
        {latestOptimization && (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-3 text-xs space-y-1">
            <div className="flex items-center justify-between font-semibold text-emerald-400">
              <span className="flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" />
                Latest Optimization ({latestOptimization.status})
              </span>
              <span>${latestOptimization.baseline_comparison.cost_savings.toFixed(2)} saved</span>
            </div>
            <p className="text-slate-300 text-[11px]">
              {latestOptimization.assignments.length} assigned · {latestOptimization.charging_plans.length} charging sessions · {latestOptimization.baseline_comparison.savings_percentage}% cost reduction
            </p>
          </div>
        )}

        {/* Message bubbles */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start space-x-2.5 ${
              msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
            }`}
          >
            <div
              className={`w-7 h-7 rounded-lg shrink-0 flex items-center justify-center text-xs ${
                msg.sender === 'user'
                  ? 'bg-slate-700 text-white'
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
            </div>
            <div
              className={`rounded-2xl p-3.5 max-w-[85%] text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-emerald-600 text-white font-medium'
                  : 'bg-slate-950/80 border border-slate-800 text-slate-200'
              }`}
            >
              <div className="whitespace-pre-line">{msg.text}</div>
              {msg.provider && (
                <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                  <span className="flex items-center gap-1 text-emerald-400/80">
                    <ShieldCheck className="w-3 h-3" />
                    Verified Facts
                  </span>
                  <span>{msg.provider}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-xs text-slate-400 p-2">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
            <span>Consulting deterministic optimization engine...</span>
          </div>
        )}
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-4 py-2 bg-slate-950/40 border-t border-slate-800/60 overflow-x-auto flex gap-1.5 no-scrollbar">
        {quickPrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => handleSend(p)}
            className="shrink-0 text-[11px] rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 px-2.5 py-1 border border-slate-700/60 transition-colors"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/60">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about SOC, charging, routes, costs..."
            className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="p-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40 transition-colors shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="mt-2 text-[10px] text-center text-slate-400">
          AI Copilot synthesizes data without fabricating mathematical values.
        </p>
      </div>
    </div>
  );
};
