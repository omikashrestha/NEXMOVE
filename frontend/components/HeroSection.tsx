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
  Calendar
} from "lucide-react";

interface HeroSectionProps {
  onStartClick: () => void;
  onExploreClick: () => void;
}

export default function HeroSection({ onStartClick, onExploreClick }: HeroSectionProps) {
  const [imageError, setImageError] = useState(false);

  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-blue-50/40 via-white to-slate-50 border-b border-slate-200/60 py-8 md:py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Left Column: Hero Copy & CTA (7 cols) */}
          <div className="lg:col-span-7 space-y-4 text-center lg:text-left">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200/60">
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              <span>Smart Relocation Assistant</span>
            </div>

            <div className="space-y-2">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-slate-900 leading-tight">
                Your next move, made simple.
              </h1>
              <p className="text-base sm:text-lg text-slate-600 max-w-2xl font-normal leading-relaxed">
                Find a suitable home, plan your moving costs, and organize your relocation in one place with help from AI.
              </p>
            </div>

            {/* Supporting Line */}
            <p className="text-xs sm:text-sm text-slate-500 max-w-xl">
              NEXMOVE brings housing, budgeting, moving logistics, and lease review together in one seamless plan.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3 pt-2">
              <button
                onClick={onStartClick}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-sm hover:shadow transition flex items-center justify-center space-x-2 group"
              >
                <span>Plan My Move</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition" />
              </button>

              <button
                onClick={onExploreClick}
                className="w-full sm:w-auto px-5 py-3 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm border border-slate-200 transition shadow-xs"
              >
                How NEXMOVE Works
              </button>
            </div>

            {/* Trust Pill Highlights */}
            <div className="pt-3 flex flex-wrap items-center justify-center lg:justify-start gap-4 text-xs text-slate-500">
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Verified home filters</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Zero hidden budget surprises</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Plain-English lease review</span>
              </div>
            </div>
          </div>

          {/* Right Column: Clean Visual Image / Card (5 cols) */}
          <div className="lg:col-span-5">
            <div className="relative rounded-2xl bg-white p-3 border border-slate-200/80 shadow-md overflow-hidden">
              <div className="relative rounded-xl overflow-hidden aspect-[4/3] max-h-72 bg-slate-100 flex items-center justify-center">
                {!imageError ? (
                  <img
                    src="https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=800&q=80"
                    alt="Bright modern apartment interior and relocation setup"
                    className="w-full h-full object-cover max-h-72 transition hover:scale-105 duration-500"
                    style={{ maxHeight: "288px", width: "100%", objectFit: "cover" }}
                    onError={() => setImageError(true)}
                    loading="lazy"
                  />
                ) : (
                  /* Fallback SVG illustration if offline or image blocked */
                  <div className="w-full h-full bg-gradient-to-br from-blue-50 to-indigo-50 flex flex-col items-center justify-center p-6 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-blue-600 text-white flex items-center justify-center mb-3 shadow-md">
                      <Home className="w-8 h-8" />
                    </div>
                    <h4 className="font-bold text-slate-800 text-sm">Your Home & Moving Timeline</h4>
                    <p className="text-xs text-slate-500 mt-1 max-w-xs">
                      All your relocation details coordinated automatically.
                    </p>
                  </div>
                )}

                {/* Subtle caption tag */}
                <div className="absolute bottom-2 left-2 bg-slate-900/75 backdrop-blur-xs text-white text-[10px] font-medium px-2 py-0.5 rounded">
                  Example home & moving plan
                </div>
              </div>

              {/* Quick Summary Pill Row Under Image */}
              <div className="grid grid-cols-4 gap-2 pt-3 text-center">
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <Home className="w-4 h-4 text-blue-600 mx-auto mb-1" />
                  <span className="text-[11px] font-semibold text-slate-700 block">Home</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <Wallet className="w-4 h-4 text-emerald-600 mx-auto mb-1" />
                  <span className="text-[11px] font-semibold text-slate-700 block">Budget</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <Truck className="w-4 h-4 text-amber-600 mx-auto mb-1" />
                  <span className="text-[11px] font-semibold text-slate-700 block">Moving</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <FileText className="w-4 h-4 text-purple-600 mx-auto mb-1" />
                  <span className="text-[11px] font-semibold text-slate-700 block">Lease</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
