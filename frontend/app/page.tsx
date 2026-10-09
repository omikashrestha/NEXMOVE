"use client";

import React, { useState } from "react";
import { 
  Building2, 
  Truck, 
  Wallet, 
  Calendar, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight, 
  RefreshCw, 
  Bot, 
  Info,
  ShieldCheck,
  Clock,
  Sparkles
} from "lucide-react";

const API_BASE = "http://localhost:8000";

interface ProjectDetail {
  project_id: string;
  user_email: string;
  user_name: string;
  origin_city: string;
  destination_city: string;
  target_move_date: string;
  upfront_budget_limit_inr: number;
  monthly_budget_limit_inr: number;
  home_bhk: number;
  has_pets: boolean;
  status: string;
  housing_proposal?: any;
  logistics_estimate?: any;
  budget_audit?: any;
  document_audit?: any;
  schedule_plan?: any;
  synthesized_plan?: any;
  active_conflicts?: any[];
  iteration_count?: number;
  execution_logs?: any[];
}

export default function NexMoveDashboard() {
  // Form State
  const [origin, setOrigin] = useState("Pune");
  const [destination, setDestination] = useState("Bengaluru");
  const [moveDate, setMoveDate] = useState("2026-11-05");
  const [upfrontBudget, setUpfrontBudget] = useState(150000);
  const [monthlyBudget, setMonthlyBudget] = useState(45000);
  const [bhk, setBhk] = useState(2);
  const [hasPets, setHasPets] = useState(true);

  // App Execution State
  const [activeTab, setActiveTab] = useState<"overview" | "budget" | "timeline" | "agents" | "document">("overview");
  const [loading, setLoading] = useState(false);
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [replanBudget, setReplanBudget] = useState<number>(130000);
  const [selectedDocSample, setSelectedDocSample] = useState<string>("lease_redflag_inr.txt");
  const [docAuditResult, setDocAuditResult] = useState<any>(null);
  const [docLoading, setDocLoading] = useState(false);

  // Document Sample Audit Handler
  const handleAnalyzeSampleDoc = async (sampleName?: string) => {
    const filename = sampleName || selectedDocSample;
    setDocLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/documents/analyze-sample?sample_filename=${filename}`, {
        method: "POST"
      });
      if (!res.ok) throw new Error("Document analysis failed");
      const data = await res.json();
      setDocAuditResult(data.audit);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to analyze document");
    } finally {
      setDocLoading(false);
    }
  };

  // 1. Start Relocation Planning
  const handleStartPlanning = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // Step A: Create project
      const createRes = await fetch(`${API_BASE}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_email: "omika@example.com",
          user_name: "Omika Shrestha",
          origin_city: origin,
          destination_city: destination,
          target_move_date: moveDate,
          upfront_budget_limit_inr: upfrontBudget,
          monthly_budget_limit_inr: monthlyBudget,
          home_bhk: bhk,
          has_pets: hasPets,
          target_workplace: "Manyata Tech Park",
          max_commute_mins: 40,
        }),
      });

      if (!createRes.ok) throw new Error("Failed to initialize project");
      const projectSummary = await createRes.json();

      // Step B: Run planning agents
      const runRes = await fetch(`${API_BASE}/api/projects/${projectSummary.project_id}/run`, {
        method: "POST",
      });

      if (!runRes.ok) throw new Error("Failed to execute multi-agent planning");
      const fullProject = await runRes.json();
      setProject(fullProject);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to reach backend API at " + API_BASE);
    } finally {
      setLoading(false);
    }
  };

  // 2. Dynamic Replanning on Budget Change
  const handleReplan = async () => {
    if (!project) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${project.project_id}/replan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          upfront_budget_limit_inr: replanBudget,
        }),
      });
      if (!res.ok) throw new Error("Replanning execution failed");
      const updated = await res.json();
      setProject(updated);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. User Decision Action (Approve / Reject / Escalation Option)
  const handleDecision = async (action: string) => {
    if (!project) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${project.project_id}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision_action: action }),
      });
      if (!res.ok) throw new Error("Failed to record decision");
      const updated = await res.json();
      setProject(updated);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20">
      {/* Top Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              NM
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900">NEXMOVE</h1>
              <p className="text-xs text-slate-500 font-medium">Autonomous Multi-Agent Relocation Assistant</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
              FastAPI Engine Online
            </span>
            <span className="text-xs text-slate-400 border-l border-slate-200 pl-3">
              Currency: <strong>INR (₹)</strong>
            </span>
          </div>
        </div>
      </header>

      {/* Main Layout Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Banner Alert if error */}
        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">Execution Notice</p>
              <p className="text-xs mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Requirements & Input Controls (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <h2 className="text-base font-semibold text-slate-900 flex items-center mb-4">
                <Sparkles className="w-4 h-4 text-blue-600 mr-2" />
                Relocation Parameters
              </h2>

              <div className="space-y-4 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Origin City</label>
                    <input 
                      type="text" 
                      value={origin} 
                      onChange={(e) => setOrigin(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Destination</label>
                    <input 
                      type="text" 
                      value={destination} 
                      onChange={(e) => setDestination(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Target Move Date</label>
                  <input 
                    type="date" 
                    value={moveDate} 
                    onChange={(e) => setMoveDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="border-t border-slate-100 pt-3">
                  <label className="block text-xs font-semibold text-slate-700 mb-1 flex justify-between">
                    <span>Upfront Capital Limit</span>
                    <span className="text-blue-600 font-bold">₹{upfrontBudget.toLocaleString("en-IN")}</span>
                  </label>
                  <p className="text-[11px] text-slate-400 mb-2">Movers freight + deposits + travel</p>
                  <input 
                    type="range" 
                    min={40000} 
                    max={250000} 
                    step={5000}
                    value={upfrontBudget}
                    onChange={(e) => setUpfrontBudget(Number(e.target.value))}
                    className="w-full accent-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1 flex justify-between">
                    <span>Monthly Living Cap</span>
                    <span className="text-blue-600 font-bold">₹{monthlyBudget.toLocaleString("en-IN")}/mo</span>
                  </label>
                  <p className="text-[11px] text-slate-400 mb-2">Rent + maintenance + utilities + commute</p>
                  <input 
                    type="range" 
                    min={20000} 
                    max={75000} 
                    step={2500}
                    value={monthlyBudget}
                    onChange={(e) => setMonthlyBudget(Number(e.target.value))}
                    className="w-full accent-blue-600"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Home Size</label>
                    <select 
                      value={bhk} 
                      onChange={(e) => setBhk(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
                    >
                      <option value={1}>1 BHK</option>
                      <option value={2}>2 BHK</option>
                      <option value={3}>3 BHK</option>
                    </select>
                  </div>
                  <div className="flex items-center pt-5">
                    <label className="flex items-center space-x-2 text-xs font-medium text-slate-700 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={hasPets} 
                        onChange={(e) => setHasPets(e.target.checked)}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                      />
                      <span>Family Pet</span>
                    </label>
                  </div>
                </div>

                <button 
                  onClick={handleStartPlanning}
                  disabled={loading}
                  className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-xl flex items-center justify-center space-x-2 transition shadow-md shadow-blue-500/20 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Coordinating Agents...</span>
                    </>
                  ) : (
                    <>
                      <span>Launch Multi-Agent Planning</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Dynamic Replanning Widget */}
            {project && (
              <div className="bg-amber-50/70 border border-amber-200 rounded-2xl p-5 text-sm space-y-3">
                <div className="flex items-center space-x-2 text-amber-800 font-semibold text-xs uppercase tracking-wider">
                  <RefreshCw className="w-4 h-4 text-amber-600" />
                  <span>Dynamic Replanning Sandbox</span>
                </div>
                <p className="text-xs text-amber-900 leading-relaxed">
                  Simulate user requirement changes (e.g. reduced moving budget) to test how agents re-negotiate constraints.
                </p>

                <div>
                  <label className="block text-xs font-medium text-amber-950 mb-1 flex justify-between">
                    <span>Adjust Upfront Budget</span>
                    <span className="font-bold text-amber-900">₹{replanBudget.toLocaleString("en-IN")}</span>
                  </label>
                  <input 
                    type="range"
                    min={45000}
                    max={220000}
                    step={5000}
                    value={replanBudget}
                    onChange={(e) => setReplanBudget(Number(e.target.value))}
                    className="w-full accent-amber-600"
                  />
                </div>

                <button
                  onClick={handleReplan}
                  disabled={loading}
                  className="w-full bg-amber-600 hover:bg-amber-700 text-white font-medium py-2 px-3 rounded-lg text-xs flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Execute Dynamic Re-Audit</span>
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Execution Dashboard & Tabs (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {!project ? (
              /* Empty State */
              <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[480px]">
                <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4">
                  <Bot className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-bold text-slate-800">Agent Command Center Idle</h3>
                <p className="text-slate-500 text-xs max-w-md mt-1 mb-6 leading-relaxed">
                  Configure your parameters on the left and trigger the LangGraph orchestration engine to observe Housing, Budget, Logistics, and Document agents reason and resolve conflicts.
                </p>
                <button
                  onClick={handleStartPlanning}
                  disabled={loading}
                  className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition"
                >
                  Run Sample Relocation (Pune → BLR)
                </button>
              </div>
            ) : (
              /* Active Dashboard View */
              <div className="space-y-6">
                {/* Plan Header & Status Banner */}
                <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-slate-500 font-mono bg-slate-100 px-2 py-0.5 rounded">
                        ID: {project.project_id}
                      </span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        project.status === "CONSENSUS_REACHED" 
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : project.status === "AWAITING_USER_DECISION"
                          ? "bg-amber-50 text-amber-700 border border-amber-200"
                          : project.status === "APPROVED"
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : "bg-slate-100 text-slate-700"
                      }`}>
                        {project.status.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-mono">
                        Round {project.iteration_count || 1} / 2
                      </span>
                    </div>

                    <h2 className="text-xl font-bold text-slate-900 mt-1">
                      {project.synthesized_plan?.recommended_housing_title || `${project.origin_city} to ${project.destination_city} Plan`}
                    </h2>
                  </div>

                  <div className="flex items-center space-x-2">
                    {project.status === "CONSENSUS_REACHED" && (
                      <button
                        onClick={() => handleDecision("APPROVE")}
                        disabled={loading}
                        className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs flex items-center space-x-1.5 shadow-sm transition"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Confirm & Approve Plan</span>
                      </button>
                    )}
                    {project.status === "APPROVED" && (
                      <span className="px-4 py-2 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 font-semibold text-xs flex items-center space-x-1.5">
                        <ShieldCheck className="w-4 h-4 text-blue-600" />
                        <span>Plan Locked & Ready</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* HITL Escalation Modal / Box if AWAITING_USER_DECISION */}
                {project.status === "AWAITING_USER_DECISION" && project.synthesized_plan?.escalation_options && (
                  <div className="bg-amber-50 border-2 border-amber-300 rounded-2xl p-6 shadow-md space-y-4">
                    <div className="flex items-start space-x-3">
                      <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0" />
                      <div>
                        <h4 className="text-base font-bold text-amber-950">Human Decision Required (Revisions Capped)</h4>
                        <p className="text-xs text-amber-900 mt-1">
                          Automated conflict arbitration completed 2 rounds without reaching a plan that satisfies all hard constraints. Please select your preferred compromise:
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      {project.synthesized_plan.escalation_options.map((opt: any) => (
                        <div key={opt.option_id} className="bg-white rounded-xl p-4 border border-amber-200 shadow-sm flex flex-col justify-between">
                          <div>
                            <span className="inline-block px-2 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-bold rounded">
                              OPTION {opt.option_id}
                            </span>
                            <h5 className="font-bold text-sm text-slate-900 mt-1.5">{opt.title}</h5>
                            <p className="text-xs text-slate-600 mt-1 leading-relaxed">{opt.trade_off_summary}</p>
                            <div className="mt-3 text-xs space-y-1 text-slate-500 font-mono">
                              <div>Upfront Cost: ₹{opt.upfront_cost_inr.toLocaleString("en-IN")}</div>
                              <div>Commute: ~{opt.commute_mins} mins</div>
                            </div>
                          </div>

                          <button
                            onClick={() => handleDecision(`SELECT_OPTION_${opt.option_id}`)}
                            disabled={loading}
                            className="mt-4 w-full py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg transition"
                          >
                            Accept Option {opt.option_id}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Navigation Tabs */}
                <div className="flex border-b border-slate-200 space-x-6 text-sm font-medium">
                  <button
                    onClick={() => setActiveTab("overview")}
                    className={`pb-3 relative ${activeTab === "overview" ? "text-blue-600 border-b-2 border-blue-600 font-semibold" : "text-slate-500 hover:text-slate-800"}`}
                  >
                    Executive Summary
                  </button>
                  <button
                    onClick={() => setActiveTab("budget")}
                    className={`pb-3 relative ${activeTab === "budget" ? "text-blue-600 border-b-2 border-blue-600 font-semibold" : "text-slate-500 hover:text-slate-800"}`}
                  >
                    Three-Tier Budget
                  </button>
                  <button
                    onClick={() => setActiveTab("timeline")}
                    className={`pb-3 relative ${activeTab === "timeline" ? "text-blue-600 border-b-2 border-blue-600 font-semibold" : "text-slate-500 hover:text-slate-800"}`}
                  >
                    Schedule & Milestones
                  </button>
                  <button
                    onClick={() => setActiveTab("agents")}
                    className={`pb-3 relative ${activeTab === "agents" ? "text-blue-600 border-b-2 border-blue-600 font-semibold" : "text-slate-500 hover:text-slate-800"}`}
                  >
                    Agent Trace Feed
                  </button>
                  <button
                    onClick={() => {
                      setActiveTab("document");
                      if (!docAuditResult) handleAnalyzeSampleDoc();
                    }}
                    className={`pb-3 relative ${activeTab === "document" ? "text-blue-600 border-b-2 border-blue-600 font-semibold" : "text-slate-500 hover:text-slate-800"}`}
                  >
                    Document Intelligence
                  </button>
                </div>

                {/* TAB 1: EXECUTIVE SUMMARY */}
                {activeTab === "overview" && (
                  <div className="space-y-6">
                    {/* Key Cards Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Housing Card */}
                      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
                            <Building2 className="w-3.5 h-3.5 mr-1 text-blue-500" />
                            Recommended Property
                          </span>
                          <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded font-mono">
                            SYNTHETIC BENCHMARK
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-slate-900">{project.housing_proposal?.title}</h4>
                        <p className="text-xs text-slate-500 mt-0.5">{project.housing_proposal?.neighborhood}, {project.housing_proposal?.city}</p>

                        <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-100 text-xs">
                          <div>
                            <span className="text-slate-400 block text-[11px]">Monthly Base Rent</span>
                            <span className="font-bold text-slate-900">₹{project.housing_proposal?.monthly_rent_inr.toLocaleString("en-IN")}</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Security Deposit</span>
                            <span className="font-bold text-slate-900">₹{project.housing_proposal?.security_deposit_inr.toLocaleString("en-IN")}</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Workplace Commute</span>
                            <span className="font-bold text-emerald-600">{project.housing_proposal?.commute_to_workplace_mins} mins</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Pet Friendly</span>
                            <span className="font-bold text-slate-800">{project.housing_proposal?.pet_friendly ? "Yes (Permitted)" : "No"}</span>
                          </div>
                        </div>
                      </div>

                      {/* Logistics Card */}
                      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
                            <Truck className="w-3.5 h-3.5 mr-1 text-amber-500" />
                            Logistics & Transport
                          </span>
                          <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded font-mono">
                            SYNTHETIC TARIFF
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-slate-900">{project.logistics_estimate?.vehicle_type}</h4>
                        <p className="text-xs text-slate-500 mt-0.5">{project.logistics_estimate?.route} ({project.logistics_estimate?.distance_km} km)</p>

                        <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-100 text-xs">
                          <div>
                            <span className="text-slate-400 block text-[11px]">Total Freight Quote</span>
                            <span className="font-bold text-slate-900">₹{project.logistics_estimate?.total_logistics_inr.toLocaleString("en-IN")}</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Transit Duration</span>
                            <span className="font-bold text-slate-900">{project.logistics_estimate?.estimated_transit_days} Days</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Loading Date</span>
                            <span className="font-mono text-slate-700">{project.logistics_estimate?.recommended_pickup_date}</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Arrival & Delivery</span>
                            <span className="font-mono text-slate-700">{project.logistics_estimate?.estimated_delivery_date}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Trade-offs & Advisories */}
                    <div className="bg-slate-100/70 rounded-2xl p-5 border border-slate-200 text-xs space-y-3">
                      <h4 className="font-semibold text-slate-800 flex items-center text-xs uppercase tracking-wider">
                        <Info className="w-4 h-4 text-blue-600 mr-1.5" />
                        Decision Agent Rationale & Trade-offs
                      </h4>
                      {project.synthesized_plan?.trade_offs_resolved?.map((trade: string, i: number) => (
                        <p key={i} className="text-slate-700 leading-relaxed bg-white p-3 rounded-xl border border-slate-200/80">
                          {trade}
                        </p>
                      ))}

                      {project.synthesized_plan?.user_advisories?.length > 0 && (
                        <div className="pt-2">
                          <span className="font-semibold text-slate-700 block mb-1">Contractual Advisories for Human Review:</span>
                          <ul className="list-disc list-inside space-y-1 text-slate-600">
                            {project.synthesized_plan.user_advisories.map((adv: string, idx: number) => (
                              <li key={idx}>{adv}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* TAB 2: THREE-TIER BUDGET */}
                {activeTab === "budget" && project.budget_audit && (
                  <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">Three-Tier Financial Separation (INR)</h3>
                      <p className="text-xs text-slate-500 mt-0.5">Strict mathematical segregation of upfront capital vs. recurring monthly costs.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Upfront Budget Summary */}
                      <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-bold text-xs uppercase text-slate-600">Upfront Capital Outlay</span>
                          <span className={`text-xs font-bold px-2 py-0.5 rounded ${project.budget_audit.upfront_violation ? "bg-rose-100 text-rose-800" : "bg-emerald-100 text-emerald-800"}`}>
                            {project.budget_audit.upfront_violation ? "CAP OVERRUN" : "PASSED"}
                          </span>
                        </div>
                        <div className="text-2xl font-extrabold text-slate-900">
                          ₹{project.budget_audit.total_upfront_outlay_inr.toLocaleString("en-IN")}
                        </div>
                        <p className="text-xs text-slate-500 mt-1">Budget Cap: ₹{project.budget_audit.upfront_budget_limit_inr.toLocaleString("en-IN")}</p>

                        <div className="mt-4 pt-3 border-t border-slate-200 space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-600">1. One-Time Physical Move:</span>
                            <span className="font-mono font-medium">₹{project.budget_audit.one_time_costs.total_one_time_inr.toLocaleString("en-IN")}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">2. Initial Housing Outlay:</span>
                            <span className="font-mono font-medium">₹{project.budget_audit.housing_outlay.total_housing_outlay_inr.toLocaleString("en-IN")}</span>
                          </div>
                          <div className="flex justify-between font-bold pt-1 border-t border-dashed border-slate-200">
                            <span className="text-slate-800">Remaining Contingency Buffer:</span>
                            <span className={project.budget_audit.upfront_variance_inr >= 0 ? "text-emerald-600" : "text-rose-600"}>
                              ₹{project.budget_audit.upfront_variance_inr.toLocaleString("en-IN")}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Recurring Monthly Spend */}
                      <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-bold text-xs uppercase text-slate-600">Recurring Monthly Living</span>
                          <span className={`text-xs font-bold px-2 py-0.5 rounded ${project.budget_audit.monthly_violation ? "bg-rose-100 text-rose-800" : "bg-emerald-100 text-emerald-800"}`}>
                            {project.budget_audit.monthly_violation ? "CAP OVERRUN" : "PASSED"}
                          </span>
                        </div>
                        <div className="text-2xl font-extrabold text-slate-900">
                          ₹{project.budget_audit.recurring_monthly_costs.total_recurring_monthly_inr.toLocaleString("en-IN")}/mo
                        </div>
                        <p className="text-xs text-slate-500 mt-1">Monthly Ceiling: ₹{project.budget_audit.monthly_budget_limit_inr.toLocaleString("en-IN")}</p>

                        <div className="mt-4 pt-3 border-t border-slate-200 space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-slate-600">Base House Rent:</span>
                            <span className="font-mono">₹{project.budget_audit.recurring_monthly_costs.monthly_base_rent_inr.toLocaleString("en-IN")}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Society Maintenance:</span>
                            <span className="font-mono">₹{project.budget_audit.recurring_monthly_costs.society_maintenance_inr.toLocaleString("en-IN")}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Utilities (Power, Gas, WiFi):</span>
                            <span className="font-mono">₹{project.budget_audit.recurring_monthly_costs.estimated_utilities_inr.toLocaleString("en-IN")}</span>
                          </div>
                          <div className="flex justify-between font-bold pt-1 border-t border-dashed border-slate-200">
                            <span className="text-slate-800">Monthly Surplus Headroom:</span>
                            <span className="text-emerald-600">
                              ₹{project.budget_audit.monthly_variance_inr.toLocaleString("en-IN")}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 3: TIMELINE & MILESTONES */}
                {activeTab === "timeline" && project.schedule_plan && (
                  <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="text-base font-bold text-slate-900">Relocation Topological Schedule</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Critical-path sequence eliminating overlapping dates.</p>
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
                        Chronology Validated
                      </span>
                    </div>

                    <div className="space-y-3 pt-2">
                      {project.schedule_plan.critical_path_milestones.map((m: any, idx: number) => (
                        <div key={idx} className="flex items-center space-x-4 p-3.5 rounded-xl border border-slate-100 hover:border-slate-200 bg-slate-50/50 transition">
                          <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                            {m.step_id}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h5 className="font-semibold text-xs text-slate-900 truncate">{m.task_name}</h5>
                            <p className="text-[11px] text-slate-400 mt-0.5">Owner: {m.owner_party}</p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <span className="text-xs font-mono font-semibold text-slate-700 block">{m.target_date}</span>
                            {m.is_critical_path && (
                              <span className="text-[10px] text-amber-600 font-semibold uppercase tracking-wider">Critical Path</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* TAB 4: AGENT REASONING TRACE FEED */}
                {activeTab === "agents" && project.execution_logs && (
                  <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">Agent War Room: Inter-Agent Negotiation</h3>
                      <p className="text-xs text-slate-500 mt-0.5">Auditable message trace between Housing, Budget, Logistics, and Decision agents.</p>
                    </div>

                    <div className="space-y-3 pt-2">
                      {project.execution_logs.map((log: any, idx: number) => (
                        <div key={idx} className="p-3.5 rounded-xl border border-slate-100 bg-slate-50 text-xs space-y-1">
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-blue-700">{log.agent_name}</span>
                            <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-mono">
                              {log.status} (Round {log.iteration})
                            </span>
                          </div>
                          <p className="text-slate-600 mt-1">{log.notes}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* TAB 5: DOCUMENT INTELLIGENCE */}
                {activeTab === "document" && (
                  <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
                    {/* Legal Disclaimer Box */}
                    <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start space-x-3">
                      <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                      <div className="text-xs">
                        <p className="font-bold text-amber-950 uppercase tracking-wide">Legal Advisory & Educational Disclaimer</p>
                        <p className="mt-1 leading-relaxed text-amber-900">
                          This automated lease clause audit is provided strictly for educational and informational review. It does NOT constitute legal advice or formal representation. Consult a qualified advocate before signing legal agreements.
                        </p>
                      </div>
                    </div>

                    {/* Interactive Sample Selector */}
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                      <div className="w-full sm:w-auto">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Select Benchmark Lease Agreement</label>
                        <select
                          value={selectedDocSample}
                          onChange={(e) => setSelectedDocSample(e.target.value)}
                          className="w-full sm:w-80 px-3 py-2 rounded-lg border border-slate-200 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="lease_standard_inr.txt">Standard 2BHK Lease (HSR Layout, ₹30k/mo)</option>
                          <option value="lease_redflag_inr.txt">Strict Non-Standard Lease (Indiranagar, Red Flags)</option>
                        </select>
                      </div>
                      <button
                        onClick={() => handleAnalyzeSampleDoc()}
                        disabled={docLoading}
                        className="w-full sm:w-auto px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
                      >
                        {docLoading ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span>Analyzing Clauses...</span>
                          </>
                        ) : (
                          <>
                            <FileText className="w-3.5 h-3.5" />
                            <span>Run Clause Audit</span>
                          </>
                        )}
                      </button>
                    </div>

                    {/* Audit Results */}
                    {docAuditResult && (
                      <div className="space-y-5 pt-2">
                        {/* Extracted Key Terms */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                          <div className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs">
                            <span className="text-slate-400 block text-[11px]">Monthly Rent</span>
                            <span className="font-bold text-slate-900">₹{docAuditResult.extracted_monthly_rent_inr?.toLocaleString("en-IN") || "N/A"}</span>
                          </div>
                          <div className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs">
                            <span className="text-slate-400 block text-[11px]">Security Deposit</span>
                            <span className="font-bold text-slate-900">₹{docAuditResult.extracted_security_deposit_inr?.toLocaleString("en-IN") || "N/A"}</span>
                          </div>
                          <div className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs">
                            <span className="text-slate-400 block text-[11px]">Notice Period</span>
                            <span className="font-bold text-slate-900">{docAuditResult.extracted_notice_period_days} Days</span>
                          </div>
                          <div className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs">
                            <span className="text-slate-400 block text-[11px]">Lock-In Period</span>
                            <span className="font-bold text-slate-900">{docAuditResult.extracted_lock_in_months} Months</span>
                          </div>
                        </div>

                        {/* Flagged Clauses Section */}
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="text-sm font-bold text-slate-900 flex items-center">
                              <FileText className="w-4 h-4 text-blue-600 mr-1.5" />
                              <span>Flagged Risk Clauses ({docAuditResult.flagged_clauses_for_review?.length || 0})</span>
                            </h4>
                            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                              docAuditResult.flagged_clauses_for_review?.length > 0 
                                ? "bg-rose-50 text-rose-700 border border-rose-200" 
                                : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            }`}>
                              {docAuditResult.flagged_clauses_for_review?.length > 0 ? "ACTION REQUIRED" : "STANDARD LEASE"}
                            </span>
                          </div>

                          {docAuditResult.flagged_clauses_for_review?.length === 0 ? (
                            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 text-emerald-800 text-xs flex items-center space-x-2">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              <span>No high-risk penalty clauses or hidden covenants detected in this agreement.</span>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              {docAuditResult.flagged_clauses_for_review.map((clause: any, idx: number) => (
                                <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50 text-xs space-y-2">
                                  <div className="flex items-center justify-between">
                                    <span className="font-bold text-slate-900">{clause.clause_title}</span>
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                      clause.severity === "HIGH" 
                                        ? "bg-rose-100 text-rose-800"
                                        : clause.severity === "MEDIUM"
                                        ? "bg-amber-100 text-amber-800"
                                        : "bg-slate-200 text-slate-700"
                                    }`}>
                                      {clause.severity} RISK
                                    </span>
                                  </div>
                                  <p className="text-slate-600 italic bg-white p-2.5 rounded border border-slate-200/80 font-mono text-[11px]">
                                    "{clause.clause_text}"
                                  </p>
                                  <div className="text-slate-700 space-y-1 pt-1">
                                    <div><strong>Risk Rationale:</strong> {clause.issue_rationale}</div>
                                    <div><strong>Recommended Action:</strong> <span className="text-blue-700">{clause.suggested_action}</span></div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
