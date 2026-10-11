"use client";

import React, { useState } from "react";
import { 
  Building2, 
  MapPin, 
  Wallet, 
  Calendar, 
  FileText, 
  HelpCircle,
  ArrowRight, 
  CheckCircle2,
  Menu,
  X,
  Globe
} from "lucide-react";
import { CURRENCY_OPTIONS } from "@/lib/currency";

interface NavbarProps {
  onPlanClick: () => void;
  onNavigateSection: (sectionId: string) => void;
  currency: string;
  onCurrencyChange: (newCurrency: string) => void;
  hasActiveProject?: boolean;
}

export default function Navbar({
  onPlanClick,
  onNavigateSection,
  currency,
  onCurrencyChange,
  hasActiveProject = false
}: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { id: "overview", label: "Overview" },
    ...(hasActiveProject
      ? [
          { id: "home-options", label: "Home Options" },
          { id: "budget-costs", label: "Budget & Costs" },
          { id: "moving-timeline", label: "Moving Timeline" },
          { id: "lease-review", label: "Lease Review" },
        ]
      : []),
    { id: "how-it-works", label: "How It Works" },
  ];

  const handleLinkClick = (id: string) => {
    onNavigateSection(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="border-b border-slate-200/70 bg-white/95 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Name */}
        <div 
          className="flex items-center space-x-3 cursor-pointer group"
          onClick={() => handleLinkClick("top")}
        >
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-black text-lg shadow-sm group-hover:bg-blue-700 transition">
            NM
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-slate-900">NEXMOVE</span>
              <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                Relocation Assistant
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block">Your next move, made simple.</p>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center space-x-1 text-sm font-medium text-slate-600">
          {navLinks.map((link) => (
            <button
              key={link.id}
              onClick={() => handleLinkClick(link.id)}
              className="px-3 py-1.5 rounded-lg hover:text-slate-900 hover:bg-slate-100/80 transition"
            >
              {link.label}
            </button>
          ))}
        </nav>

        {/* Right Controls: Currency Selector, Status, and CTA */}
        <div className="hidden sm:flex items-center space-x-3">
          
          {/* Currency Dropdown */}
          <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs">
            <Globe className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={currency}
              onChange={(e) => onCurrencyChange(e.target.value)}
              className="bg-transparent text-slate-700 font-medium focus:outline-none cursor-pointer pr-1"
              aria-label="Select display currency"
            >
              {CURRENCY_OPTIONS.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} ({c.symbol}) — {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Simple Friendly System Status */}
          <div className="flex items-center space-x-1.5 text-xs text-slate-600 px-2 py-1 bg-slate-50 rounded-lg border border-slate-100">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="font-medium">Ready to plan</span>
          </div>

          {/* Primary Action Button */}
          <button
            onClick={onPlanClick}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs px-4 py-2 rounded-xl flex items-center space-x-1.5 shadow-sm hover:shadow transition"
          >
            <span>{hasActiveProject ? "Plan Another Move" : "Plan My Move"}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Mobile Hamburger Toggle */}
        <div className="flex items-center space-x-2 sm:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="sm:hidden border-t border-slate-200 bg-white px-4 py-4 space-y-3 shadow-lg animate-fadeIn">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <span className="text-xs text-slate-500 font-medium">Display Currency:</span>
            <select
              value={currency}
              onChange={(e) => onCurrencyChange(e.target.value)}
              className="text-xs font-semibold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-md"
            >
              {CURRENCY_OPTIONS.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} ({c.symbol})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            {navLinks.map((link) => (
              <button
                key={link.id}
                onClick={() => handleLinkClick(link.id)}
                className="w-full text-left px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-lg"
              >
                {link.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              onPlanClick();
              setMobileMenuOpen(false);
            }}
            className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm py-2.5 rounded-xl flex items-center justify-center space-x-2 shadow-sm"
          >
            <span>Plan My Move</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </header>
  );
}
