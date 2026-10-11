"use client";

import React from "react";
import { 
  Home, 
  Wallet, 
  Truck, 
  Calendar, 
  FileText, 
  CheckCircle2, 
  Clock, 
  Sparkles,
  HelpCircle
} from "lucide-react";

interface AgentExplainerProps {
  executionLogs?: any[];
  iterationCount?: number;
}

export default function AgentExplainer({ executionLogs, iterationCount }: AgentExplainerProps) {
  // Map friendly role to execution log status if available
  const getAgentStatus = (agentName: string) => {
    if (!executionLogs || executionLogs.length === 0) return null;
    const latest = [...executionLogs].reverse().find((l) => l.agent_name === agentName);
    if (!latest) return null;
    return latest.status;
  };

  const agents = [
    {
      role: "Home Finder",
      technicalName: "Housing Research Agent",
      icon: Home,
      color: "blue",
      desc: "Helps compare housing options based on your bedrooms, budget, pets, and commute distance.",
    },
    {
      role: "Budget Planner",
      technicalName: "Budget Analyst Agent",
      icon: Wallet,
      color: "emerald",
      desc: "Checks whether the move fits your budget by separating one-time moving costs from monthly rent.",
    },
    {
      role: "Moving Coordinator",
      technicalName: "Logistics Agent",
      icon: Truck,
      color: "amber",
      desc: "Estimates transportation and moving needs, truck sizes, freight costs, and transit times.",
    },
    {
      role: "Timeline Planner",
      technicalName: "Schedule Optimization Agent",
      icon: Calendar,
      color: "purple",
      desc: "Organizes the steps and dates into a clear chronological order so you never miss a moving deadline.",
    },
    {
      role: "Lease Checker",
      technicalName: "Document Intelligence Agent",
      icon: FileText,
      color: "indigo",
      desc: "Highlights clauses that may need attention, like hidden deductions or strict notice periods.",
    },
    {
      role: "Plan Coordinator",
      technicalName: "Decision & Synthesis Agent",
      icon: CheckCircle2,
      color: "teal",
      desc: "Combines the results, identifies any conflicting requirements, and ensures your complete plan works.",
    },
  ];

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
      
      {/* Title & Introduction */}
      <div className="max-w-2xl">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Intelligent Coordination</span>
        </div>
        <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
          How NEXMOVE Helps You Move
        </h3>
        <p className="text-xs sm:text-sm text-slate-500 mt-1 leading-relaxed">
          Instead of you managing six different moving checklists, our specialized AI assistants handle each part of your relocation simultaneously.
        </p>
      </div>

      {/* 6 Friendly Role Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
        {agents.map((agent, idx) => {
          const Icon = agent.icon;
          const status = getAgentStatus(agent.technicalName);

          return (
            <div 
              key={idx} 
              className="p-5 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 transition flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 shadow-2xs flex items-center justify-center text-blue-600">
                    <Icon className="w-5 h-5" />
                  </div>

                  {status && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                      Completed
                    </span>
                  )}
                </div>

                <h4 className="text-sm font-bold text-slate-900">{agent.role}</h4>
                <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                  {agent.desc}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-200/60 text-[11px] text-slate-400">
                Automatic coordination
              </div>
            </div>
          );
        })}
      </div>

      {/* Helpful note at bottom */}
      <div className="pt-2 text-center text-xs text-slate-400">
        All calculations respect real-world constraints such as moving dates, deposit requirements, and commute limits.
      </div>
    </div>
  );
}
