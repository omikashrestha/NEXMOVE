"use client";

import React, { useState } from "react";
import { 
  ArrowRight, 
  Sparkles, 
  Home, 
  Wallet, 
  Truck, 
  FileText,
  CheckCircle2,
  ShieldCheck
} from "lucide-react";

interface HeroSectionProps {
  onStartClick: () => void;
  onExploreClick: () => void;
}

export default function HeroSection({ onStartClick, onExploreClick }: HeroSectionProps) {
  const [imageError, setImageError] = useState(false);

  return (
    <section className="relative overflow-hidden bg-[#FAF8F3] dark:bg-[#101918] border-b border-[#E4E8E3] dark:border-[#354540] py-10 md:py-16 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          {/* Left Column: Hero Copy & CTA (7 cols) */}
          <div className="lg:col-span-7 space-y-5 text-center lg:text-left">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-[#E8F3F0] dark:bg-[#203D37] text-[#115E59] dark:text-[#5EEAD4] text-xs font-semibold border border-[#CCE3D7] dark:border-[#354540]">
              <Sparkles className="w-3.5 h-3.5 text-[#0F766E] dark:text-[#5EEAD4]" aria-hidden="true" />
              <span>Multi-Agent Relocation Intelligence</span>
            </div>

            <div className="space-y-3">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-[#18312F] dark:text-[#F3F7F4] leading-tight">
                Your next move, <span className="text-[#0F766E] dark:text-[#5EEAD4]">made simple.</span>
              </h1>
              <p className="text-base sm:text-lg text-[#526461] dark:text-[#B6C6C1] max-w-2xl font-normal leading-relaxed">
                Find verified homes, calculate moving costs, and organize your relocation timeline in minutes with coordinated AI agents.
              </p>
            </div>

            {/* Supporting Line */}
            <p className="text-xs sm:text-sm text-[#526461] dark:text-[#B6C6C1] max-w-xl">
              NEXMOVE unifies verified neighborhood housing, 3-tier budgeting, transport logistics, and contractual lease audits into one actionable plan.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3 pt-2">
              <button
                onClick={onStartClick}
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-[#0F766E] hover:bg-[#115E59] dark:bg-[#5EEAD4] dark:hover:bg-[#2DD4BF] text-white dark:text-[#101918] font-semibold text-sm shadow-xs hover:shadow transition flex items-center justify-center space-x-2 group focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F766E] dark:focus-visible:ring-[#5EEAD4]"
              >
                <span>Plan My Move</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition" aria-hidden="true" />
              </button>

              <button
                onClick={onExploreClick}
                className="w-full sm:w-auto px-5 py-3.5 rounded-xl bg-white dark:bg-[#182321] hover:bg-[#FAF8F3] dark:hover:bg-[#202D2A] text-[#18312F] dark:text-[#F3F7F4] font-semibold text-sm border border-[#E4E8E3] dark:border-[#354540] transition shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F766E] dark:focus-visible:ring-[#5EEAD4]"
              >
                How NEXMOVE Works
              </button>
            </div>

            {/* Trust Highlights */}
            <div className="pt-2 flex flex-wrap items-center justify-center lg:justify-start gap-4 text-xs text-[#526461] dark:text-[#B6C6C1]">
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#237A57] dark:text-[#5EEAD4]" aria-hidden="true" />
                <span>Verified home listings</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#237A57] dark:text-[#5EEAD4]" aria-hidden="true" />
                <span>Zero hidden budget surprises</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#237A57] dark:text-[#5EEAD4]" aria-hidden="true" />
                <span>Plain-language lease review</span>
              </div>
            </div>
          </div>

          {/* Right Column: Curated Relocation Imagery Card (5 cols) */}
          <div className="lg:col-span-5">
            <div className="relative rounded-3xl bg-white dark:bg-[#182321] p-3.5 border border-[#E4E8E3] dark:border-[#354540] shadow-card overflow-hidden">
              <div className="relative rounded-2xl overflow-hidden aspect-[4/3] max-h-76 bg-[#FAF8F3] dark:bg-[#101918] flex items-center justify-center border border-[#E4E8E3]/60 dark:border-[#354540]">
                {!imageError ? (
                  <img
                    src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80"
                    alt="Bright, welcoming modern apartment interior with natural light and clean decor"
                    className="w-full h-full object-cover max-h-76 transition hover:scale-102 duration-500"
                    style={{ maxHeight: "304px", width: "100%", objectFit: "cover" }}
                    onError={() => setImageError(true)}
                    loading="lazy"
                  />
                ) : (
                  /* Accessible Fallback Illustration */
                  <div className="w-full h-full bg-[#E8F3F0] dark:bg-[#203D37] flex flex-col items-center justify-center p-6 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-[#0F766E] dark:bg-[#5EEAD4] text-white dark:text-[#101918] flex items-center justify-center mb-3 shadow-xs">
                      <Home className="w-8 h-8" aria-hidden="true" />
                    </div>
                    <h4 className="font-bold text-[#18312F] dark:text-[#F3F7F4] text-sm">Your Home & Moving Timeline</h4>
                    <p className="text-xs text-[#526461] dark:text-[#B6C6C1] mt-1 max-w-xs">
                      All your relocation details coordinated automatically.
                    </p>
                  </div>
                )}

                {/* Illustrative badge */}
                <div className="absolute bottom-2.5 left-2.5 bg-[#18312F]/85 dark:bg-[#101918]/90 backdrop-blur-xs text-white dark:text-[#F3F7F4] text-[10px] font-medium px-2.5 py-1 rounded-md border border-white/10 flex items-center space-x-1">
                  <ShieldCheck className="w-3 h-3 text-[#5EEAD4]" aria-hidden="true" />
                  <span>Curated relocation benchmark</span>
                </div>
              </div>

              {/* 4 Pillars Under Image */}
              <div className="grid grid-cols-4 gap-2 pt-3 text-center">
                <div className="p-2.5 rounded-xl bg-[#FAF8F3] dark:bg-[#202D2A] border border-[#E4E8E3] dark:border-[#354540]">
                  <Home className="w-4 h-4 text-[#0F766E] dark:text-[#5EEAD4] mx-auto mb-1" aria-hidden="true" />
                  <span className="text-[11px] font-semibold text-[#18312F] dark:text-[#F3F7F4] block">Homes</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#FAF8F3] dark:bg-[#202D2A] border border-[#E4E8E3] dark:border-[#354540]">
                  <Wallet className="w-4 h-4 text-[#0F766E] dark:text-[#5EEAD4] mx-auto mb-1" aria-hidden="true" />
                  <span className="text-[11px] font-semibold text-[#18312F] dark:text-[#F3F7F4] block">Budget</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#FAF8F3] dark:bg-[#202D2A] border border-[#E4E8E3] dark:border-[#354540]">
                  <Truck className="w-4 h-4 text-[#0F766E] dark:text-[#5EEAD4] mx-auto mb-1" aria-hidden="true" />
                  <span className="text-[11px] font-semibold text-[#18312F] dark:text-[#F3F7F4] block">Movers</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#FAF8F3] dark:bg-[#202D2A] border border-[#E4E8E3] dark:border-[#354540]">
                  <FileText className="w-4 h-4 text-[#0F766E] dark:text-[#5EEAD4] mx-auto mb-1" aria-hidden="true" />
                  <span className="text-[11px] font-semibold text-[#18312F] dark:text-[#F3F7F4] block">Leases</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
