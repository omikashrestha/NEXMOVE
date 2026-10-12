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
  ShieldCheck,
  Compass
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
        <div className="bg-white dark:bg-[#182321] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] shadow-xs flex flex-col justify-between transition-colors">
          <div className="flex items-center justify-between text-[#526461] dark:text-[#B6C6C1]">
            <span className="text-xs font-semibold text-[#526461] dark:text-[#B6C6C1]">Your Route</span>
            <div className="w-8 h-8 rounded-lg bg-[#E8F3F0] dark:bg-[#203D37] text-[#0F766E] dark:text-[#5EEAD4] flex items-center justify-center">
              <MapPin className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div className="my-3">
            <div className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">Choose Cities</div>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1">Set your origin, destination, and target date.</p>
          </div>
          <button
            onClick={onOpenWizard}
            className="text-xs font-semibold text-[#0F766E] dark:text-[#5EEAD4] hover:text-[#115E59] dark:hover:text-[#2DD4BF] flex items-center space-x-1 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F766E] dark:focus-visible:ring-[#5EEAD4] rounded-md px-1 py-0.5"
          >
            <span>Configure route</span>
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>

        {/* Card 2: Moving Costs */}
        <div className="bg-white dark:bg-[#182321] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] shadow-xs flex flex-col justify-between transition-colors">
          <div className="flex items-center justify-between text-[#526461] dark:text-[#B6C6C1]">
            <span className="text-xs font-semibold text-[#526461] dark:text-[#B6C6C1]">Moving & Deposit Outlay</span>
            <div className="w-8 h-8 rounded-lg bg-[#E8F3F0] dark:bg-[#203D37] text-[#0F766E] dark:text-[#5EEAD4] flex items-center justify-center">
              <Wallet className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div className="my-3">
            <div className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">—</div>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1">Movers freight, security deposit, and move-in fees.</p>
          </div>
          <span className="text-xs text-[#526461]/80 dark:text-[#B6C6C1]/80">Calculated after you plan</span>
        </div>

        {/* Card 3: Monthly Living */}
        <div className="bg-white dark:bg-[#182321] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] shadow-xs flex flex-col justify-between transition-colors">
          <div className="flex items-center justify-between text-[#526461] dark:text-[#B6C6C1]">
            <span className="text-xs font-semibold text-[#526461] dark:text-[#B6C6C1]">Monthly Living Budget</span>
            <div className="w-8 h-8 rounded-lg bg-[#E8F3F0] dark:bg-[#203D37] text-[#0F766E] dark:text-[#5EEAD4] flex items-center justify-center">
              <Home className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div className="my-3">
            <div className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">—</div>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1">Rent, society fees, and everyday utilities.</p>
          </div>
          <span className="text-xs text-[#526461]/80 dark:text-[#B6C6C1]/80">Tailored to your preferences</span>
        </div>

        {/* Card 4: Moving Steps */}
        <div className="bg-white dark:bg-[#182321] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] shadow-xs flex flex-col justify-between transition-colors">
          <div className="flex items-center justify-between text-[#526461] dark:text-[#B6C6C1]">
            <span className="text-xs font-semibold text-[#526461] dark:text-[#B6C6C1]">Guided Setup</span>
            <div className="w-8 h-8 rounded-lg bg-[#E8F3F0] dark:bg-[#203D37] text-[#0F766E] dark:text-[#5EEAD4] flex items-center justify-center">
              <Calendar className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div className="my-3">
            <div className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">4 Simple Steps</div>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1">Takes less than 2 minutes to plan your move.</p>
          </div>
          <button
            onClick={onOpenWizard}
            className="text-xs font-semibold text-[#0F766E] dark:text-[#5EEAD4] hover:text-[#115E59] dark:hover:text-[#2DD4BF] flex items-center space-x-1 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F766E] dark:focus-visible:ring-[#5EEAD4] rounded-md px-1 py-0.5"
          >
            <span>Start relocation plan</span>
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
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
        <div className="bg-white dark:bg-[#182321] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] shadow-xs flex flex-col justify-between transition-colors">
          <div className="flex items-center justify-between text-[#526461] dark:text-[#B6C6C1]">
            <span className="text-xs font-semibold text-[#526461] dark:text-[#B6C6C1]">Your Route</span>
            <div className="w-8 h-8 rounded-lg bg-[#E8F3F0] dark:bg-[#203D37] text-[#0F766E] dark:text-[#5EEAD4] flex items-center justify-center">
              <MapPin className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div className="my-2">
            <div className="text-lg font-bold text-[#18312F] dark:text-[#F3F7F4] truncate">
              {project.origin_city} → {project.destination_city}
            </div>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-0.5">
              Target Move: <span className="font-semibold text-[#18312F] dark:text-[#F3F7F4]">{project.target_move_date}</span>
            </p>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-[#E4E8E3] dark:border-[#354540]">
            <span className="text-[#526461] dark:text-[#B6C6C1]">{project.home_bhk} BHK Home</span>
            <span className="font-medium text-[#18312F] dark:text-[#F3F7F4]">{project.has_pets ? "With Pet" : "No Pets"}</span>
          </div>
        </div>

        {/* Card 2: Money Available for Moving */}
        <div className="bg-white dark:bg-[#182321] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] shadow-xs flex flex-col justify-between transition-colors">
          <div className="flex items-center justify-between text-[#526461] dark:text-[#B6C6C1]">
            <span className="text-xs font-semibold text-[#526461] dark:text-[#B6C6C1]">Moving & Deposit Cost</span>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isUpfrontOver 
                ? "bg-[#FDF2F1] dark:bg-[#3D1414] text-[#B42318] dark:text-[#F87171]" 
                : "bg-[#E8F3F0] dark:bg-[#203D37] text-[#0F766E] dark:text-[#5EEAD4]"
            }`}>
              <Wallet className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div className="my-2">
            <div className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">
              {formatCurrency(upfrontSpent, currency)}
            </div>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-0.5">
              Budget: {formatCurrency(upfrontLimit, currency)}
            </p>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-[#E4E8E3] dark:border-[#354540]">
            <span className="text-[#526461] dark:text-[#B6C6C1]">Balance:</span>
            <span className={`font-semibold ${
              isUpfrontOver ? "text-[#B42318] dark:text-[#F87171]" : "text-[#237A57] dark:text-[#5EEAD4]"
            }`}>
              {isUpfrontOver
                ? `${formatCurrency(Math.abs(upfrontRemaining), currency)} over budget`
                : `${formatCurrency(upfrontRemaining, currency)} saved`}
            </span>
          </div>
        </div>

        {/* Card 3: Monthly Living Budget */}
        <div className="bg-white dark:bg-[#182321] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] shadow-xs flex flex-col justify-between transition-colors">
          <div className="flex items-center justify-between text-[#526461] dark:text-[#B6C6C1]">
            <span className="text-xs font-semibold text-[#526461] dark:text-[#B6C6C1]">Monthly Rent & Living</span>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isMonthlyOver 
                ? "bg-[#FDF2F1] dark:bg-[#3D1414] text-[#B42318] dark:text-[#F87171]" 
                : "bg-[#E8F3F0] dark:bg-[#203D37] text-[#0F766E] dark:text-[#5EEAD4]"
            }`}>
              <Home className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div className="my-2">
            <div className="text-xl font-bold text-[#18312F] dark:text-[#F3F7F4]">
              {formatCurrency(monthlySpent, currency)}
              <span className="text-xs font-normal text-[#526461] dark:text-[#B6C6C1]">/mo</span>
            </div>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-0.5">
              Budget limit: {formatCurrency(monthlyLimit, currency)}/mo
            </p>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-[#E4E8E3] dark:border-[#354540]">
            <span className="text-[#526461] dark:text-[#B6C6C1]">Monthly room:</span>
            <span className={`font-semibold ${
              isMonthlyOver ? "text-[#B42318] dark:text-[#F87171]" : "text-[#237A57] dark:text-[#5EEAD4]"
            }`}>
              {isMonthlyOver
                ? `${formatCurrency(Math.abs(monthlyRemaining), currency)} over`
                : `${formatCurrency(monthlyRemaining, currency)} buffer`}
            </span>
          </div>
        </div>

        {/* Card 4: Moving Plan Status */}
        <div className="bg-white dark:bg-[#182321] rounded-2xl p-5 border border-[#E4E8E3] dark:border-[#354540] shadow-xs flex flex-col justify-between transition-colors">
          <div className="flex items-center justify-between text-[#526461] dark:text-[#B6C6C1]">
            <span className="text-xs font-semibold text-[#526461] dark:text-[#B6C6C1]">Plan Agreement</span>
            <div className="w-8 h-8 rounded-lg bg-[#E8F3F0] dark:bg-[#203D37] text-[#237A57] dark:text-[#5EEAD4] flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div className="my-2">
            <div className="text-lg font-bold text-[#18312F] dark:text-[#F3F7F4]">
              {project.status === "CONSENSUS_REACHED" || project.status === "APPROVED" 
                ? "Plan Agreed" 
                : project.status === "AWAITING_USER_DECISION" 
                ? "Your Choice Needed"
                : project.status === "NO_HOUSING_AVAILABLE"
                ? "No Properties Found"
                : "Plan Created"}
            </div>
            <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-0.5">
              {project.status === "AWAITING_USER_DECISION"
                ? "Select a compromise option below"
                : project.status === "NO_HOUSING_AVAILABLE"
                ? "No listings match criteria in destination"
                : "Home, budget, and movers aligned"}
            </p>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-[#E4E8E3] dark:border-[#354540]">
            <span className="text-[#526461] dark:text-[#B6C6C1]">Recommended Home:</span>
            <span className="font-semibold text-[#18312F] dark:text-[#F3F7F4] truncate max-w-[120px]">
              {project.housing_proposal?.neighborhood || (project.status === "NO_HOUSING_AVAILABLE" ? "None Available" : "Selected")}
            </span>
          </div>
        </div>

      </div>

      {currencyNote && (
        <p className="text-[11px] text-[#526461] dark:text-[#B6C6C1] italic text-right px-1">
          *{currencyNote}
        </p>
      )}
    </div>
  );
}
