"use client";

import React, { useState, useEffect } from "react";
import { 
  MapPin, 
  Calendar, 
  Check, 
  ArrowRight, 
  ArrowLeft, 
  RefreshCw,
  Sparkles, 
  AlertCircle,
  Briefcase,
  Users
} from "lucide-react";
import { formatCurrency } from "@/lib/currency";

interface WizardFormProps {
  onSuccess: (projectData: any) => void;
  apiBase: string;
  defaultCurrency?: string;
  onCurrencyChange?: (c: string) => void;
}

interface PlaceCity {
  name: string;
  city?: string;
  state?: string;
  lat?: number;
  lon?: number;
}

interface PlaceWorkplace {
  name: string;
  workplace?: string;
  area?: string;
  category?: string;
  city?: string;
}

const getCityName = (c: any): string => {
  if (!c) return "";
  if (typeof c === "string") return c.trim();
  const val = c.city || c.name || "";
  return typeof val === "string" ? val.trim() : "";
};

const getCityState = (c: any): string => {
  if (!c || typeof c === "string") return "";
  return typeof c.state === "string" ? c.state.trim() : "";
};

const getWorkplaceName = (w: any): string => {
  if (!w) return "";
  if (typeof w === "string") return w.trim();
  const val = w.name || w.workplace || "";
  return typeof val === "string" ? val.trim() : "";
};

const getWorkplaceArea = (w: any): string => {
  if (!w || typeof w === "string") return "";
  return typeof w.area === "string" ? w.area.trim() : "";
};

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
  
  // Autocomplete states
  const [originSuggestions, setOriginSuggestions] = useState<PlaceCity[]>([]);
  const [showOriginMenu, setShowOriginMenu] = useState(false);
  const [destSuggestions, setDestSuggestions] = useState<PlaceCity[]>([]);
  const [showDestMenu, setShowDestMenu] = useState(false);

  // Step 2: Home Preferences & Workplace
  const [bhk, setBhk] = useState(2);
  const [householdOccupants, setHouseholdOccupants] = useState(2);
  const [hasPets, setHasPets] = useState(true);
  const [workplace, setWorkplace] = useState("Manyata Tech Park");
  const [commuteMins, setCommuteMins] = useState(40);
  const [workplaceSuggestions, setWorkplaceSuggestions] = useState<PlaceWorkplace[]>([]);
  const [showWorkplaceMenu, setShowWorkplaceMenu] = useState(false);

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

  // Fetch city suggestions for origin
  useEffect(() => {
    const q = (origin || "").trim();
    if (q.length < 1) {
      setOriginSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`${apiBase}/api/places/cities?q=${encodeURIComponent(q)}&limit=6`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setOriginSuggestions(data);
          } else {
            setOriginSuggestions([]);
          }
        }
      } catch {
        setOriginSuggestions([]);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [origin, apiBase]);

  // Fetch city suggestions for destination
  useEffect(() => {
    const q = (destination || "").trim();
    if (q.length < 1) {
      setDestSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`${apiBase}/api/places/cities?q=${encodeURIComponent(q)}&limit=6`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setDestSuggestions(data);
          } else {
            setDestSuggestions([]);
          }
        }
      } catch {
        setDestSuggestions([]);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [destination, apiBase]);

  // Fetch workplace suggestions when destination changes or user types
  useEffect(() => {
    const dest = (destination || "").trim();
    if (!dest) {
      setWorkplaceSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const wpQ = (workplace || "").trim();
        const qParam = wpQ ? `&q=${encodeURIComponent(wpQ)}` : "";
        const res = await fetch(`${apiBase}/api/places/workplaces?city=${encodeURIComponent(dest)}${qParam}&limit=6`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setWorkplaceSuggestions(data);
          } else {
            setWorkplaceSuggestions([]);
          }
        }
      } catch {
        setWorkplaceSuggestions([]);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [destination, workplace, apiBase]);

  // Validation before advancing step
  const handleNext = () => {
    setErrorMessage(null);

    const originClean = (origin || "").trim();
    const destClean = (destination || "").trim();
    const workplaceClean = (workplace || "").trim();

    if (currentStep === 1) {
      if (!originClean) {
        setErrorMessage("Please enter your current departure city.");
        return;
      }
      if (!destClean) {
        setErrorMessage("Please enter your destination city.");
        return;
      }
      if (!moveDate) {
        setErrorMessage("Please select your planned moving date.");
        return;
      }
    }

    if (currentStep === 2) {
      if (!workplaceClean) {
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

  // Submit and create plan
  const handleSubmit = async () => {
    setLoading(true);
    setErrorMessage(null);

    const originClean = (origin || "").trim();
    const destClean = (destination || "").trim();
    const workplaceClean = (workplace || "").trim();

    try {
      // 1. Create Project
      const createRes = await fetch(`${apiBase}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_email: "user@example.com",
          user_name: "Relocation Planner",
          origin_city: originClean,
          destination_city: destClean,
          target_move_date: moveDate,
          upfront_budget_limit_inr: upfrontBudgetInr,
          monthly_budget_limit_inr: monthlyBudgetInr,
          home_bhk: bhk,
          has_pets: hasPets,
          target_workplace: workplaceClean,
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
      setErrorMessage(err.message || "Failed to reach the planning server. Please verify the backend API service is online.");
    } finally {
      setLoading(false);
    }
  };

  const quickCities = ["Bengaluru", "Kolkata", "Pune", "Mumbai", "Hyderabad", "Bhopal", "Delhi"];

  return (
    <div className="bg-white dark:bg-[#182321] rounded-3xl p-6 sm:p-8 border border-[#E4E8E3] dark:border-[#354540] shadow-card max-w-3xl mx-auto transition-colors duration-200">
      
      {/* 4-Step Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between relative">
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-[#E4E8E3] dark:bg-[#354540] -translate-y-1/2 z-0" />
          <div 
            className="absolute top-1/2 left-0 h-0.5 bg-[#0F766E] dark:bg-[#2DD4BF] -translate-y-1/2 z-0 transition-all duration-300"
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
                      ? "bg-[#0F766E] dark:bg-[#2DD4BF] text-white dark:text-[#101918]"
                      : isCurrent
                      ? "bg-white dark:bg-[#182321] text-[#0F766E] dark:text-[#2DD4BF] border-2 border-[#0F766E] dark:border-[#2DD4BF] ring-4 ring-[#E8F3F0] dark:ring-[#203D37]"
                      : "bg-white dark:bg-[#202D2A] text-[#526461] dark:text-[#B6C6C1] border border-[#E4E8E3] dark:border-[#354540]"
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : step.number}
                </div>
                <span className={`text-[11px] font-semibold mt-2 hidden sm:block ${
                  isCurrent ? "text-[#18312F] dark:text-[#F3F7F4]" : isCompleted ? "text-[#526461] dark:text-[#B6C6C1]" : "text-[#526461]/60 dark:text-[#B6C6C1]/50"
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
        <div className="mb-6 p-4 rounded-xl bg-[#FDF2F1] dark:bg-[#7F1D1D]/20 border border-[#F9D1CE] dark:border-[#B42318]/40 text-[#B42318] dark:text-[#FCA5A5] text-xs flex items-center space-x-2 animate-fadeIn" role="alert">
          <AlertCircle className="w-4 h-4 text-[#B42318] dark:text-[#FCA5A5] flex-shrink-0" aria-hidden="true" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* STEP 1: Where are you moving? */}
      {currentStep === 1 && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h3 className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">Step 1: Where are you moving?</h3>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1">
              Search any Indian departure city and destination. Freeform text is supported for all locations.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            
            {/* Origin City with Searchable Autocomplete */}
            <div className="relative">
              <label className="block text-xs font-semibold text-[#18312F] dark:text-[#F3F7F4] mb-1.5">
                Current City (Departure)
              </label>
              <div className="relative">
                <MapPin className="w-4 h-4 text-[#526461] dark:text-[#B6C6C1] absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true" />
                <input
                  type="text"
                  value={origin}
                  onChange={(e) => {
                    setOrigin(e.target.value);
                    setShowOriginMenu(true);
                  }}
                  onFocus={() => setShowOriginMenu(true)}
                  onBlur={() => setTimeout(() => setShowOriginMenu(false), 200)}
                  placeholder="e.g. Pune, Bhopal, Patna, Jaipur..."
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-[#E4E8E3] dark:border-[#354540] text-[#18312F] dark:text-[#F3F7F4] placeholder:text-[#526461]/60 dark:placeholder:text-[#B6C6C1]/40 text-sm focus:outline-none focus:ring-2 focus:ring-[#0F766E] dark:focus:ring-[#2DD4BF] focus:border-transparent bg-white dark:bg-[#202D2A] shadow-2xs"
                />
              </div>

              {/* Origin Autocomplete Menu */}
              {showOriginMenu && originSuggestions.length > 0 && (
                <div className="absolute z-30 left-0 right-0 mt-1 bg-white dark:bg-[#182321] border border-[#E4E8E3] dark:border-[#354540] rounded-xl shadow-card max-h-48 overflow-y-auto">
                  {originSuggestions.map((item, idx) => {
                    const cName = getCityName(item);
                    const sName = getCityState(item);
                    if (!cName) return null;
                    return (
                      <button
                        key={`origin-${cName}-${idx}`}
                        type="button"
                        onMouseDown={() => {
                          setOrigin(cName);
                          setShowOriginMenu(false);
                        }}
                        className="w-full text-left px-3.5 py-2 hover:bg-[#E8F3F0]/60 dark:hover:bg-[#202D2A] flex items-center justify-between text-xs border-b border-[#E4E8E3]/40 dark:border-[#354540]/40 last:border-0"
                      >
                        <span className="font-semibold text-[#18312F] dark:text-[#F3F7F4]">{cName}</span>
                        {sName && <span className="text-[10px] text-[#526461] dark:text-[#B6C6C1]">{sName}</span>}
                      </button>
                    );
                  })}
                </div>
              )}

              <div className="flex flex-wrap gap-1 mt-1.5">
                {["Pune", "Mumbai", "Bhopal", "Bengaluru", "Kolkata"].map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setOrigin(c)}
                    className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border transition ${
                      (origin || "").toLowerCase() === c.toLowerCase()
                        ? "bg-[#0F766E] dark:bg-[#2DD4BF] text-white dark:text-[#101918] border-[#0F766E] dark:border-[#2DD4BF]"
                        : "bg-[#FAF8F3] dark:bg-[#202D2A] text-[#526461] dark:text-[#B6C6C1] border-[#E4E8E3] dark:border-[#354540] hover:border-[#CDE7E2] dark:hover:border-[#5EEAD4]/40 hover:text-[#18312F] dark:hover:text-[#F3F7F4]"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-[#526461] dark:text-[#B6C6C1] mt-1">Where your household items are located</p>
            </div>

            {/* Destination City with Searchable Autocomplete */}
            <div className="relative">
              <label className="block text-xs font-semibold text-[#18312F] dark:text-[#F3F7F4] mb-1.5">
                Destination City (Arrival)
              </label>
              <div className="relative">
                <MapPin className="w-4 h-4 text-[#0F766E] dark:text-[#2DD4BF] absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true" />
                <input
                  type="text"
                  value={destination}
                  onChange={(e) => {
                    setDestination(e.target.value);
                    setShowDestMenu(true);
                  }}
                  onFocus={() => setShowDestMenu(true)}
                  onBlur={() => setTimeout(() => setShowDestMenu(false), 200)}
                  placeholder="e.g. Bengaluru, Kolkata, Mumbai..."
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-[#E4E8E3] dark:border-[#354540] text-[#18312F] dark:text-[#F3F7F4] placeholder:text-[#526461]/60 dark:placeholder:text-[#B6C6C1]/40 text-sm focus:outline-none focus:ring-2 focus:ring-[#0F766E] dark:focus:ring-[#2DD4BF] focus:border-transparent bg-white dark:bg-[#202D2A] shadow-2xs"
                />
              </div>

              {/* Destination Autocomplete Menu */}
              {showDestMenu && destSuggestions.length > 0 && (
                <div className="absolute z-30 left-0 right-0 mt-1 bg-white dark:bg-[#182321] border border-[#E4E8E3] dark:border-[#354540] rounded-xl shadow-card max-h-48 overflow-y-auto">
                  {destSuggestions.map((item, idx) => {
                    const cName = getCityName(item);
                    const sName = getCityState(item);
                    if (!cName) return null;
                    return (
                      <button
                        key={`dest-${cName}-${idx}`}
                        type="button"
                        onMouseDown={() => {
                          setDestination(cName);
                          setShowDestMenu(false);
                          const lower = cName.toLowerCase();
                          if (lower === "kolkata") setWorkplace("Salt Lake Sector V");
                          else if (lower === "bengaluru") setWorkplace("Manyata Tech Park");
                          else if (lower === "pune") setWorkplace("Hinjawadi Rajiv Gandhi Infotech Park (Ph 1, 2, 3)");
                          else if (lower === "mumbai") setWorkplace("Bandra Kurla Complex (BKC)");
                          else if (lower === "hyderabad") setWorkplace("HITEC City (Cyber Towers / Cyber Gateway)");
                          else if (lower === "bhopal") setWorkplace("MP Nagar Commercial Zone");
                          else if (lower === "indore") setWorkplace("Crystal IT Park");
                          else if (lower === "delhi") setWorkplace("Connaught Place (CP)");
                          else if (lower === "gurugram" || lower === "gurgaon") setWorkplace("DLF Cyber City & Cyber Hub");
                          else if (lower === "noida") setWorkplace("Sector 62 IT Corridor");
                          else if (lower === "chennai") setWorkplace("OMR IT Corridor (Tidel Park & Ascendas)");
                          else if (lower === "patna") setWorkplace("Dak Bungalow Crossing");
                          else if (lower === "ahmedabad") setWorkplace("GIFT City (Gujarat International Finance Tec-City)");
                          else if (lower === "jaipur") setWorkplace("Mahindra World City SEZ");
                          else if (lower === "kochi") setWorkplace("Infopark Phase 1 & 2");
                          else setWorkplace(`${cName} Central`);
                        }}
                        className="w-full text-left px-3.5 py-2 hover:bg-[#E8F3F0]/60 dark:hover:bg-[#202D2A] flex items-center justify-between text-xs border-b border-[#E4E8E3]/40 dark:border-[#354540]/40 last:border-0"
                      >
                        <span className="font-semibold text-[#18312F] dark:text-[#F3F7F4]">{cName}</span>
                        {sName && <span className="text-[10px] text-[#526461] dark:text-[#B6C6C1]">{sName}</span>}
                      </button>
                    );
                  })}
                </div>
              )}

              <div className="flex flex-wrap gap-1 mt-1.5">
                {quickCities.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => {
                      setDestination(c);
                      const lower = c.toLowerCase();
                      if (lower === "kolkata") setWorkplace("Salt Lake Sector V");
                      else if (lower === "bengaluru") setWorkplace("Manyata Tech Park");
                      else if (lower === "pune") setWorkplace("Hinjawadi Rajiv Gandhi Infotech Park (Ph 1, 2, 3)");
                      else if (lower === "mumbai") setWorkplace("Bandra Kurla Complex (BKC)");
                      else if (lower === "hyderabad") setWorkplace("HITEC City (Cyber Towers / Cyber Gateway)");
                      else if (lower === "bhopal") setWorkplace("MP Nagar Commercial Zone");
                      else setWorkplace(`${c} Central`);
                    }}
                    className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border transition ${
                      (destination || "").toLowerCase() === c.toLowerCase()
                        ? "bg-[#0F766E] dark:bg-[#2DD4BF] text-white dark:text-[#101918] border-[#0F766E] dark:border-[#2DD4BF]"
                        : "bg-[#FAF8F3] dark:bg-[#202D2A] text-[#526461] dark:text-[#B6C6C1] border-[#E4E8E3] dark:border-[#354540] hover:border-[#CDE7E2] dark:hover:border-[#5EEAD4]/40 hover:text-[#18312F] dark:hover:text-[#F3F7F4]"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-[#526461] dark:text-[#B6C6C1] mt-1">Supports any Indian city (autocomplete or manual entry)</p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#18312F] dark:text-[#F3F7F4] mb-1.5">
              Planned Moving Date
            </label>
            <div className="relative max-w-sm">
              <Calendar className="w-4 h-4 text-[#526461] dark:text-[#B6C6C1] absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true" />
              <input
                type="date"
                value={moveDate}
                onChange={(e) => setMoveDate(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-[#E4E8E3] dark:border-[#354540] text-[#18312F] dark:text-[#F3F7F4] text-sm focus:outline-none focus:ring-2 focus:ring-[#0F766E] dark:focus:ring-[#2DD4BF] focus:border-transparent bg-white dark:bg-[#202D2A] shadow-2xs"
              />
            </div>
            <p className="text-[11px] text-[#526461] dark:text-[#B6C6C1] mt-1">Target delivery and move-in timeline</p>
          </div>
        </div>
      )}

      {/* STEP 2: What home do you need? */}
      {currentStep === 2 && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h3 className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">Step 2: What home do you need?</h3>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1">
              Select apartment size, family pet requirements, and workplace commute location in {destination}.
            </p>
          </div>

          {/* Home Size (BHK) */}
          <div>
            <label className="block text-xs font-semibold text-[#18312F] dark:text-[#F3F7F4] mb-2">
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
                      ? "border-[#0F766E] dark:border-[#2DD4BF] bg-[#E8F3F0] dark:bg-[#203D37] text-[#115E59] dark:text-[#5EEAD4] font-bold shadow-xs"
                      : "border-[#E4E8E3] dark:border-[#354540] hover:border-[#CDE7E2] dark:hover:border-[#5EEAD4]/40 text-[#526461] dark:text-[#B6C6C1] hover:text-[#18312F] dark:hover:text-[#F3F7F4] bg-white dark:bg-[#202D2A]"
                  }`}
                >
                  <span className="block text-base font-extrabold">{num} BHK</span>
                  <span className="text-[10px] text-[#526461] dark:text-[#B6C6C1] block">
                    {num === 1 ? "Studio / 1-Bed" : num === 2 ? "2 Bedrooms" : num === 3 ? "3 Bedrooms" : "4+ Bedrooms"}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            {/* Household Occupants */}
            <div>
              <label className="block text-xs font-semibold text-[#18312F] dark:text-[#F3F7F4] mb-1.5">
                Household Members
              </label>
              <div className="relative">
                <Users className="w-4 h-4 text-[#526461] dark:text-[#B6C6C1] absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true" />
                <select
                  value={householdOccupants}
                  onChange={(e) => setHouseholdOccupants(Number(e.target.value))}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-[#E4E8E3] dark:border-[#354540] text-sm bg-white dark:bg-[#202D2A] text-[#18312F] dark:text-[#F3F7F4] focus:outline-none focus:ring-2 focus:ring-[#0F766E] dark:focus:ring-[#2DD4BF] shadow-2xs"
                >
                  <option value={1} className="bg-white dark:bg-[#202D2A] text-[#18312F] dark:text-[#F3F7F4]">1 person (Solo)</option>
                  <option value={2} className="bg-white dark:bg-[#202D2A] text-[#18312F] dark:text-[#F3F7F4]">2 people (Couple / Roommates)</option>
                  <option value={3} className="bg-white dark:bg-[#202D2A] text-[#18312F] dark:text-[#F3F7F4]">3 people (Small family)</option>
                  <option value={4} className="bg-white dark:bg-[#202D2A] text-[#18312F] dark:text-[#F3F7F4]">4+ people (Family)</option>
                </select>
              </div>
            </div>

            {/* Traveling with Pet */}
            <div className="flex flex-col justify-end">
              <label className="flex items-center space-x-3 p-3 rounded-xl border border-[#E4E8E3] dark:border-[#354540] bg-[#FAF8F3] dark:bg-[#202D2A] cursor-pointer hover:bg-[#E8F3F0]/40 dark:hover:bg-[#203D37]/40 transition">
                <input
                  type="checkbox"
                  checked={hasPets}
                  onChange={(e) => setHasPets(e.target.checked)}
                  className="w-4 h-4 rounded text-[#0F766E] dark:text-[#2DD4BF] focus:ring-[#0F766E] dark:focus:ring-[#2DD4BF] border-[#E4E8E3] dark:border-[#354540] dark:bg-[#182321]"
                />
                <div>
                  <span className="text-xs font-bold text-[#18312F] dark:text-[#F3F7F4] block">Traveling with a Pet</span>
                  <span className="text-[11px] text-[#526461] dark:text-[#B6C6C1] block">Filters only pet-friendly housing societies</span>
                </div>
              </label>
            </div>
          </div>

          {/* Workplace & Commute with Autocomplete suggestions */}
          <div className="pt-2 border-t border-[#E4E8E3] dark:border-[#354540] space-y-4">
            <div className="relative">
              <label className="block text-xs font-semibold text-[#18312F] dark:text-[#F3F7F4] mb-1.5">
                Workplace or Preferred Hub in {destination || "Destination"}
              </label>
              <div className="relative">
                <Briefcase className="w-4 h-4 text-[#526461] dark:text-[#B6C6C1] absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true" />
                <input
                  type="text"
                  value={workplace}
                  onChange={(e) => {
                    setWorkplace(e.target.value);
                    setShowWorkplaceMenu(true);
                  }}
                  onFocus={() => setShowWorkplaceMenu(true)}
                  onBlur={() => setTimeout(() => setShowWorkplaceMenu(false), 200)}
                  placeholder="e.g. Manyata Tech Park, Whitefield, BKC, Salt Lake Sector V"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-[#E4E8E3] dark:border-[#354540] text-[#18312F] dark:text-[#F3F7F4] placeholder:text-[#526461]/60 dark:placeholder:text-[#B6C6C1]/40 text-sm focus:outline-none focus:ring-2 focus:ring-[#0F766E] dark:focus:ring-[#2DD4BF] focus:border-transparent bg-white dark:bg-[#202D2A] shadow-2xs"
                />
              </div>

              {/* Workplace Suggestions Dropdown */}
              {showWorkplaceMenu && workplaceSuggestions.length > 0 && (
                <div className="absolute z-30 left-0 right-0 mt-1 bg-white dark:bg-[#182321] border border-[#E4E8E3] dark:border-[#354540] rounded-xl shadow-card max-h-48 overflow-y-auto">
                  {workplaceSuggestions.map((wp, idx) => {
                    const wName = getWorkplaceName(wp);
                    const wArea = getWorkplaceArea(wp);
                    if (!wName) return null;
                    return (
                      <button
                        key={`wp-${wName}-${idx}`}
                        type="button"
                        onMouseDown={() => {
                          setWorkplace(wName);
                          setShowWorkplaceMenu(false);
                        }}
                        className="w-full text-left px-3.5 py-2 hover:bg-[#E8F3F0]/60 dark:hover:bg-[#202D2A] flex items-center space-x-2 text-xs border-b border-[#E4E8E3]/40 dark:border-[#354540]/40 last:border-0"
                      >
                        <Briefcase className="w-3.5 h-3.5 text-[#0F766E] dark:text-[#2DD4BF] flex-shrink-0" aria-hidden="true" />
                        <div className="flex flex-col">
                          <span className="font-semibold text-[#18312F] dark:text-[#F3F7F4]">{wName}</span>
                          {wArea && <span className="text-[10px] text-[#526461] dark:text-[#B6C6C1]">{wArea}</span>}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Quick suggestion chips */}
              {workplaceSuggestions.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {workplaceSuggestions.slice(0, 3).map((wp, idx) => {
                    const wName = getWorkplaceName(wp);
                    if (!wName) return null;
                    const isSelected = (workplace || "").toLowerCase() === wName.toLowerCase();
                    return (
                      <button
                        key={`wp-chip-${wName}-${idx}`}
                        type="button"
                        onClick={() => setWorkplace(wName)}
                        className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border transition ${
                          isSelected
                            ? "bg-[#0F766E] dark:bg-[#2DD4BF] text-white dark:text-[#101918] border-[#0F766E] dark:border-[#2DD4BF]"
                            : "bg-[#FAF8F3] dark:bg-[#202D2A] text-[#526461] dark:text-[#B6C6C1] border-[#E4E8E3] dark:border-[#354540] hover:border-[#CDE7E2] dark:hover:border-[#5EEAD4]/40 hover:text-[#18312F] dark:hover:text-[#F3F7F4]"
                        }`}
                      >
                        {wName}
                      </button>
                    );
                  })}
                </div>
              )}
              <p className="text-[11px] text-[#526461] dark:text-[#B6C6C1] mt-1">We calculate transit times from housing options to this office hub</p>
            </div>

            <div>
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="font-semibold text-[#18312F] dark:text-[#F3F7F4]">Maximum Desired Commute</span>
                <span className="font-bold text-[#0F766E] dark:text-[#5EEAD4]">{commuteMins} minutes</span>
              </div>
              <input
                type="range"
                min={15}
                max={90}
                step={5}
                value={commuteMins}
                onChange={(e) => setCommuteMins(Number(e.target.value))}
                className="w-full accent-[#0F766E] dark:accent-[#2DD4BF]"
                aria-label="Maximum desired commute in minutes"
              />
              <div className="flex justify-between text-[10px] text-[#526461] dark:text-[#B6C6C1] mt-0.5">
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
            <h3 className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">Step 3: What is your budget?</h3>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1">
              Separate your one-time relocation budget from your ongoing monthly living budget.
            </p>
          </div>

          {/* Upfront Relocation Budget */}
          <div className="p-5 rounded-2xl bg-[#E8F3F0]/60 dark:bg-[#202D2A] border border-[#CDE7E2] dark:border-[#354540] space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <div>
                <span className="text-xs font-bold text-[#115E59] dark:text-[#5EEAD4] block">Upfront Moving Budget</span>
                <span className="text-[11px] text-[#526461] dark:text-[#B6C6C1]">Covers movers, transit insurance, security deposit & advance rent</span>
              </div>
              <div className="text-lg font-black text-[#0F766E] dark:text-[#5EEAD4] bg-white dark:bg-[#182321] px-3 py-1 rounded-xl border border-[#CDE7E2] dark:border-[#354540] w-fit shadow-2xs">
                {formatCurrency(upfrontBudgetInr, currency)}
              </div>
            </div>

            <input
              type="range"
              min={40000}
              max={300000}
              step={5000}
              value={upfrontBudgetInr}
              onChange={(e) => setUpfrontBudgetInr(Number(e.target.value))}
              className="w-full accent-[#0F766E] dark:accent-[#2DD4BF]"
              aria-label="Upfront moving budget"
            />
            <div className="flex justify-between text-[10px] text-[#526461] dark:text-[#B6C6C1]">
              <span>{formatCurrency(40000, currency)} (Budget)</span>
              <span>{formatCurrency(160000, currency)} (Recommended)</span>
              <span>{formatCurrency(300000, currency)} (Premium)</span>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {[
                { label: "₹60k Tight", val: 60000 },
                { label: "₹1.2L Moderate", val: 120000 },
                { label: "₹1.6L Standard", val: 160000 },
                { label: "₹2.2L Generous", val: 220000 },
              ].map((b) => (
                <button
                  key={b.val}
                  type="button"
                  onClick={() => setUpfrontBudgetInr(b.val)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition ${
                    upfrontBudgetInr === b.val
                      ? "bg-[#0F766E] dark:bg-[#2DD4BF] text-white dark:text-[#101918] border-[#0F766E] dark:border-[#2DD4BF]"
                      : "bg-white dark:bg-[#182321] text-[#526461] dark:text-[#B6C6C1] border-[#E4E8E3] dark:border-[#354540] hover:border-[#CDE7E2] dark:hover:border-[#5EEAD4]/40 hover:text-[#18312F] dark:hover:text-[#F3F7F4]"
                  }`}
                >
                  {b.label}
                </button>
              ))}
            </div>
          </div>

          {/* Ongoing Monthly Living Budget */}
          <div className="p-5 rounded-2xl bg-[#FAF8F3] dark:bg-[#202D2A] border border-[#E4E8E3] dark:border-[#354540] space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <div>
                <span className="text-xs font-bold text-[#18312F] dark:text-[#F3F7F4] block">Monthly Living Budget Limit</span>
                <span className="text-[11px] text-[#526461] dark:text-[#B6C6C1]">Includes monthly rent, society maintenance, Wi-Fi & basic utilities</span>
              </div>
              <div className="text-lg font-black text-[#18312F] dark:text-[#F3F7F4] bg-white dark:bg-[#182321] px-3 py-1 rounded-xl border border-[#E4E8E3] dark:border-[#354540] w-fit shadow-2xs">
                {formatCurrency(monthlyBudgetInr, currency)}<span className="text-xs font-normal text-[#526461] dark:text-[#B6C6C1]">/mo</span>
              </div>
            </div>

            <input
              type="range"
              min={15000}
              max={120000}
              step={2500}
              value={monthlyBudgetInr}
              onChange={(e) => setMonthlyBudgetInr(Number(e.target.value))}
              className="w-full accent-[#115E59] dark:accent-[#2DD4BF]"
              aria-label="Monthly living budget limit"
            />
            <div className="flex justify-between text-[10px] text-[#526461] dark:text-[#B6C6C1]">
              <span>{formatCurrency(15000, currency)}</span>
              <span>{formatCurrency(45000, currency)}</span>
              <span>{formatCurrency(120000, currency)}</span>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {[
                { label: "₹25k/mo", val: 25000 },
                { label: "₹35k/mo", val: 35000 },
                { label: "₹45k/mo", val: 45000 },
                { label: "₹65k/mo", val: 65000 },
              ].map((b) => (
                <button
                  key={b.val}
                  type="button"
                  onClick={() => setMonthlyBudgetInr(b.val)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition ${
                    monthlyBudgetInr === b.val
                      ? "bg-[#115E59] dark:bg-[#2DD4BF] text-white dark:text-[#101918] border-[#115E59] dark:border-[#2DD4BF]"
                      : "bg-white dark:bg-[#182321] text-[#526461] dark:text-[#B6C6C1] border-[#E4E8E3] dark:border-[#354540] hover:border-[#CDE7E2] dark:hover:border-[#5EEAD4]/40 hover:text-[#18312F] dark:hover:text-[#F3F7F4]"
                  }`}
                >
                  {b.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* STEP 4: Review Your Details */}
      {currentStep === 4 && (
        <div className="space-y-6 animate-fadeIn">
          <div>
            <h3 className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">Step 4: Review your details</h3>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1">
              Verify your relocation parameters before the multi-agent AI engine generates your plan.
            </p>
          </div>

          <div className="bg-[#FAF8F3] dark:bg-[#202D2A] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] space-y-4 text-xs">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-white dark:bg-[#182321] rounded-xl border border-[#E4E8E3] dark:border-[#354540] shadow-2xs">
                <span className="text-[#526461] dark:text-[#B6C6C1] block text-[10px]">Moving Route</span>
                <span className="font-bold text-[#18312F] dark:text-[#F3F7F4] mt-0.5 block">{origin} → {destination}</span>
              </div>
              <div className="p-3 bg-white dark:bg-[#182321] rounded-xl border border-[#E4E8E3] dark:border-[#354540] shadow-2xs">
                <span className="text-[#526461] dark:text-[#B6C6C1] block text-[10px]">Move Date</span>
                <span className="font-bold text-[#18312F] dark:text-[#F3F7F4] mt-0.5 block">{moveDate}</span>
              </div>
              <div className="p-3 bg-white dark:bg-[#182321] rounded-xl border border-[#E4E8E3] dark:border-[#354540] shadow-2xs">
                <span className="text-[#526461] dark:text-[#B6C6C1] block text-[10px]">Apartment & Pets</span>
                <span className="font-bold text-[#18312F] dark:text-[#F3F7F4] mt-0.5 block">{bhk} BHK • {hasPets ? "With Pet" : "No Pets"}</span>
              </div>
              <div className="p-3 bg-white dark:bg-[#182321] rounded-xl border border-[#E4E8E3] dark:border-[#354540] shadow-2xs">
                <span className="text-[#526461] dark:text-[#B6C6C1] block text-[10px]">Workplace & Commute</span>
                <span className="font-bold text-[#18312F] dark:text-[#F3F7F4] mt-0.5 block">{workplace} (≤{commuteMins}m)</span>
              </div>
            </div>

            <div className="pt-2 border-t border-[#E4E8E3] dark:border-[#354540] flex flex-col sm:flex-row justify-between gap-2">
              <div>
                <span className="text-[#526461] dark:text-[#B6C6C1] text-[11px] block">Upfront Relocation Budget:</span>
                <span className="font-bold text-[#0F766E] dark:text-[#5EEAD4] text-sm">{formatCurrency(upfrontBudgetInr, currency)}</span>
              </div>
              <div>
                <span className="text-[#526461] dark:text-[#B6C6C1] text-[11px] block">Monthly Living Budget:</span>
                <span className="font-bold text-[#18312F] dark:text-[#F3F7F4] text-sm">{formatCurrency(monthlyBudgetInr, currency)}/mo</span>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#E8F3F0] dark:bg-[#203D37]/40 border border-[#CDE7E2] dark:border-[#354540] text-[#115E59] dark:text-[#5EEAD4] text-xs flex items-center space-x-2.5">
            <Sparkles className="w-4 h-4 text-[#0F766E] dark:text-[#2DD4BF] flex-shrink-0" aria-hidden="true" />
            <span>
              Autonomous agents (Housing, Logistics, Budget, Schedule, Decision) will now coordinate verified properties, carrier freight, and milestone roadmaps.
            </span>
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="mt-8 pt-4 border-t border-[#E4E8E3] dark:border-[#354540] flex items-center justify-between">
        {currentStep > 1 ? (
          <button
            type="button"
            onClick={handleBack}
            disabled={loading}
            className="px-4 py-2.5 rounded-xl border border-[#E4E8E3] dark:border-[#354540] hover:bg-[#FAF8F3] dark:hover:bg-[#202D2A] text-xs font-semibold text-[#526461] dark:text-[#B6C6C1] hover:text-[#18312F] dark:hover:text-[#F3F7F4] flex items-center space-x-1.5 transition disabled:opacity-50"
          >
            <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Back</span>
          </button>
        ) : (
          <div />
        )}

        {currentStep < 4 ? (
          <button
            type="button"
            onClick={handleNext}
            className="px-6 py-2.5 rounded-xl bg-[#0F766E] hover:bg-[#115E59] text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-xs"
          >
            <span>Continue</span>
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="px-7 py-3 rounded-xl bg-[#0F766E] hover:bg-[#115E59] text-white text-xs font-bold flex items-center space-x-2 transition shadow-card disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span>Coordinating AI Agents...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" aria-hidden="true" />
                <span>Generate My Moving Plan</span>
              </>
            )}
          </button>
        )}
      </div>

    </div>
  );
}
