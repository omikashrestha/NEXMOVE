"use client";

import React from "react";
import { 
  Home, 
  Wallet, 
  Truck, 
  Calendar, 
  FileText, 
  CheckCircle2, 
  Sparkles
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
      desc: "Compares housing options based on your bedrooms, budget, pets, and commute distance.",
    },
    {
      role: "Budget Planner",
      technicalName: "Budget Analyst Agent",
      icon: Wallet,
      desc: "Checks whether the move fits your budget by separating one-time moving costs from monthly rent.",
    },
    {
      role: "Moving Coordinator",
      technicalName: "Logistics Agent",
      icon: Truck,
      desc: "Estimates transportation and moving needs, truck sizes, freight tariffs, and transit times.",
    },
    {
      role: "Timeline Planner",
      technicalName: "Schedule Optimization Agent",
      icon: Calendar,
      desc: "Organizes the steps and dates into a clear chronological order so you never miss a moving deadline.",
    },
    {
      role: "Lease Checker",
      technicalName: "Document Intelligence Agent",
      icon: FileText,
      desc: "Highlights clauses that may need attention, like hidden deductions or strict notice periods.",
    },
    {
      role: "Plan Coordinator",
      technicalName: "Decision & Synthesis Agent",
      icon: CheckCircle2,
      desc: "Combines the results, identifies any conflicting requirements, and ensures your complete plan works.",
    },
  ];

  return (
    <div className="bg-white dark:bg-[#182321] rounded-3xl p-6 sm:p-8 border border-[#E4E8E3] dark:border-[#354540] shadow-card space-y-6 transition-colors duration-200">
      
      {/* Title & Introduction */}
      <div className="max-w-2xl">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#E8F3F0] dark:bg-[#203D37] text-[#115E59] dark:text-[#5EEAD4] text-xs font-semibold mb-2 border border-[#CCE3D7] dark:border-[#354540]">
          <Sparkles className="w-3.5 h-3.5 text-[#0F766E] dark:text-[#5EEAD4]" aria-hidden="true" />
          <span>Intelligent Multi-Agent Coordination</span>
        </div>
        <h3 className="text-2xl font-bold text-[#18312F] dark:text-[#F3F7F4] tracking-tight">
          How NEXMOVE Helps You Move
        </h3>
        <p className="text-xs sm:text-sm text-[#526461] dark:text-[#B6C6C1] mt-1 leading-relaxed">
          Instead of managing six separate spreadsheets, our specialized AI domain agents coordinate each pillar of your move together.
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
              className="p-5 rounded-2xl border border-[#E4E8E3] dark:border-[#354540] bg-[#FAF8F3] dark:bg-[#202D2A] hover:bg-[#E8F3F0]/40 dark:hover:bg-[#203D37]/40 transition flex flex-col justify-between space-y-3 shadow-2xs"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-white dark:bg-[#182321] border border-[#E4E8E3] dark:border-[#354540] shadow-2xs flex items-center justify-center text-[#0F766E] dark:text-[#5EEAD4]">
                    <Icon className="w-5 h-5" aria-hidden="true" />
                  </div>

                  {status && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#EEF7F2] dark:bg-[#1C3A2B] text-[#237A57] dark:text-[#5EEAD4] border border-[#CCE3D7] dark:border-[#2DD4BF]/30">
                      Completed
                    </span>
                  )}
                </div>

                <h4 className="text-sm font-bold text-[#18312F] dark:text-[#F3F7F4]">{agent.role}</h4>
                <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1.5 leading-relaxed">
                  {agent.desc}
                </p>
              </div>

              <div className="pt-2 border-t border-[#E4E8E3] dark:border-[#354540] text-[11px] text-[#526461] dark:text-[#B6C6C1]/80">
                Autonomous domain agent
              </div>
            </div>
          );
        })}
      </div>

      {/* Helpful note at bottom */}
      <div className="pt-2 text-center text-xs text-[#526461] dark:text-[#B6C6C1]">
        All calculations respect real-world constraints such as moving dates, deposit requirements, and commute limits.
      </div>
    </div>
  );
}
