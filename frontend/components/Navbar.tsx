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
  Globe,
  Sun,
  Moon,
  Sparkles
} from "lucide-react";
import { CURRENCY_OPTIONS } from "@/lib/currency";
import { useTheme } from "@/lib/theme";

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
  const { theme, toggleTheme } = useTheme();

  const navLinks = [
    { id: "overview", label: "Overview" },
    ...(hasActiveProject
      ? [
          { id: "home-options", label: "Homes" },
          { id: "budget-costs", label: "Budget" },
          { id: "moving-timeline", label: "Timeline" },
          { id: "lease-review", label: "Lease" },
        ]
      : []),
    { id: "how-it-works", label: "How It Works" },
  ];

  const handleLinkClick = (id: string) => {
    onNavigateSection(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="border-b border-[#E4E8E3] dark:border-[#354540] bg-[#FAF8F3]/95 dark:bg-[#101918]/95 backdrop-blur-md sticky top-0 z-50 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between gap-4">
        
        {/* Left: Distinctive Brand Logo & Title */}
        <div 
          className="flex items-center space-x-3 cursor-pointer group flex-shrink-0"
          onClick={() => handleLinkClick("top")}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleLinkClick("top"); } }}
          aria-label="NEXMOVE Home"
        >
          {/* Polished Logo Container with stylized vector monogram mark */}
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0F766E] to-[#115E59] dark:from-[#2DD4BF] dark:to-[#0F766E] flex items-center justify-center shadow-card group-hover:scale-102 transition-transform duration-200 flex-shrink-0">
            <svg 
              className="w-5 h-5 text-white dark:text-[#101918]" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2.5" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              aria-hidden="true"
            >
              {/* Modern geometric N with forward relocation arrow chevron */}
              <path d="M4 19V5l9 14V5" />
              <path d="M17 9l4 4-4 4" />
            </svg>
          </div>

          <div>
            <div className="flex items-center space-x-1.5">
              <span className="text-xl font-extrabold tracking-tight text-[#18312F] dark:text-[#F3F7F4] leading-none">
                NEXMOVE
              </span>
            </div>
            <p className="text-[11px] text-[#526461] dark:text-[#B6C6C1] mt-0.5 font-medium leading-tight hidden sm:block">
              Your next move, made simple.
            </p>
          </div>
        </div>

        {/* Center: Clean Navigation Links */}
        <nav 
          className="hidden md:flex items-center space-x-1 text-xs lg:text-sm font-medium text-[#526461] dark:text-[#B6C6C1] overflow-x-auto py-1" 
          aria-label="Main Navigation"
        >
          {navLinks.map((link) => (
            <button
              key={link.id}
              onClick={() => handleLinkClick(link.id)}
              className="px-3 py-1.5 rounded-lg hover:text-[#0F766E] dark:hover:text-[#5EEAD4] hover:bg-[#E8F3F0]/60 dark:hover:bg-[#203D37]/50 transition whitespace-nowrap focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F766E] dark:focus-visible:ring-[#5EEAD4]"
            >
              {link.label}
            </button>
          ))}
        </nav>

        {/* Right: Utilities & Primary Action */}
        <div className="hidden sm:flex items-center space-x-2.5 flex-shrink-0">
          
          {/* Currency Selector */}
          <div className="flex items-center space-x-1 bg-white dark:bg-[#182321] border border-[#E4E8E3] dark:border-[#354540] rounded-xl px-2.5 py-1.5 text-xs shadow-2xs hover:border-[#0F766E]/40 dark:hover:border-[#5EEAD4]/40 transition">
            <Globe className="w-3.5 h-3.5 text-[#526461] dark:text-[#B6C6C1]" aria-hidden="true" />
            <select
              value={currency}
              onChange={(e) => onCurrencyChange(e.target.value)}
              className="bg-transparent text-[#18312F] dark:text-[#F3F7F4] font-medium focus:outline-none cursor-pointer pr-1 text-xs"
              aria-label="Select display currency"
            >
              {CURRENCY_OPTIONS.map((c) => (
                <option key={c.code} value={c.code} className="bg-white dark:bg-[#182321] text-[#18312F] dark:text-[#F3F7F4]">
                  {c.code} ({c.symbol})
                </option>
              ))}
            </select>
          </div>

          {/* Theme Toggle (Light / Dark) */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-white dark:bg-[#182321] border border-[#E4E8E3] dark:border-[#354540] text-[#526461] dark:text-[#B6C6C1] hover:text-[#0F766E] dark:hover:text-[#5EEAD4] hover:bg-[#FAF8F3] dark:hover:bg-[#202D2A] transition shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F766E] dark:focus-visible:ring-[#5EEAD4]"
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              <Sun className="w-4 h-4 text-[#5EEAD4] animate-fadeIn" aria-hidden="true" />
            ) : (
              <Moon className="w-4 h-4 text-[#115E59] animate-fadeIn" aria-hidden="true" />
            )}
          </button>

          {/* Quiet Status Indicator */}
          <div className="hidden lg:flex items-center space-x-1.5 text-xs text-[#115E59] dark:text-[#5EEAD4] px-2.5 py-1.5 bg-[#E8F3F0] dark:bg-[#203D37] rounded-xl border border-[#CCE3D7] dark:border-[#354540]">
            <span className="w-2 h-2 rounded-full bg-[#237A57] dark:bg-[#5EEAD4] animate-pulse" aria-hidden="true"></span>
            <span className="font-medium text-[11px]">Ready</span>
          </div>

          {/* Primary Action Button */}
          <button
            onClick={onPlanClick}
            className="bg-[#0F766E] hover:bg-[#115E59] dark:bg-[#5EEAD4] dark:hover:bg-[#2DD4BF] text-white dark:text-[#101918] font-semibold text-xs px-4 py-2.5 rounded-xl flex items-center space-x-1.5 shadow-xs hover:shadow transition focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F766E] dark:focus-visible:ring-[#5EEAD4]"
          >
            <span>{hasActiveProject ? "Plan Another Move" : "Plan My Move"}</span>
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>

        {/* Mobile Hamburger Toggle & Mobile Theme Switcher */}
        <div className="flex items-center space-x-2 sm:hidden">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-[#526461] dark:text-[#B6C6C1] bg-white dark:bg-[#182321] border border-[#E4E8E3] dark:border-[#354540]"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="w-4 h-4 text-[#5EEAD4]" /> : <Moon className="w-4 h-4 text-[#0F766E]" />}
          </button>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-[#18312F] dark:text-[#F3F7F4] hover:bg-[#E8F3F0] dark:hover:bg-[#202D2A]"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="sm:hidden border-t border-[#E4E8E3] dark:border-[#354540] bg-white dark:bg-[#182321] px-4 py-4 space-y-3 shadow-lg animate-fadeIn">
          <div className="flex items-center justify-between pb-3 border-b border-[#E4E8E3] dark:border-[#354540]">
            <span className="text-xs text-[#526461] dark:text-[#B6C6C1] font-medium">Display Currency:</span>
            <select
              value={currency}
              onChange={(e) => onCurrencyChange(e.target.value)}
              className="text-xs font-semibold text-[#18312F] dark:text-[#F3F7F4] bg-[#FAF8F3] dark:bg-[#202D2A] border border-[#E4E8E3] dark:border-[#354540] px-2.5 py-1 rounded-md"
              aria-label="Select display currency"
            >
              {CURRENCY_OPTIONS.map((c) => (
                <option key={c.code} value={c.code} className="bg-white dark:bg-[#182321]">
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
                className="w-full text-left px-3 py-2 text-sm font-medium text-[#18312F] dark:text-[#F3F7F4] hover:bg-[#E8F3F0] dark:hover:bg-[#203D37] rounded-lg transition"
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
            className="w-full mt-2 bg-[#0F766E] hover:bg-[#115E59] dark:bg-[#5EEAD4] dark:hover:bg-[#2DD4BF] text-white dark:text-[#101918] font-semibold text-sm py-2.5 rounded-xl flex items-center justify-center space-x-2 shadow-xs"
          >
            <span>{hasActiveProject ? "Plan Another Move" : "Plan My Move"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </header>
  );
}
