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
  Sparkles, 
  ChevronDown, 
  ChevronUp, 
  Check, 
  Home, 
  MapPin, 
  Sliders, 
  HelpCircle,
  AlertCircle,
  Upload,
  Plus,
  Filter,
  ArrowUpDown
} from "lucide-react";
import { formatCurrency, getCurrencyFootnote } from "@/lib/currency";

const SAMPLE_LEASE_DESCRIPTIONS: Record<string, string> = {
  "lease_standard_inr.txt": "Fair-market standard agreement: ₹30,000 rent, standard 2-month refundable deposit, 1-month notice, and routine wear-and-tear terms.",
  "lease_redflag_inr.txt": "High-risk agreement with penalty clauses: Non-refundable 1-month painting deduction, strict pet prohibition with deposit forfeiture, and tight elevator moving hours.",
  "lease_ambiguous_inr.txt": "Incomplete draft agreement: Lacks explicit rupee figures for monthly rent and deposit, creating severe financial ambiguity before signing."
};

interface ResultsViewProps {
  project: any;
  loading: boolean;
  activeTab?: "overview" | "budget" | "timeline" | "lease" | "replan";
  onTabChange?: (tab: "overview" | "budget" | "timeline" | "lease" | "replan") => void;
  onReplan: (newUpfrontBudget: number) => Promise<void>;
  onDecision: (action: string) => Promise<void>;
  onSelectProperty?: (propertyId: string) => Promise<void>;
  onAddCustomProperty?: (data: any) => Promise<void>;
  onAnalyzeSampleDoc: (filename: string) => Promise<void>;
  onUploadLeaseDocument?: (file: File) => Promise<void>;
  docAuditResult: any;
  docLoading: boolean;
  currency: string;
}

export default function ResultsView({
  project,
  loading,
  activeTab,
  onTabChange,
  onReplan,
  onDecision,
  onSelectProperty,
  onAddCustomProperty,
  onAnalyzeSampleDoc,
  onUploadLeaseDocument,
  docAuditResult,
  docLoading,
  currency
}: ResultsViewProps) {
  // Navigation tabs with plain English labels
  const [internalTab, setInternalTab] = useState<"overview" | "budget" | "timeline" | "lease" | "replan">("overview");
  const currentTab = activeTab ?? internalTab;

  const handleTabClick = (tab: "overview" | "budget" | "timeline" | "lease" | "replan") => {
    if (onTabChange) {
      onTabChange(tab);
    } else {
      setInternalTab(tab);
    }
  };
  
  // Replan Budget Slider
  const [replanBudgetInr, setReplanBudgetInr] = useState<number>(
    project.budget_audit?.upfront_budget_limit_inr ? project.budget_audit.upfront_budget_limit_inr - 20000 : 120000
  );

  // Sample lease file selector
  const [selectedLeaseFile, setSelectedLeaseFile] = useState<string>("lease_standard_inr.txt");

  // Optional Technical Details Accordion (Hidden by default)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  // Image fallback state
  const [propertyImgError, setPropertyImgError] = useState(false);

  // Housing filter & sort state
  const [filterBhk, setFilterBhk] = useState<number | "ALL">("ALL");
  const [filterPetOnly, setFilterPetOnly] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<"RECOMMENDED" | "RENT_ASC" | "UPFRONT_ASC" | "COMMUTE_ASC">("RECOMMENDED");

  // Manual property entry modal state
  const [showManualPropertyModal, setShowManualPropertyModal] = useState(false);
  const [manualTitle, setManualTitle] = useState("");
  const [manualNeighborhood, setManualNeighborhood] = useState("");
  const [manualBhk, setManualBhk] = useState(project.home_bhk || 2);
  const [manualRent, setManualRent] = useState(30000);
  const [manualDeposit, setManualDeposit] = useState(60000);
  const [manualMaintenance, setManualMaintenance] = useState(2500);
  const [manualCommute, setManualCommute] = useState(30);
  const [manualPetFriendly, setManualPetFriendly] = useState(project.has_pets || false);
  const [manualSubmitting, setManualSubmitting] = useState(false);

  // File upload state
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

  const housing = project.housing_proposal;
  const availableOptions = project.available_housing_options || (housing ? [housing] : []);
  const activePropertyId = project.selected_property_id || housing?.property_id;

  const logistics = project.logistics_estimate;
  const budget = project.budget_audit;
  const schedule = project.schedule_plan;
  const synthesized = project.synthesized_plan;
  const logs = project.execution_logs || [];

  const upfrontSpent = budget?.total_upfront_outlay_inr || 0;
  const upfrontLimit = project.upfront_budget_limit_inr || 0;
  const upfrontVariance = upfrontLimit - upfrontSpent;
  const isUpfrontOver = upfrontVariance < 0;

  const monthlySpent = budget?.recurring_monthly_costs?.total_recurring_monthly_inr || 0;
  const monthlyLimit = project.monthly_budget_limit_inr || 0;
  const monthlyVariance = monthlyLimit - monthlySpent;
  const isMonthlyOver = monthlyVariance < 0;

  const currencyFootnote = getCurrencyFootnote(currency);

  // Group lease findings if audit exists
  const flaggedClauses = docAuditResult?.flagged_clauses_for_review || [];
  const needsAttention = flaggedClauses.filter((c: any) => c.severity === "HIGH");
  const worthChecking = flaggedClauses.filter((c: any) => c.severity === "MEDIUM");
  const informational = flaggedClauses.filter((c: any) => c.severity === "LOW" || !c.severity);

  // Filter & sort candidate options
  let filteredOptions = availableOptions.filter((opt: any) => {
    if (filterBhk !== "ALL" && opt.bhk !== filterBhk) return false;
    if (filterPetOnly && !opt.pet_friendly) return false;
    return true;
  });

  if (sortBy === "RENT_ASC") {
    filteredOptions = [...filteredOptions].sort((a, b) => a.monthly_rent_inr - b.monthly_rent_inr);
  } else if (sortBy === "UPFRONT_ASC") {
    filteredOptions = [...filteredOptions].sort((a, b) => (a.total_upfront_outlay_inr || (a.security_deposit_inr + a.monthly_rent_inr)) - (b.total_upfront_outlay_inr || (b.security_deposit_inr + b.monthly_rent_inr)));
  } else if (sortBy === "COMMUTE_ASC") {
    filteredOptions = [...filteredOptions].sort((a, b) => (a.commute_to_workplace_mins || 999) - (b.commute_to_workplace_mins || 999));
  }

  const handleManualPropertySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onAddCustomProperty) return;
    setManualSubmitting(true);
    try {
      await onAddCustomProperty({
        title: manualTitle.trim() || `${manualBhk} BHK Apartment in ${manualNeighborhood || project.destination_city}`,
        neighborhood: manualNeighborhood.trim() || "Central Area",
        bhk: Number(manualBhk),
        monthly_rent_inr: Number(manualRent),
        security_deposit_inr: Number(manualDeposit),
        society_maintenance_inr: Number(manualMaintenance),
        move_in_fee_inr: 0,
        commute_to_workplace_mins: Number(manualCommute),
        pet_friendly: Boolean(manualPetFriendly),
        property_type: "Manual Entry"
      });
      setShowManualPropertyModal(false);
    } catch {
      // handled by parent
    } finally {
      setManualSubmitting(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUploadLeaseDocument) {
      setUploadedFileName(file.name);
      onUploadLeaseDocument(file);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      
      {/* 1. Header Banner & Plan Status */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
              project.status === "CONSENSUS_REACHED" || project.status === "APPROVED"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : project.status === "AWAITING_USER_DECISION"
                ? "bg-amber-50 text-amber-800 border border-amber-200"
                : "bg-blue-50 text-blue-800 border border-blue-200"
            }`}>
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
              {project.status === "CONSENSUS_REACHED"
                ? "Plan Agreed"
                : project.status === "APPROVED"
                ? "Plan Accepted"
                : project.status === "AWAITING_USER_DECISION"
                ? "Your Choice Needed"
                : project.status === "NO_HOUSING_AVAILABLE"
                ? "No Properties Found"
                : "Plan Ready"}
            </span>

            <span className="text-xs text-slate-500 font-medium bg-slate-50 px-2.5 py-1 rounded-full border border-slate-100">
              {project.origin_city} to {project.destination_city}
            </span>
          </div>

          <h2 className="text-2xl font-black text-slate-900 tracking-tight mt-2">
            {project.status === "NO_HOUSING_AVAILABLE" 
              ? `No Housing Available in ${project.destination_city}`
              : (synthesized?.recommended_housing_title || `${project.origin_city} to ${project.destination_city} Moving Plan`)}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Target move date: <strong className="text-slate-700">{project.target_move_date}</strong> • {project.home_bhk} BHK • {project.has_pets ? "Pet Friendly" : "No Pets"}
          </p>
        </div>

        {/* Accept Button / Approval Badge */}
        <div className="flex items-center space-x-2">
          {project.status === "CONSENSUS_REACHED" && (
            <button
              onClick={() => onDecision("APPROVE")}
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-sm transition"
            >
              <Check className="w-4 h-4" />
              <span>Accept This Plan</span>
            </button>
          )}

          {project.status === "APPROVED" && (
            <div className="px-4 py-2 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 font-bold text-xs flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              <span>Plan Accepted</span>
            </div>
          )}
        </div>
      </div>

      {/* Warning when destination has no listings */}
      {(!housing || project.status === "NO_HOUSING_AVAILABLE") && (
        <div className="bg-amber-50/90 border-2 border-amber-300 rounded-3xl p-6 shadow-xs space-y-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-2">
              <h3 className="text-base font-bold text-amber-950">No Verified Benchmark Listings in {project.destination_city}</h3>
              <p className="text-xs text-amber-900 leading-relaxed">
                Our pre-verified benchmark dataset does not currently index rental apartments in <strong>{project.destination_city}</strong> matching {project.home_bhk} BHK ({project.has_pets ? "pet friendly" : "standard"}).
              </p>
              <p className="text-xs text-amber-900 font-medium">
                NEXMOVE guarantees complete data integrity: we will never substitute listings from another city. You can enter your property details manually or pick a supported benchmark city.
              </p>
              <div className="flex flex-wrap gap-2 pt-2">
                <button
                  onClick={() => setShowManualPropertyModal(true)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center space-x-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Enter Property Manually</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. User Decision / Compromise Choice Banner (if AWAITING_USER_DECISION) */}
      {project.status === "AWAITING_USER_DECISION" && synthesized?.escalation_options && (
        <div className="bg-amber-50/90 border-2 border-amber-300 rounded-3xl p-6 shadow-xs space-y-5">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-base font-bold text-amber-950">Your Choice is Needed to Proceed</h3>
              <p className="text-xs text-amber-900 mt-1 leading-relaxed">
                The moving costs or commute exceeded your budget limits. We prepared two realistic alternatives below so you can choose the trade-off that fits best:
              </p>
            </div>
          </div>

          {/* Financial Shortfall Breakdown */}
          <div className="bg-white/90 rounded-2xl p-4 border border-amber-200 text-xs space-y-3">
            <span className="font-bold text-amber-950 block">Original Budget Shortfall Analysis:</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-[11px] text-slate-500 block">Your Stated Upfront Budget</span>
                <span className="text-sm font-bold text-slate-900">{formatCurrency(project.upfront_budget_limit_inr, currency)}</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-[11px] text-slate-500 block">Required Initial Outlay</span>
                <span className="text-sm font-bold text-slate-900">
                  {formatCurrency(synthesized.escalation_options[0]?.upfront_cost_inr || synthesized.total_upfront_outlay_inr, currency)}
                </span>
              </div>
              <div className="p-3 bg-rose-50 rounded-xl border border-rose-200">
                <span className="text-[11px] text-rose-800 font-semibold block">Upfront Shortfall (Deficit)</span>
                <span className="text-sm font-black text-rose-700">
                  {Math.max(0, (synthesized.escalation_options[0]?.upfront_cost_inr || synthesized.total_upfront_outlay_inr) - project.upfront_budget_limit_inr) > 0
                    ? `+ ${formatCurrency(Math.max(0, (synthesized.escalation_options[0]?.upfront_cost_inr || synthesized.total_upfront_outlay_inr) - project.upfront_budget_limit_inr), currency)}`
                    : "None"}
                </span>
              </div>
            </div>
            {synthesized.escalation_options[0]?.monthly_cost_inr > project.monthly_budget_limit_inr && (
              <p className="text-[11px] text-amber-900">
                • Monthly Living Budget Shortfall: Stated limit {formatCurrency(project.monthly_budget_limit_inr, currency)} vs required {formatCurrency(synthesized.escalation_options[0].monthly_cost_inr, currency)} (Deficit: {formatCurrency(synthesized.escalation_options[0].monthly_cost_inr - project.monthly_budget_limit_inr, currency)}/mo).
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            {synthesized.escalation_options.map((opt: any) => (
              <div 
                key={opt.option_id} 
                className="bg-white rounded-2xl p-5 border border-amber-200 shadow-xs flex flex-col justify-between hover:border-amber-300 transition"
              >
                <div>
                  <span className="inline-block px-2.5 py-0.5 bg-amber-100 text-amber-900 text-[11px] font-bold rounded-md">
                    Choice {opt.option_id}
                  </span>
                  <h4 className="font-bold text-sm text-slate-900 mt-2">{opt.title}</h4>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">{opt.trade_off_summary}</p>

                  <div className="mt-3.5 pt-3 border-t border-slate-100 text-xs space-y-1.5 text-slate-600">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Upfront moving cost:</span>
                      <span className="font-bold text-slate-900">{formatCurrency(opt.upfront_cost_inr, currency)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Expected office commute:</span>
                      <span className="font-bold text-slate-900">~{opt.commute_mins} minutes</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => onDecision(`SELECT_OPTION_${opt.option_id}`)}
                  disabled={loading}
                  className="mt-4 w-full py-2.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center justify-center space-x-1.5 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Updating plan...</span>
                    </>
                  ) : (
                    <span>Choose Choice {opt.option_id}</span>
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Navigation Tabs in Plain English */}
      <div className="flex border-b border-slate-200 space-x-2 sm:space-x-6 text-xs sm:text-sm font-semibold overflow-x-auto pb-px">
        <button
          onClick={() => handleTabClick("overview")}
          className={`pb-3 whitespace-nowrap transition border-b-2 ${
            currentTab === "overview"
              ? "text-blue-600 border-blue-600 font-bold"
              : "text-slate-500 hover:text-slate-800 border-transparent"
          }`}
        >
          Home Options & Moving
        </button>

        <button
          onClick={() => handleTabClick("budget")}
          className={`pb-3 whitespace-nowrap transition border-b-2 ${
            currentTab === "budget"
              ? "text-blue-600 border-blue-600 font-bold"
              : "text-slate-500 hover:text-slate-800 border-transparent"
          }`}
        >
          Budget & Costs
        </button>

        <button
          onClick={() => handleTabClick("timeline")}
          className={`pb-3 whitespace-nowrap transition border-b-2 ${
            currentTab === "timeline"
              ? "text-blue-600 border-blue-600 font-bold"
              : "text-slate-500 hover:text-slate-800 border-transparent"
          }`}
        >
          Moving Timeline
        </button>

        <button
          onClick={() => {
            handleTabClick("lease");
            if (!docAuditResult && !docLoading) {
              onAnalyzeSampleDoc(selectedLeaseFile);
            }
          }}
          className={`pb-3 whitespace-nowrap transition border-b-2 ${
            currentTab === "lease"
              ? "text-blue-600 border-blue-600 font-bold"
              : "text-slate-500 hover:text-slate-800 border-transparent"
          }`}
        >
          Lease Review
        </button>

        <button
          onClick={() => handleTabClick("replan")}
          className={`pb-3 whitespace-nowrap transition border-b-2 ${
            currentTab === "replan"
              ? "text-blue-600 border-blue-600 font-bold"
              : "text-slate-500 hover:text-slate-800 border-transparent"
          }`}
        >
          Try a Budget Change
        </button>
      </div>

      {/* ==================================================================== */}
      {/* TAB 1: HOME OPTIONS & RECOMMENDED HOME */}
      {/* ==================================================================== */}
      {currentTab === "overview" && (
        <div className="space-y-8">
          
          {/* Main Selected Home & Logistics Hero */}
          {housing && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Left Card: Active Property Photo & Details (7 cols) */}
              <div className="lg:col-span-7 bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider block">
                      Active Selected Home
                    </span>
                    <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                      {housing?.title || "Modern 2BHK Apartment"}
                    </h3>
                    <p className="text-xs text-slate-500 flex items-center mt-1">
                      <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" />
                      <span>{housing?.neighborhood}, {housing?.city}</span>
                    </p>
                  </div>

                  <span className="text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full">
                    Selected for Plan
                  </span>
                </div>

                {/* Apartment Photo with Clear Illustrative Label */}
                <div className="relative rounded-2xl overflow-hidden aspect-[16/9] max-h-80 bg-slate-100">
                  {!propertyImgError ? (
                    <img
                      src="https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1000&q=80"
                      alt="Bright living room of recommended apartment"
                      className="w-full h-full object-cover max-h-80"
                      style={{ maxHeight: "320px", width: "100%", objectFit: "cover" }}
                      onError={() => setPropertyImgError(true)}
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center p-6 text-slate-400">
                      <Home className="w-10 h-10 mb-2 text-slate-300" />
                      <span className="text-xs font-medium">Apartment Preview</span>
                    </div>
                  )}
                  <div className="absolute bottom-2.5 left-2.5 bg-slate-900/75 backdrop-blur-xs text-white text-[10px] font-medium px-2.5 py-1 rounded-md">
                    Example property photo (illustrative)
                  </div>
                </div>

                {/* Key Highlights Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                    <span className="text-[11px] text-slate-400 block">Monthly Rent</span>
                    <span className="text-sm font-bold text-slate-900">
                      {formatCurrency(housing?.monthly_rent_inr, currency)}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                    <span className="text-[11px] text-slate-400 block">Security Deposit</span>
                    <span className="text-sm font-bold text-slate-900">
                      {formatCurrency(housing?.security_deposit_inr, currency)}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                    <span className="text-[11px] text-slate-400 block">Office Commute</span>
                    <span className="text-sm font-bold text-emerald-600">
                      {housing?.commute_to_workplace_mins || 25} mins
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                    <span className="text-[11px] text-slate-400 block">Pet Suitable</span>
                    <span className="text-sm font-bold text-slate-800">
                      {housing?.pet_friendly ? "Yes (Permitted)" : "No"}
                    </span>
                  </div>
                </div>

                {/* Property Description */}
                <p className="text-xs text-slate-600 leading-relaxed pt-1">
                  {housing?.description || "Spacious, well-ventilated apartment located in a secure gated community with 24/7 power backup and designated parking."}
                </p>
              </div>

              {/* Right Card: Moving Logistics & Why Recommended (5 cols) */}
              <div className="lg:col-span-5 space-y-6">
                
                {/* Estimated Moving Transport */}
                <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center">
                      <Truck className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
                      Estimated Moving Cost
                    </span>
                    <span className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      Door-to-Door
                    </span>
                  </div>

                  <div>
                    <h4 className="text-lg font-bold text-slate-900">
                      {logistics?.vehicle_type || "Dedicated 14ft Moving Truck"}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {logistics?.route} ({logistics?.distance_km} km)
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-50">
                      <span className="text-[11px] text-slate-400 block">Total Moving Quote</span>
                      <span className="font-bold text-slate-900 text-sm">
                        {formatCurrency(logistics?.total_logistics_inr, currency)}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-50">
                      <span className="text-[11px] text-slate-400 block">Transit Time</span>
                      <span className="font-bold text-slate-900 text-sm">
                        {logistics?.estimated_transit_days || 2} Days
                      </span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-100 text-xs space-y-1.5 text-slate-600">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Scheduled packing & pickup:</span>
                      <span className="font-semibold text-slate-800">{logistics?.recommended_pickup_date}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Estimated delivery:</span>
                      <span className="font-semibold text-slate-800">{logistics?.estimated_delivery_date}</span>
                    </div>
                  </div>
                </div>

                {/* Why We Recommend This Plan */}
                <div className="bg-slate-50 rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center">
                    <Sparkles className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
                    Why We Recommend This Plan
                  </h4>

                  {synthesized?.trade_offs_resolved && synthesized.trade_offs_resolved.length > 0 ? (
                    <div className="space-y-2 text-xs text-slate-700">
                      {synthesized.trade_offs_resolved.map((trade: string, i: number) => (
                        <div key={i} className="p-3 bg-white rounded-xl border border-slate-200/70 leading-relaxed">
                          {trade}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-600 leading-relaxed bg-white p-3 rounded-xl border border-slate-200/70">
                      This home matches your preferred apartment size, respects family pet permissions, stays within your travel distance to the workplace, and fits cleanly inside your moving budget.
                    </p>
                  )}

                  {synthesized?.user_advisories && synthesized.user_advisories.length > 0 && (
                    <div className="pt-2 text-xs">
                      <span className="font-semibold text-slate-700 block mb-1">Helpful Advice for Your Move:</span>
                      <ul className="list-disc list-inside space-y-1 text-slate-600 text-[11px]">
                        {synthesized.user_advisories.map((adv: string, idx: number) => (
                          <li key={idx}>{adv}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

              </div>

            </div>
          )}

          {/* Multiple Housing Options Section */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-xl font-bold text-slate-900">
                  Candidate Home Options in {project.destination_city}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Compare all matching properties. Selecting any option automatically updates your move budget, transit, and timeline.
                </p>
              </div>

              <button
                onClick={() => setShowManualPropertyModal(true)}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold transition w-fit"
              >
                <Plus className="w-3.5 h-3.5 text-blue-600" />
                <span>Enter Property Manually</span>
              </button>
            </div>

            {/* Filter and Sort Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 pb-1 border-b border-slate-100 text-xs">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-slate-500 font-semibold flex items-center">
                  <Filter className="w-3.5 h-3.5 mr-1" />
                  Filter:
                </span>
                
                {/* BHK Filter */}
                <div className="flex gap-1">
                  {(["ALL", 1, 2, 3] as const).map((b) => (
                    <button
                      key={String(b)}
                      type="button"
                      onClick={() => setFilterBhk(b)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                        filterBhk === b
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      {b === "ALL" ? "All BHK" : `${b} BHK`}
                    </button>
                  ))}
                </div>

                {/* Pet Friendly Toggle */}
                <button
                  type="button"
                  onClick={() => setFilterPetOnly(!filterPetOnly)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
                    filterPetOnly
                      ? "bg-slate-800 text-white border-slate-800"
                      : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                  }`}
                >
                  {filterPetOnly ? "✓ Pet Friendly Only" : "Pet Friendly"}
                </button>
              </div>

              {/* Sort Dropdown */}
              <div className="flex items-center space-x-1.5 text-slate-600">
                <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-semibold text-slate-500">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="RECOMMENDED">Top Recommended</option>
                  <option value="RENT_ASC">Lowest Monthly Rent</option>
                  <option value="UPFRONT_ASC">Lowest Upfront Outlay</option>
                  <option value="COMMUTE_ASC">Shortest Office Commute</option>
                </select>
              </div>
            </div>

            {/* Single Property Match Explanation */}
            {filteredOptions.length === 1 && (
              <div className="p-3 bg-blue-50/70 rounded-xl border border-blue-200/80 text-xs text-blue-900 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <span>
                  Showing the <strong>1 property</strong> matching your specific requirements in {project.destination_city} ({filterBhk === "ALL" ? `${project.home_bhk} BHK` : `${filterBhk} BHK`}{filterPetOnly ? ", Pet Friendly" : ""}).
                </span>
                {(filterBhk !== "ALL" || filterPetOnly) && (
                  <button
                    onClick={() => { setFilterBhk("ALL"); setFilterPetOnly(false); }}
                    className="text-[11px] font-bold text-blue-700 underline hover:text-blue-800 whitespace-nowrap"
                  >
                    Reset filters to view all options
                  </button>
                )}
              </div>
            )}

            {/* Property Cards Grid */}
            {filteredOptions.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
                {filteredOptions.map((prop: any) => {
                  const isSelected = prop.property_id === activePropertyId;
                  const upfrontCost = prop.total_upfront_outlay_inr || (prop.security_deposit_inr + prop.monthly_rent_inr);
                  const monthlyCost = prop.total_recurring_monthly_inr || (prop.monthly_rent_inr + (prop.society_maintenance_inr || 0));

                  return (
                    <div 
                      key={prop.proposal_id || prop.property_id}
                      className={`rounded-2xl p-5 border transition flex flex-col justify-between ${
                        isSelected 
                          ? "border-emerald-400 bg-emerald-50/20 shadow-xs ring-2 ring-emerald-400/40"
                          : "border-slate-200/90 bg-white hover:border-slate-300 shadow-2xs"
                      }`}
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                              {prop.bhk} BHK • {prop.property_type || "Apartment"}
                            </span>
                            <h4 className="font-bold text-sm text-slate-900 mt-0.5 leading-snug">
                              {prop.title}
                            </h4>
                            <p className="text-[11px] text-slate-500 flex items-center mt-0.5">
                              <MapPin className="w-3 h-3 mr-0.5 text-slate-400" />
                              <span>{prop.neighborhood}, {prop.city}</span>
                            </p>
                          </div>

                          {isSelected ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 flex-shrink-0">
                              Selected
                            </span>
                          ) : prop.is_verified ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600 flex-shrink-0">
                              Verified
                            </span>
                          ) : null}
                        </div>

                        {/* Financial Metrics */}
                        <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
                          <div className="p-2.5 rounded-xl bg-slate-50">
                            <span className="text-[10px] text-slate-400 block">Monthly Rent</span>
                            <span className="font-bold text-slate-900">
                              {formatCurrency(prop.monthly_rent_inr, currency)}
                            </span>
                          </div>
                          <div className="p-2.5 rounded-xl bg-slate-50">
                            <span className="text-[10px] text-slate-400 block">Upfront Outlay</span>
                            <span className="font-bold text-slate-900">
                              {formatCurrency(upfrontCost, currency)}
                            </span>
                          </div>
                        </div>

                        {/* Commute and Features */}
                        <div className="text-[11px] text-slate-600 space-y-1 pt-1 border-t border-slate-100">
                          <div className="flex justify-between">
                            <span className="text-slate-400">Deposit:</span>
                            <span className="font-medium">{formatCurrency(prop.security_deposit_inr, currency)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Office Commute:</span>
                            <span className="font-bold text-emerald-600">{prop.commute_to_workplace_mins || 25} mins</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Pet Policy:</span>
                            <span className="font-medium">{prop.pet_friendly ? "Permitted" : "No Pets"}</span>
                          </div>
                        </div>
                      </div>

                      {/* Select CTA */}
                      <div className="pt-4 mt-2">
                        {isSelected ? (
                          <div className="w-full py-2 bg-emerald-600 text-white rounded-xl text-xs font-bold text-center flex items-center justify-center space-x-1 shadow-2xs">
                            <Check className="w-3.5 h-3.5" />
                            <span>Currently Active in Plan</span>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => onSelectProperty && onSelectProperty(prop.property_id)}
                            disabled={loading}
                            className="w-full py-2 bg-slate-900 hover:bg-blue-600 text-white rounded-xl text-xs font-semibold text-center transition shadow-2xs disabled:opacity-50"
                          >
                            Select This Home
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-10 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                <Home className="w-8 h-8 mx-auto text-slate-400" />
                <div>
                  <p className="text-xs font-semibold text-slate-700">No properties match your active filter in {project.destination_city}.</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">Try resetting your BHK or Pet filters, or enter a property manually.</p>
                </div>
                <div className="flex justify-center gap-2 pt-1">
                  {(filterBhk !== "ALL" || filterPetOnly) && (
                    <button
                      onClick={() => { setFilterBhk("ALL"); setFilterPetOnly(false); }}
                      className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-100"
                    >
                      Reset Filters
                    </button>
                  )}
                  <button
                    onClick={() => setShowManualPropertyModal(true)}
                    className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700"
                  >
                    Enter Property Manually
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: BUDGET & COSTS */}
      {/* ==================================================================== */}
      {currentTab === "budget" && budget && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-8">
          <div>
            <h3 className="text-xl font-bold text-slate-900">Budget & Costs</h3>
            <p className="text-xs text-slate-500 mt-1">
              Clear breakdown of your one-time moving expenses and ongoing monthly costs.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Box 1: One-Time Moving Costs */}
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                    Money Needed Upfront
                  </span>
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                    isUpfrontOver ? "bg-rose-100 text-rose-800" : "bg-emerald-100 text-emerald-800"
                  }`}>
                    {isUpfrontOver ? "Over Budget" : "Within Budget"}
                  </span>
                </div>

                <div className="text-3xl font-extrabold text-slate-900">
                  {formatCurrency(upfrontSpent, currency)}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Budget limit: {formatCurrency(upfrontLimit, currency)}
                </p>

                {/* Progress bar */}
                <div className="my-4">
                  <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${isUpfrontOver ? "bg-rose-500" : "bg-emerald-500"}`}
                      style={{ width: `${Math.min((upfrontSpent / (upfrontLimit || 1)) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500 mt-1.5 font-medium">
                    <span>Spent: {Math.round((upfrontSpent / (upfrontLimit || 1)) * 100)}%</span>
                    <span className={isUpfrontOver ? "text-rose-600 font-bold" : "text-emerald-700 font-bold"}>
                      {isUpfrontOver 
                        ? `${formatCurrency(Math.abs(upfrontVariance), currency)} over budget` 
                        : `${formatCurrency(upfrontVariance, currency)} buffer remaining`}
                    </span>
                  </div>
                </div>

                {/* Breakdown items */}
                <div className="space-y-2.5 text-xs pt-3 border-t border-slate-200">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Movers & Freight Truck:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.one_time_costs?.packers_movers_inr, currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Transit Insurance:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.one_time_costs?.transit_insurance_inr, currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Travel & Tickets:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.one_time_costs?.travel_tickets_inr, currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Packing Supplies & Boxes:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.one_time_costs?.packing_supplies_inr, currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Rental Security Deposit:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.housing_outlay?.security_deposit_inr, currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">First Month Advance Rent:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.housing_outlay?.advance_rent_inr, currency)}
                    </span>
                  </div>
                  {budget.housing_outlay?.move_in_fee_inr > 0 && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Move-in Society Fee:</span>
                      <span className="font-semibold text-slate-800">
                        {formatCurrency(budget.housing_outlay?.move_in_fee_inr, currency)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Box 2: Recurring Monthly Living */}
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50/60 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                    Monthly Living Costs
                  </span>
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                    isMonthlyOver ? "bg-rose-100 text-rose-800" : "bg-emerald-100 text-emerald-800"
                  }`}>
                    {isMonthlyOver ? "Over Budget" : "Within Budget"}
                  </span>
                </div>

                <div className="text-3xl font-extrabold text-slate-900">
                  {formatCurrency(monthlySpent, currency)}
                  <span className="text-sm font-normal text-slate-400">/mo</span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Budget limit: {formatCurrency(monthlyLimit, currency)}/mo
                </p>

                {/* Progress bar */}
                <div className="my-4">
                  <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${isMonthlyOver ? "bg-rose-500" : "bg-blue-600"}`}
                      style={{ width: `${Math.min((monthlySpent / (monthlyLimit || 1)) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500 mt-1.5 font-medium">
                    <span>Used: {Math.round((monthlySpent / (monthlyLimit || 1)) * 100)}%</span>
                    <span className={isMonthlyOver ? "text-rose-600 font-bold" : "text-emerald-700 font-bold"}>
                      {isMonthlyOver 
                        ? `${formatCurrency(Math.abs(monthlyVariance), currency)} over budget` 
                        : `${formatCurrency(monthlyVariance, currency)} buffer remaining`}
                    </span>
                  </div>
                </div>

                {/* Breakdown items */}
                <div className="space-y-2.5 text-xs pt-3 border-t border-slate-200">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Monthly House Rent:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.recurring_monthly_costs?.monthly_base_rent_inr, currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Society Maintenance:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.recurring_monthly_costs?.society_maintenance_inr, currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Utilities (Electricity, Water, Wi-Fi):</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.recurring_monthly_costs?.estimated_utilities_inr, currency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Estimated Commute & Travel:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(budget.recurring_monthly_costs?.estimated_commute_inr, currency)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

          </div>

          {currencyFootnote && (
            <p className="text-xs text-slate-400 italic">
              *{currencyFootnote}
            </p>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 3: MOVING TIMELINE */}
      {/* ==================================================================== */}
      {currentTab === "timeline" && schedule && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-xl font-bold text-slate-900">Moving Timeline</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Suggested chronological roadmap based on your move date and transit days. (Planning guide, not confirmed vendor bookings).
              </p>
            </div>
            <span className="text-xs font-semibold px-3 py-1 bg-blue-50 text-blue-800 border border-blue-200 rounded-full w-fit">
              Suggested Tasks (Not Bookings)
            </span>
          </div>

          <div className="space-y-3 pt-2">
            {schedule.critical_path_milestones?.map((m: any, idx: number) => {
              const isNeedsAttention = m.is_critical_path;
              const statusLabel = isNeedsAttention ? "Suggested Critical Task" : "Suggested Task";

              return (
                <div 
                  key={idx} 
                  className={`p-4 rounded-2xl border transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    isNeedsAttention 
                      ? "border-blue-200 bg-blue-50/40" 
                      : "border-slate-200/70 bg-white hover:bg-slate-50/50"
                  }`}
                >
                  <div className="flex items-start space-x-3.5">
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5 ${
                      isNeedsAttention ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700"
                    }`}>
                      {m.step_id || idx + 1}
                    </div>

                    <div>
                      <h4 className="font-bold text-sm text-slate-900">{m.task_name}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Responsible: <span className="font-medium text-slate-700">{m.owner_party}</span>
                        {m.notes ? ` • ${m.notes}` : ""}
                      </p>
                    </div>
                  </div>

                  <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-slate-900 bg-white sm:bg-transparent px-2.5 py-1 rounded-md border sm:border-0 border-slate-200">
                      {m.target_date}
                    </span>
                    <span className={`text-[11px] font-semibold mt-0.5 ${
                      isNeedsAttention ? "text-blue-700" : "text-slate-500"
                    }`}>
                      {statusLabel}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 4: LEASE REVIEW */}
      {/* ==================================================================== */}
      {currentTab === "lease" && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
          <div>
            <h3 className="text-xl font-bold text-slate-900">Lease Review</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Highlights clauses that deserve closer attention before you sign your rental agreement.
            </p>
          </div>

          {/* Legal Disclaimer Box */}
          <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 text-amber-900 flex items-start space-x-3">
            <Info className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
            <div className="text-xs">
              <span className="font-bold text-amber-950 block">Informational Review Notice</span>
              <p className="mt-0.5 text-amber-900 leading-relaxed">
                This automated review provides helpful tips and suggested questions to ask your landlord. It does not constitute formal legal representation or legal advice.
              </p>
            </div>
          </div>

          {/* Document Input Options: Sample Selector OR File Upload */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Box A: Sample Agreement Picker */}
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
              <label className="block font-bold text-slate-800">
                Option A: Review an Example Agreement
              </label>
              <select
                value={selectedLeaseFile}
                onChange={(e) => {
                  setSelectedLeaseFile(e.target.value);
                  onAnalyzeSampleDoc(e.target.value);
                }}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="lease_standard_inr.txt">Example 1: Standard Bengaluru 2BHK Lease (HSR Layout)</option>
                <option value="lease_redflag_inr.txt">Example 2: Strict Agreement with Penalty Clauses (Indiranagar)</option>
                <option value="lease_ambiguous_inr.txt">Example 3: Draft Agreement (Missing Rent / Deposit Terms)</option>
              </select>

              {/* Sample Description */}
              <p className="text-[11px] text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200 leading-relaxed">
                <span className="font-semibold text-slate-800">What this test covers: </span>
                {SAMPLE_LEASE_DESCRIPTIONS[selectedLeaseFile] || "Pre-packaged sample lease for evaluation."}
              </p>

              <button
                onClick={() => onAnalyzeSampleDoc(selectedLeaseFile)}
                disabled={docLoading}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
              >
                {docLoading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Analyzing clauses...</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-3.5 h-3.5" />
                    <span>Check Selected Agreement</span>
                  </>
                )}
              </button>
            </div>

            {/* Box B: File Upload Input */}
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
              <label className="block font-bold text-slate-800">
                Option B: Upload Your Own Agreement
              </label>
              <div className="relative border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-4 text-center cursor-pointer transition bg-white">
                <input
                  type="file"
                  accept=".txt,.pdf"
                  onChange={handleFileUpload}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <Upload className="w-5 h-5 mx-auto text-slate-400 mb-1" />
                <span className="block font-semibold text-slate-700">
                  {uploadedFileName ? uploadedFileName : "Click or drag text/PDF agreement here"}
                </span>
                <span className="block text-[10px] text-slate-400 mt-0.5">Supports .txt and .pdf files</span>
              </div>

              {uploadedFileName && (
                <div className="text-[11px] text-emerald-700 font-medium flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>File loaded: {uploadedFileName}</span>
                </div>
              )}
            </div>

          </div>

          {/* Analysis In Progress Indicator */}
          {docLoading && (
            <div className="p-8 rounded-2xl bg-blue-50/60 border border-blue-200 text-center space-y-3">
              <RefreshCw className="w-6 h-6 mx-auto text-blue-600 animate-spin" />
              <div>
                <h4 className="font-bold text-sm text-blue-900">Document Intelligence Agent Analyzing Agreement...</h4>
                <p className="text-xs text-blue-700 mt-0.5">Extracting rent, deposit, notice terms, and flagging potential contractual risks.</p>
              </div>
            </div>
          )}

          {/* Audit Results Grouped by Plain Categories */}
          {docAuditResult && (
            <div className="space-y-6 pt-2">
              
              {/* Needs manual review notice if terms missing */}
              {docAuditResult.parse_status === "NEEDS_MANUAL_REVIEW" && (
                <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 text-amber-950 text-xs flex items-start space-x-3 shadow-xs">
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-bold text-sm text-amber-950">Needs Manual Review</h5>
                    <p className="mt-0.5 text-amber-900 leading-relaxed">
                      Certain key lease terms (such as explicit rent or security deposit amounts) were missing or unstated in this agreement text. We recommend requesting an explicit written schedule of charges before signing.
                    </p>
                  </div>
                </div>
              )}

              {/* Extracted Basics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Rent Stated in Lease</span>
                  <span className="font-bold text-slate-900 text-sm">
                    {docAuditResult.extracted_monthly_rent_inr != null 
                      ? formatCurrency(docAuditResult.extracted_monthly_rent_inr, currency)
                      : <span className="text-amber-700 text-xs font-semibold">Not specified in text</span>}
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Security Deposit</span>
                  <span className="font-bold text-slate-900 text-sm">
                    {docAuditResult.extracted_security_deposit_inr != null 
                      ? formatCurrency(docAuditResult.extracted_security_deposit_inr, currency)
                      : <span className="text-amber-700 text-xs font-semibold">Not specified in text</span>}
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Notice Period</span>
                  <span className="font-bold text-slate-900 text-sm">
                    {docAuditResult.extracted_notice_period_days != null 
                      ? `${docAuditResult.extracted_notice_period_days} Days`
                      : <span className="text-slate-500 text-xs font-normal">Not stated</span>}
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Lock-In Period</span>
                  <span className="font-bold text-slate-900 text-sm">
                    {docAuditResult.extracted_lock_in_months != null && docAuditResult.extracted_lock_in_months > 0
                      ? `${docAuditResult.extracted_lock_in_months} Months`
                      : <span className="text-slate-500 text-xs font-normal">None specified</span>}
                  </span>
                </div>
              </div>

              {/* Group 1: Needs Attention (High Severity) */}
              {needsAttention.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-rose-800">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <h4 className="font-bold text-sm">Needs Attention ({needsAttention.length})</h4>
                  </div>

                  <div className="space-y-3">
                    {needsAttention.map((clause: any, idx: number) => (
                      <div key={idx} className="p-5 rounded-2xl border border-rose-200 bg-rose-50/30 text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <h5 className="font-bold text-slate-900 text-sm">{clause.clause_title}</h5>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                            Needs attention
                          </span>
                        </div>
                        <p className="text-slate-600 italic bg-white p-3 rounded-xl border border-slate-200 text-[11px]">
                          "{clause.clause_text || clause.raw_text}"
                        </p>
                        <div className="text-slate-700 space-y-1 pt-1">
                          <div><strong>Why it matters:</strong> {clause.issue_rationale || clause.advisory_note}</div>
                          {clause.suggested_action && (
                            <div className="text-blue-800 font-medium">
                              <strong>Question to ask landlord:</strong> {clause.suggested_action}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Group 2: Worth Checking (Medium Severity) */}
              {worthChecking.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-amber-800">
                    <Info className="w-4 h-4 text-amber-600" />
                    <h4 className="font-bold text-sm">Worth Checking ({worthChecking.length})</h4>
                  </div>

                  <div className="space-y-3">
                    {worthChecking.map((clause: any, idx: number) => (
                      <div key={idx} className="p-4 rounded-xl border border-amber-200 bg-amber-50/30 text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <h5 className="font-bold text-slate-900">{clause.clause_title}</h5>
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800">
                            Check Details
                          </span>
                        </div>
                        <p className="text-slate-600 italic bg-white p-2.5 rounded-lg border border-slate-200 text-[11px]">
                          "{clause.clause_text || clause.raw_text}"
                        </p>
                        <p className="text-slate-700">{clause.issue_rationale}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Group 3: Informational Notes */}
              {informational.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-slate-600">
                    <ShieldCheck className="w-4 h-4 text-slate-400" />
                    <h4 className="font-bold text-sm">Informational Notes ({informational.length})</h4>
                  </div>

                  <div className="space-y-2">
                    {informational.map((clause: any, idx: number) => (
                      <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50 text-xs space-y-1">
                        <div className="flex items-center justify-between font-bold text-slate-800">
                          <span>{clause.clause_title}</span>
                          <span className="text-[10px] text-slate-500 bg-slate-200 px-2 py-0.5 rounded">Standard</span>
                        </div>
                        <p className="text-slate-600 text-[11px]">{clause.issue_rationale}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {flaggedClauses.length === 0 && (
                <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2.5">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  <span>No high-risk penalty clauses or hidden fees were found in this agreement.</span>
                </div>
              )}

            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 5: WHAT IF MY BUDGET CHANGES? */}
      {/* ==================================================================== */}
      {currentTab === "replan" && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
          <div>
            <h3 className="text-xl font-bold text-slate-900">What If My Budget Changes?</h3>
            <p className="text-xs text-slate-500 mt-1">
              Adjust your budget to see whether your current moving plan still works.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 space-y-4 max-w-xl">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-800">Adjust Upfront Moving Budget</span>
              <span className="text-base font-extrabold text-blue-600 bg-white px-3 py-1 rounded-lg border border-slate-200 shadow-2xs">
                {formatCurrency(replanBudgetInr, currency)}
              </span>
            </div>

            <input
              type="range"
              min={40000}
              max={220000}
              step={5000}
              value={replanBudgetInr}
              onChange={(e) => setReplanBudgetInr(Number(e.target.value))}
              className="w-full accent-blue-600"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>{formatCurrency(40000, currency)}</span>
              <span>{formatCurrency(130000, currency)}</span>
              <span>{formatCurrency(220000, currency)}</span>
            </div>

            {/* Quick Budget Presets */}
            <div className="pt-2">
              <span className="text-[11px] font-semibold text-slate-500 block mb-1.5">
                Quick Presets:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { label: "₹45,000 (Low Budget Recheck)", val: 45000 },
                  { label: "₹60,000 (Tight Budget)", val: 60000 },
                  { label: "₹1,15,000 (Reduced)", val: 115000 },
                  { label: "₹1,20,000 (Moderate)", val: 120000 },
                  { label: "₹1,60,000 (Standard)", val: 160000 },
                  { label: "₹2,00,000 (Comfortable)", val: 200000 }
                ].map((preset) => (
                  <button
                    key={preset.val}
                    type="button"
                    onClick={() => setReplanBudgetInr(preset.val)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition ${
                      replanBudgetInr === preset.val
                        ? "bg-blue-600 text-white border-blue-600 shadow-2xs"
                        : "bg-white text-slate-700 border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => onReplan(replanBudgetInr)}
              disabled={loading}
              className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 px-4 rounded-xl text-xs flex items-center justify-center space-x-2 transition disabled:opacity-50 shadow-sm"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Rechecking your plan...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Recheck My Plan</span>
                </>
              )}
            </button>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed max-w-xl">
            If your new budget is too low for the current apartment and movers, NEXMOVE will either suggest alternative homes or invite you to make a choice between budget and commute.
          </p>
        </div>
      )}

      {/* Manual Property Entry Modal */}
      {showManualPropertyModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-200 my-8 animate-fadeIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-5">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Enter Property Details Manually</h3>
                <p className="text-xs text-slate-500">Add a specific apartment in {project.destination_city}</p>
              </div>
              <button
                onClick={() => setShowManualPropertyModal(false)}
                className="w-7 h-7 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleManualPropertySubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Property Name / Title</label>
                <input
                  type="text"
                  required
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.target.value)}
                  placeholder={`e.g. ${manualBhk} BHK Apartment in ${project.destination_city}`}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Neighborhood / Locality</label>
                  <input
                    type="text"
                    required
                    value={manualNeighborhood}
                    onChange={(e) => setManualNeighborhood(e.target.value)}
                    placeholder="e.g. Central City, IT Corridor"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">BHK (Bedrooms)</label>
                  <select
                    value={manualBhk}
                    onChange={(e) => setManualBhk(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  >
                    <option value={1}>1 BHK</option>
                    <option value={2}>2 BHK</option>
                    <option value={3}>3 BHK</option>
                    <option value={4}>4 BHK</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Monthly Rent (₹)</label>
                  <input
                    type="number"
                    required
                    min={1000}
                    step={500}
                    value={manualRent}
                    onChange={(e) => setManualRent(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Security Deposit (₹)</label>
                  <input
                    type="number"
                    required
                    min={0}
                    step={1000}
                    value={manualDeposit}
                    onChange={(e) => setManualDeposit(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Society Maintenance (₹/mo)</label>
                  <input
                    type="number"
                    min={0}
                    value={manualMaintenance}
                    onChange={(e) => setManualMaintenance(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Commute to Office (Mins)</label>
                  <input
                    type="number"
                    min={5}
                    max={120}
                    value={manualCommute}
                    onChange={(e) => setManualCommute(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-1">
                <label className="flex items-center space-x-2 text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={manualPetFriendly}
                    onChange={(e) => setManualPetFriendly(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500 border-slate-300"
                  />
                  <span className="font-semibold">Pet friendly apartment society</span>
                </label>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowManualPropertyModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={manualSubmitting}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition shadow-xs disabled:opacity-50"
                >
                  {manualSubmitting ? "Saving Property..." : "Add & Update Plan"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* OPTIONAL TECHNICAL DETAILS & AGENT LOGS (Hidden by default) */}
      {/* ==================================================================== */}
      <div className="pt-4 border-t border-slate-100">
        <button
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="text-xs text-slate-500 hover:text-slate-800 font-semibold flex items-center space-x-1.5 transition py-2"
        >
          <span>{showTechnicalDetails ? "Hide Advanced Details" : "View Advanced Details & Technical Logs"}</span>
          {showTechnicalDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showTechnicalDetails && (
          <div className="mt-4 p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-4 animate-fadeIn">
            <div>
              <h5 className="font-bold text-slate-900">Technical Logs & Coordination History</h5>
              <p className="text-[11px] text-slate-500">
                Project ID: <span className="font-mono text-slate-700">{project.project_id}</span> • Iteration Count: {project.iteration_count || 1}
              </p>
            </div>

            {logs.length > 0 ? (
              <div className="space-y-2 font-mono text-[11px]">
                {logs.map((log: any, idx: number) => (
                  <div key={idx} className="p-3 bg-white rounded-lg border border-slate-200 space-y-1">
                    <div className="flex justify-between text-slate-700 font-semibold">
                      <span>{log.agent_name}</span>
                      <span className="text-slate-400 text-[10px]">{log.status} (Round {log.iteration})</span>
                    </div>
                    <p className="text-slate-600 font-sans text-xs">{log.notes}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 italic">No raw log entries found.</p>
            )}
          </div>
        )}
      </div>

    </div>
  );
}
