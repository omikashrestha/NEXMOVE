"use client";

import React, { useState, useRef, useEffect } from "react";
import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import DashboardSummary from "@/components/DashboardSummary";
import WizardForm from "@/components/WizardForm";
import ResultsView from "@/components/ResultsView";
import AgentExplainer from "@/components/AgentExplainer";
import { 
  AlertTriangle, 
  Sparkles, 
  PlusCircle, 
  CheckCircle2, 
  Home, 
  HelpCircle, 
  ExternalLink, 
  ChevronDown 
} from "lucide-react";
import { getCurrencyFootnote } from "@/lib/currency";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function HomeDashboard() {
  // Global Project & App State
  const [project, setProject] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [currency, setCurrency] = useState("INR");
  
  // Tab state inside ResultsView controlled by Navbar and tab buttons
  const [resultsTab, setResultsTab] = useState<"overview" | "budget" | "timeline" | "lease" | "replan">("overview");

  // Toggle wizard modal when a plan is already active
  const [showWizardModal, setShowWizardModal] = useState(false);

  // Document Intelligence / Lease review state
  const [docAuditResult, setDocAuditResult] = useState<any | null>(null);
  const [docLoading, setDocLoading] = useState(false);

  // Section references for smooth navigation
  const topRef = useRef<HTMLDivElement>(null);
  const wizardRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const explainerRef = useRef<HTMLDivElement>(null);

  const scrollToWizard = () => {
    if (project) {
      setShowWizardModal(true);
    } else {
      wizardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const scrollToExplainer = () => {
    explainerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleNavigateSection = (sectionId: string) => {
    if (sectionId === "top") {
      topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (sectionId === "overview") {
      if (project) {
        setResultsTab("overview");
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      } else {
        topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } else if (sectionId === "how-it-works") {
      explainerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (sectionId === "home-options") {
      setResultsTab("overview");
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (sectionId === "budget-costs") {
      setResultsTab("budget");
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (sectionId === "moving-timeline") {
      setResultsTab("timeline");
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (sectionId === "lease-review") {
      setResultsTab("lease");
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // 1. Wizard Completion Handler
  const handleWizardSuccess = (projectData: any) => {
    setProject(projectData);
    setShowWizardModal(false);
    setErrorMsg(null);
    setResultsTab("overview");
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 150);
  };

  // 2. Dynamic Replanning on Upfront Budget Change
  const handleReplan = async (newUpfrontBudgetInr: number) => {
    if (!project) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${project.project_id}/replan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          upfront_budget_limit_inr: newUpfrontBudgetInr,
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Unable to recalculate your moving plan with the new budget.");
      }
      const updated = await res.json();
      setProject(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update your plan. Please check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  // 3. User Decision Action (Accept / Choice A / Choice B)
  const handleDecision = async (action: string) => {
    if (!project) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${project.project_id}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision_action: action }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Unable to save your choice.");
      }
      const updated = await res.json();
      setProject(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit choice. Please check connection.");
    } finally {
      setLoading(false);
    }
  };

  // 4. Select Candidate Property
  const handleSelectProperty = async (propertyId: string) => {
    if (!project) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${project.project_id}/select-property`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ property_id: propertyId }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to select this property.");
      }
      const updated = await res.json();
      setProject(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to select property.");
    } finally {
      setLoading(false);
    }
  };

  // 5. Add Custom Property (Manual Entry)
  const handleAddCustomProperty = async (data: any) => {
    if (!project) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${project.project_id}/custom-property`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to save custom property.");
      }
      const updated = await res.json();
      setProject(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to save property.");
    } finally {
      setLoading(false);
    }
  };

  // 6. Document Sample Lease Audit Handler
  const handleAnalyzeSampleDoc = async (sampleFilename: string) => {
    setDocLoading(true);
    setDocAuditResult(null);
    setErrorMsg(null);
    try {
      const projectIdParam = project?.project_id ? `&project_id=${project.project_id}` : "";
      const res = await fetch(`${API_BASE}/api/documents/analyze-sample?sample_filename=${sampleFilename}${projectIdParam}`, {
        method: "POST"
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Unable to analyze lease sample.");
      }
      const data = await res.json();
      setDocAuditResult(data.audit);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to analyze document.");
    } finally {
      setDocLoading(false);
    }
  };

  // 7. Document File Upload Audit Handler
  const handleUploadLeaseDocument = async (file: File) => {
    setDocLoading(true);
    setDocAuditResult(null);
    setErrorMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (project?.project_id) {
        formData.append("project_id", project.project_id);
      }
      const res = await fetch(`${API_BASE}/api/documents/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Unable to upload and analyze document.");
      }
      const data = await res.json();
      setDocAuditResult(data.audit);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload document.");
    } finally {
      setDocLoading(false);
    }
  };

  return (
    <div ref={topRef} className="min-h-screen bg-[#fafaf9] text-slate-900 flex flex-col font-sans selection:bg-blue-100 selection:text-blue-900">
      
      {/* Top Navbar */}
      <Navbar 
        onPlanClick={scrollToWizard} 
        onNavigateSection={handleNavigateSection}
        currency={currency}
        onCurrencyChange={setCurrency}
        hasActiveProject={!!project}
      />

      {/* Hero Header Section */}
      <HeroSection 
        onStartClick={scrollToWizard} 
        onExploreClick={scrollToExplainer} 
      />

      {/* Main Content Workspace */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10 flex-1 w-full">
        
        {/* Friendly Error Notice Banner */}
        {errorMsg && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 flex items-start justify-between shadow-xs animate-fadeIn">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-xs text-rose-800">Connection Notice</p>
                <p className="text-xs text-rose-700 mt-0.5">{errorMsg}</p>
              </div>
            </div>
            <button 
              onClick={() => setErrorMsg(null)}
              className="text-xs font-semibold text-rose-500 hover:text-rose-700 p-1"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Overview Metric Summary */}
        <section aria-label="Overview Summary Cards">
          <div className="flex items-center justify-between mb-3.5">
            <div>
              <h2 className="text-base font-bold text-slate-900">Overview</h2>
              <p className="text-xs text-slate-500">Your move at a glance</p>
            </div>
            {project && (
              <button
                onClick={() => setShowWizardModal(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition"
              >
                <PlusCircle className="w-3.5 h-3.5 text-blue-600" />
                <span>Plan Another Move</span>
              </button>
            )}
          </div>

          <DashboardSummary 
            project={project} 
            onOpenWizard={scrollToWizard}
            currency={currency}
          />
        </section>

        {/* Guided Wizard Form (Shown when no project yet) */}
        {!project && (
          <section ref={wizardRef} aria-label="Relocation Setup">
            <div className="text-center max-w-xl mx-auto mb-6 space-y-1">
              <span className="text-xs font-bold text-blue-600 bg-blue-50 px-3 py-1 rounded-full border border-blue-200/60 inline-block mb-1">
                Guided Relocation Setup
              </span>
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">Plan Your Move in 4 Simple Steps</h2>
              <p className="text-xs text-slate-500">
                Answer a few quick questions to receive your tailored home options, moving quotes, and timeline.
              </p>
            </div>

            <WizardForm 
              onSuccess={handleWizardSuccess} 
              apiBase={API_BASE}
              defaultCurrency={currency}
              onCurrencyChange={setCurrency}
            />
          </section>
        )}

        {/* Results Workspace (Shown when project exists) */}
        {project && (
          <section ref={resultsRef} aria-label="Your Moving Plan">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-blue-600 flex items-center">
                  <Sparkles className="w-3.5 h-3.5 mr-1" />
                  Your Moving Plan
                </span>
                <h2 className="text-xl font-extrabold text-slate-900 tracking-tight mt-0.5">
                  {project.origin_city} to {project.destination_city} Relocation
                </h2>
              </div>
              <button
                onClick={() => setShowWizardModal(true)}
                className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center space-x-1 hover:underline"
              >
                <span>Change parameters</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </button>
            </div>

            <ResultsView 
              project={project}
              loading={loading}
              activeTab={resultsTab}
              onTabChange={setResultsTab}
              onReplan={handleReplan}
              onDecision={handleDecision}
              onSelectProperty={handleSelectProperty}
              onAddCustomProperty={handleAddCustomProperty}
              onAnalyzeSampleDoc={handleAnalyzeSampleDoc}
              onUploadLeaseDocument={handleUploadLeaseDocument}
              docAuditResult={docAuditResult}
              docLoading={docLoading}
              currency={currency}
            />
          </section>
        )}

        {/* How NEXMOVE Helps You Move (Agent Explainer) */}
        <section ref={explainerRef} id="how-it-works" aria-label="How NEXMOVE Works">
          <AgentExplainer 
            executionLogs={project?.execution_logs}
            iterationCount={project?.iteration_count}
          />
        </section>

      </main>

      {/* Modal for Starting Another Move while one is active */}
      {showWizardModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-3xl w-full p-6 sm:p-8 shadow-2xl border border-slate-200 my-8 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Plan a New Relocation</h3>
                <p className="text-xs text-slate-500">Configure parameters to generate a fresh moving plan</p>
              </div>
              <button
                onClick={() => setShowWizardModal(false)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 font-bold transition text-sm"
              >
                ✕
              </button>
            </div>

            <WizardForm 
              onSuccess={handleWizardSuccess} 
              apiBase={API_BASE}
              defaultCurrency={currency}
              onCurrencyChange={setCurrency}
            />
          </div>
        </div>
      )}

      {/* Trustworthy Consumer Footer */}
      <footer className="border-t border-slate-200/80 bg-white py-10 mt-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-5">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                NM
              </div>
              <div>
                <p className="font-bold text-slate-900">NEXMOVE — Your next move, made simple.</p>
                <p className="text-[11px] text-slate-400">Autonomous relocation assistance for housing, budgets, moving, and leases.</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500 font-medium">
              <span>Housing & Movers</span>
              <span>•</span>
              <span>Budget Planning</span>
              <span>•</span>
              <span>Lease Review</span>
              <span>•</span>
              <span>Selected Currency: <strong className="text-slate-800">{currency}</strong></span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex flex-col md:flex-row items-center justify-between gap-3 text-[11px] text-slate-400">
            <p>
              NEXMOVE University Project Demonstration. Designed by Omika Shrestha, Pritika Kurup, Neel Wyvern, and Tanmay.
            </p>
            <p className="italic">
              *All property listings and carrier tariffs are synthetic benchmark examples used for testing and demonstration.
            </p>
          </div>
        </div>
      </footer>

    </div>
  );
}
