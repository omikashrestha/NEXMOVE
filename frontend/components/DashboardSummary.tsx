"use client";

import React from "react";
import { 
  Home, 
  Wallet, 
  Calendar, 
  Truck, 
  CheckCircle2, 
  AlertTriangle,
  ArrowRight,
  Clock,
  MapPin,
  TrendingUp,
  ShieldCheck
} from "lucide-react";
import { formatCurrency, getCurrencyFootnote } from "@/lib/currency";

interface DashboardSummaryProps {
  project: any | null;
  onOpenWizard: () => void;
  currency: string;
}

export default function DashboardSummary({ project, onOpenWizard, currency }: DashboardSummaryProps) {
  // If no project is generated yet, render clean empty-state welcoming cards
  if (!project) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Your Move */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold text-slate-500">Your Move</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <MapPin className="w-4 h-4" />
            </div>
          </div>
          <div className="my-3">
            <div className="text-xl font-bold text-slate-800">No Move Selected</div>
            <p className="text-xs text-slate-400 mt-1">Set your origin, destination, and target date.</p>
          </div>
          <button
            onClick={onOpenWizard}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
          >
            <span>Choose cities</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Card 2: Moving Costs */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold text-slate-500">Money for Moving</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="my-3">
            <div className="text-xl font-bold text-slate-800">—</div>
            <p className="text-xs text-slate-400 mt-1">Movers freight, security deposit, and travel.</p>
          </div>
          <span className="text-xs text-slate-400">Calculated after you plan</span>
        </div>

        {/* Card 3: Monthly Living */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold text-slate-500">Monthly Living Budget</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Home className="w-4 h-4" />
            </div>
          </div>
          <div className="my-3">
            <div className="text-xl font-bold text-slate-800">—</div>
            <p className="text-xs text-slate-400 mt-1">Rent, society fees, and everyday utilities.</p>
          </div>
          <span className="text-xs text-slate-400">Tailored to your preferences</span>
        </div>

        {/* Card 4: Moving Steps */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold text-slate-500">Moving Steps</span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="my-3">
            <div className="text-xl font-bold text-slate-800">4 Guided Steps</div>
            <p className="text-xs text-slate-400 mt-1">Takes less than 2 minutes to plan your move.</p>
          </div>
          <button
            onClick={onOpenWizard}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
          >
            <span>Start moving plan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    );
  }

  // Active Project Data
  const budget = project.budget_audit;
  const upfrontSpent = budget?.total_upfront_outlay_inr || 0;
  const upfrontLimit = project.upfront_budget_limit_inr || 0;
  const upfrontRemaining = upfrontLimit - upfrontSpent;
  const isUpfrontOver = upfrontRemaining < 0;

  const monthlySpent = budget?.recurring_monthly_costs?.total_recurring_monthly_inr || 0;
  const monthlyLimit = project.monthly_budget_limit_inr || 0;
  const monthlyRemaining = monthlyLimit - monthlySpent;
  const isMonthlyOver = monthlyRemaining < 0;

  const currencyNote = getCurrencyFootnote(currency);

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1: Your Active Move */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold text-slate-500">Your Route</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <MapPin className="w-4 h-4" />
            </div>
          </div>
          <div className="my-2">
            <div className="text-lg font-bold text-slate-900 truncate">
              {project.origin_city} → {project.destination_city}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Target Move: <span className="font-semibold text-slate-700">{project.target_move_date}</span>
            </p>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
            <span className="text-slate-500">{project.home_bhk} BHK Home</span>
            <span className="font-medium text-slate-700">{project.has_pets ? "With Pet" : "No Pets"}</span>
          </div>
        </div>

        {/* Card 2: Money Available for Moving */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold text-slate-500">Moving & Deposit Cost</span>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isUpfrontOver ? "bg-rose-50 text-rose-600" : "bg-emerald-50 text-emerald-600"
            }`}>
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="my-2">
            <div className="text-xl font-bold text-slate-900">
              {formatCurrency(upfrontSpent, currency)}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Budget: {formatCurrency(upfrontLimit, currency)}
            </p>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
            <span className="text-slate-500">Balance:</span>
            <span className={`font-semibold ${isUpfrontOver ? "text-rose-600" : "text-emerald-600"}`}>
              {isUpfrontOver
                ? `${formatCurrency(Math.abs(upfrontRemaining), currency)} over budget`
                : `${formatCurrency(upfrontRemaining, currency)} saved`}
            </span>
          </div>
        </div>

        {/* Card 3: Monthly Living Budget */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold text-slate-500">Monthly Rent & Living</span>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isMonthlyOver ? "bg-rose-50 text-rose-600" : "bg-blue-50 text-blue-600"
            }`}>
              <Home className="w-4 h-4" />
            </div>
          </div>
          <div className="my-2">
            <div className="text-xl font-bold text-slate-900">
              {formatCurrency(monthlySpent, currency)}
              <span className="text-xs font-normal text-slate-400">/mo</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Budget limit: {formatCurrency(monthlyLimit, currency)}/mo
            </p>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
            <span className="text-slate-500">Monthly room:</span>
            <span className={`font-semibold ${isMonthlyOver ? "text-rose-600" : "text-emerald-600"}`}>
              {isMonthlyOver
                ? `${formatCurrency(Math.abs(monthlyRemaining), currency)} over`
                : `${formatCurrency(monthlyRemaining, currency)} buffer`}
            </span>
          </div>
        </div>

        {/* Card 4: Moving Plan Status */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold text-slate-500">Plan Agreement</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="my-2">
            <div className="text-lg font-bold text-slate-900">
              {project.status === "CONSENSUS_REACHED" || project.status === "APPROVED" 
                ? "Plan Agreed" 
                : project.status === "AWAITING_USER_DECISION" 
                ? "Your Choice Needed"
                : project.status === "NO_HOUSING_AVAILABLE"
                ? "No Properties Found"
                : "Plan Created"}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {project.status === "AWAITING_USER_DECISION"
                ? "Select a compromise option below"
                : project.status === "NO_HOUSING_AVAILABLE"
                ? "No listings match criteria in destination"
                : "Home, budget, and movers aligned"}
            </p>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
            <span className="text-slate-500">Recommended Home:</span>
            <span className="font-semibold text-slate-800 truncate max-w-[120px]">
              {project.housing_proposal?.neighborhood || (project.status === "NO_HOUSING_AVAILABLE" ? "None Available" : "Selected")}
            </span>
          </div>
        </div>

      </div>

      {currencyNote && (
        <p className="text-[11px] text-slate-400 italic text-right px-1">
          *{currencyNote}
        </p>
      )}
    </div>
  );
}
