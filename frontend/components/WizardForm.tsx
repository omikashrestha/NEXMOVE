"use client";

import React, { useState } from "react";
import { 
  Building2, 
  MapPin, 
  Calendar, 
  Wallet, 
  Check, 
  ArrowRight, 
  ArrowLeft, 
  RefreshCw,
  Sparkles,
  Info,
  CheckCircle2,
  AlertCircle,
  Globe,
  Home,
  Briefcase,
  Users
} from "lucide-react";
import { formatCurrency, CURRENCY_OPTIONS, convertToInr } from "@/lib/currency";

interface WizardFormProps {
  onSuccess: (projectData: any) => void;
  apiBase: string;
  defaultCurrency?: string;
  onCurrencyChange?: (c: string) => void;
}

export default function WizardForm({
  onSuccess,
  apiBase,
  defaultCurrency = "INR",
  onCurrencyChange
}: WizardFormProps) {
  // Step State (1 to 4)
  const [currentStep, setCurrentStep] = useState(1);

  // Form Fields State with realistic friendly defaults
  const [origin, setOrigin] = useState("Pune");
  const [destination, setDestination] = useState("Bengaluru");
  const [moveDate, setMoveDate] = useState("2026-11-15");
  
  // Step 2: Home Preferences
  const [bhk, setBhk] = useState(2);
  const [householdOccupants, setHouseholdOccupants] = useState(2);
  const [hasPets, setHasPets] = useState(true);
  const [workplace, setWorkplace] = useState("Manyata Tech Park");
  const [commuteMins, setCommuteMins] = useState(40);

  // Step 3: Budget
  const [currency, setCurrency] = useState(defaultCurrency);
  const [upfrontBudgetInr, setUpfrontBudgetInr] = useState(160000);
  const [monthlyBudgetInr, setMonthlyBudgetInr] = useState(45000);

  // Submission State
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const steps = [
    { number: 1, title: "Where are you moving?", short: "Cities & Date" },
    { number: 2, title: "What home do you need?", short: "Home & Work" },
    { number: 3, title: "What is your budget?", short: "Moving Budget" },
    { number: 4, title: "Review your details", short: "Summary" },
  ];

  // Validation before advancing step
  const handleNext = () => {
    setErrorMessage(null);

    if (currentStep === 1) {
      if (!origin.trim()) {
        setErrorMessage("Please enter your current departure city.");
        return;
      }
      if (!destination.trim()) {
        setErrorMessage("Please enter your destination city.");
        return;
      }
      if (!moveDate) {
        setErrorMessage("Please select your planned moving date.");
        return;
      }
    }

    if (currentStep === 2) {
      if (!workplace.trim()) {
        setErrorMessage("Please enter your target workplace or preferred area.");
        return;
      }
    }

    if (currentStep === 3) {
      if (upfrontBudgetInr <= 0) {
        setErrorMessage("Please enter a valid upfront moving budget.");
        return;
      }
      if (monthlyBudgetInr <= 0) {
        setErrorMessage("Please enter a valid monthly living budget.");
        return;
      }
    }

    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    setErrorMessage(null);
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCurrencySelect = (newCurr: string) => {
    setCurrency(newCurr);
    if (onCurrencyChange) onCurrencyChange(newCurr);
  };

  // Submit and create plan
  const handleSubmit = async () => {
    setLoading(true);
    setErrorMessage(null);

    try {
      // 1. Create Project
      const createRes = await fetch(`${apiBase}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_email: "user@example.com",
          user_name: "Relocation Planner",
          origin_city: origin.trim(),
          destination_city: destination.trim(),
          target_move_date: moveDate,
          upfront_budget_limit_inr: upfrontBudgetInr,
          monthly_budget_limit_inr: monthlyBudgetInr,
          home_bhk: bhk,
          has_pets: hasPets,
          target_workplace: workplace.trim(),
          max_commute_mins: commuteMins,
        }),
      });

      if (!createRes.ok) {
        const errorData = await createRes.json().catch(() => ({}));
        throw new Error(errorData.detail || "Unable to save moving project details. Please check connection.");
      }

      const summary = await createRes.json();

      // 2. Run Autonomous Planning
      const runRes = await fetch(`${apiBase}/api/projects/${summary.project_id}/run`, {
        method: "POST",
      });

      if (!runRes.ok) {
        const runError = await runRes.json().catch(() => ({}));
        throw new Error(runError.detail || "Planning engine encountered an issue while coordinating results.");
      }

      const fullProject = await runRes.json();
      onSuccess(fullProject);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to reach the planning server. Please verify backend is running on :8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm max-w-3xl mx-auto">
      
      {/* 4-Step Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between relative">
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-100 -translate-y-1/2 z-0" />
          <div 
            className="absolute top-1/2 left-0 h-0.5 bg-blue-600 -translate-y-1/2 z-0 transition-all duration-300"
            style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
          />

          {steps.map((step) => {
            const isCompleted = currentStep > step.number;
            const isCurrent = currentStep === step.number;

            return (
              <div 
                key={step.number} 
                className="relative z-10 flex flex-col items-center cursor-pointer"
                onClick={() => {
                  if (step.number < currentStep) setCurrentStep(step.number);
                }}
              >
                <div 
                  className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition shadow-xs ${
                    isCompleted
                      ? "bg-blue-600 text-white"
                      : isCurrent
                      ? "bg-white text-blue-600 border-2 border-blue-600 ring-4 ring-blue-50"
                      : "bg-white text-slate-400 border border-slate-200"
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : step.number}
                </div>
                <span className={`text-[11px] font-semibold mt-2 hidden sm:block ${
                  isCurrent ? "text-slate-900" : isCompleted ? "text-slate-600" : "text-slate-400"
                }`}>
                  {step.short}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Error alert if validation failed */}
      {errorMessage && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2 animate-fadeIn">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* STEP 1: Where are you moving? */}
      {currentStep === 1 && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h3 className="text-xl font-bold text-slate-900">Step 1: Where are you moving?</h3>
            <p className="text-xs text-slate-500 mt-1">
              Tell us your starting city, new destination, and when you plan to arrive.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Current City (Departure)
              </label>
              <div className="relative">
                <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  placeholder="e.g. Pune"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-1.5 mt-1.5">
                {["Pune", "Mumbai", "Bengaluru", "Kolkata"].map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setOrigin(c)}
                    className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border transition ${
                      origin.toLowerCase() === c.toLowerCase()
                        ? "bg-slate-800 text-white border-slate-800"
                        : "bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Where your household items are located</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Destination City (Arrival)
              </label>
              <div className="relative">
                <MapPin className="w-4 h-4 text-blue-600 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="e.g. Bengaluru"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-1.5 mt-1.5">
                {["Bengaluru", "Kolkata", "Pune"].map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => {
                      setDestination(c);
                      if (c === "Kolkata" && workplace === "Manyata Tech Park") {
                        setWorkplace("Salt Lake Sector V");
                      } else if (c === "Bengaluru" && workplace === "Salt Lake Sector V") {
                        setWorkplace("Manyata Tech Park");
                      }
                    }}
                    className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border transition ${
                      destination.toLowerCase() === c.toLowerCase()
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Where you are searching for a new home</p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Planned Moving Date
            </label>
            <div className="relative max-w-sm">
              <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="date"
                value={moveDate}
                onChange={(e) => setMoveDate(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Target delivery and move-in timeline</p>
          </div>
        </div>
      )}

      {/* STEP 2: What home do you need? */}
      {currentStep === 2 && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h3 className="text-xl font-bold text-slate-900">Step 2: What home do you need?</h3>
            <p className="text-xs text-slate-500 mt-1">
              Select apartment size, family pet requirements, and workplace commute location.
            </p>
          </div>

          {/* Home Size (BHK) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-2">
              Apartment Size (Bedrooms)
            </label>
            <div className="grid grid-cols-4 gap-3">
              {[1, 2, 3, 4].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setBhk(num)}
                  className={`py-3 rounded-xl border text-center transition ${
                    bhk === num
                      ? "border-blue-600 bg-blue-50 text-blue-700 font-bold shadow-xs"
                      : "border-slate-200 hover:border-slate-300 text-slate-700"
                  }`}
                >
                  <span className="block text-base font-extrabold">{num} BHK</span>
                  <span className="text-[10px] text-slate-500 block">
                    {num === 1 ? "Studio / 1-Bed" : num === 2 ? "2 Bedrooms" : num === 3 ? "3 Bedrooms" : "4+ Bedrooms"}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            {/* Household Occupants */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Household Members
              </label>
              <div className="relative">
                <Users className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <select
                  value={householdOccupants}
                  onChange={(e) => setHouseholdOccupants(Number(e.target.value))}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1}>1 person (Solo)</option>
                  <option value={2}>2 people (Couple / Roommates)</option>
                  <option value={3}>3 people (Small family)</option>
                  <option value={4}>4+ people (Family)</option>
                </select>
              </div>
            </div>

            {/* Traveling with Pet */}
            <div className="flex flex-col justify-end">
              <label className="flex items-center space-x-3 p-3 rounded-xl border border-slate-200 bg-slate-50/60 cursor-pointer hover:bg-slate-50 transition">
                <input
                  type="checkbox"
                  checked={hasPets}
                  onChange={(e) => setHasPets(e.target.checked)}
                  className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300"
                />
                <div>
                  <span className="text-xs font-bold text-slate-800 block">Traveling with a Pet</span>
                  <span className="text-[11px] text-slate-500 block">Filters only pet-friendly housing societies</span>
                </div>
              </label>
            </div>
          </div>

          {/* Workplace & Commute */}
          <div className="pt-2 border-t border-slate-100 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Workplace or Preferred Hub in {destination || "Destination"}
              </label>
              <div className="relative">
                <Briefcase className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={workplace}
                  onChange={(e) => setWorkplace(e.target.value)}
                  placeholder="e.g. Manyata Tech Park, Whitefield, Cyber City"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">We prioritize housing within easy reach of this office</p>
            </div>

            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="font-semibold text-slate-700">Maximum Desired Commute</span>
                <span className="font-bold text-blue-600">{commuteMins} minutes</span>
              </div>
              <input
                type="range"
                min={15}
                max={90}
                step={5}
                value={commuteMins}
                onChange={(e) => setCommuteMins(Number(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                <span>15 mins (Walk/Short drive)</span>
                <span>45 mins (Balanced)</span>
                <span>90 mins (Wide radius)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: What is your budget? */}
      {currentStep === 3 && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h3 className="text-xl font-bold text-slate-900">Step 3: What is your budget?</h3>
            <p className="text-xs text-slate-500 mt-1">
              Separate your one-time moving costs from your recurring monthly living budget.
            </p>
          </div>

          {/* Currency Preference Selector */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4 text-slate-500" />
              <div>
                <span className="font-bold text-slate-800 block">Preferred Currency</span>
                <span className="text-[11px] text-slate-500">Estimates will display in this currency</span>
              </div>
            </div>

            <select
              value={currency}
              onChange={(e) => handleCurrencySelect(e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {CURRENCY_OPTIONS.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} ({c.symbol}) — {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Upfront Moving Budget (One-time) */}
          <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50/50 space-y-3">
            <div className="flex justify-between items-start">
              <div>
                <label className="text-xs font-bold text-slate-800 block">
                  Money Available for Moving (Upfront)
                </label>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Covers movers truck, security deposit, packing, and travel.
                </p>
              </div>
              <span className="text-base font-extrabold text-blue-600 bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
                {formatCurrency(upfrontBudgetInr, currency)}
              </span>
            </div>

            <input
              type="range"
              min={40000}
              max={250000}
              step={5000}
              value={upfrontBudgetInr}
              onChange={(e) => setUpfrontBudgetInr(Number(e.target.value))}
              className="w-full accent-blue-600"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>{formatCurrency(40000, currency)}</span>
              <span>{formatCurrency(150000, currency)}</span>
              <span>{formatCurrency(250000, currency)}</span>
            </div>
          </div>

          {/* Monthly Living Budget */}
          <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50/50 space-y-3">
            <div className="flex justify-between items-start">
              <div>
                <label className="text-xs font-bold text-slate-800 block">
                  Monthly Living Budget
                </label>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Covers monthly house rent, society maintenance, and utilities.
                </p>
              </div>
              <span className="text-base font-extrabold text-emerald-600 bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
                {formatCurrency(monthlyBudgetInr, currency)}/mo
              </span>
            </div>

            <input
              type="range"
              min={20000}
              max={80000}
              step={2500}
              value={monthlyBudgetInr}
              onChange={(e) => setMonthlyBudgetInr(Number(e.target.value))}
              className="w-full accent-emerald-600"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>{formatCurrency(20000, currency)}/mo</span>
              <span>{formatCurrency(45000, currency)}/mo</span>
              <span>{formatCurrency(80000, currency)}/mo</span>
            </div>
          </div>
        </div>
      )}

      {/* STEP 4: Review your details */}
      {currentStep === 4 && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h3 className="text-xl font-bold text-slate-900">Step 4: Review your details</h3>
            <p className="text-xs text-slate-500 mt-1">
              Verify your relocation preferences before we create your moving plan.
            </p>
          </div>

          <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200/80 space-y-4 text-xs">
            {/* Row 1: Route */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <span className="text-slate-400 block text-[11px]">Route & Move Date</span>
                <span className="text-sm font-bold text-slate-900">
                  {origin} → {destination}
                </span>
                <span className="text-slate-500 block text-[11px] mt-0.5">{moveDate}</span>
              </div>
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="text-xs font-semibold text-blue-600 hover:underline"
              >
                Edit
              </button>
            </div>

            {/* Row 2: Home Preferences */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <span className="text-slate-400 block text-[11px]">Home Preferences</span>
                <span className="font-bold text-slate-900">
                  {bhk} BHK Apartment • {hasPets ? "Pet Friendly" : "No Pets"}
                </span>
                <span className="text-slate-500 block text-[11px] mt-0.5">
                  Near {workplace} (≤ {commuteMins} mins commute)
                </span>
              </div>
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="text-xs font-semibold text-blue-600 hover:underline"
              >
                Edit
              </button>
            </div>

            {/* Row 3: Budget Allocations */}
            <div className="flex items-center justify-between">
              <div>
                <span className="text-slate-400 block text-[11px]">Budget Caps ({currency})</span>
                <span className="font-bold text-slate-900">
                  Upfront Moving: {formatCurrency(upfrontBudgetInr, currency)}
                </span>
                <span className="text-emerald-700 block font-semibold text-[11px] mt-0.5">
                  Monthly Living: {formatCurrency(monthlyBudgetInr, currency)}/mo
                </span>
              </div>
              <button
                type="button"
                onClick={() => setCurrentStep(3)}
                className="text-xs font-semibold text-blue-600 hover:underline"
              >
                Edit
              </button>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-800 flex items-start space-x-2">
            <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
            <p>
              When you click <strong>Create My Moving Plan</strong>, our assistants will search housing options, calculate truck freight tariffs, audit budgets, and organize your move date into a single timeline.
            </p>
          </div>
        </div>
      )}

      {/* Navigation Buttons: Previous & Continue / Create Plan */}
      <div className="mt-8 pt-4 border-t border-slate-100 flex items-center justify-between">
        {currentStep > 1 ? (
          <button
            type="button"
            onClick={handleBack}
            disabled={loading}
            className="px-4 py-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 text-xs font-semibold flex items-center space-x-1 transition disabled:opacity-50"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Previous</span>
          </button>
        ) : (
          <div />
        )}

        {currentStep < 4 ? (
          <button
            type="button"
            onClick={handleNext}
            className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-sm transition"
          >
            <span>Continue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="px-7 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold flex items-center space-x-2 shadow-md hover:shadow-lg transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Creating Your Moving Plan...</span>
              </>
            ) : (
              <>
                <span>Create My Moving Plan</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        )}
      </div>

    </div>
  );
}
