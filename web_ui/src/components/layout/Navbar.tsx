import React from 'react';
import { Eye, Sparkles, Compass, CheckCircle2, Shield, Activity } from 'lucide-react';
import { HealthData } from '../../types';

export type CleanNavTab = 'studio' | 'explore' | 'review';
export type NavTab = CleanNavTab;

interface NavbarProps {
  currentTab: CleanNavTab;
  onSelectTab: (tab: CleanNavTab) => void;
  health: HealthData | null;
  pendingReviewsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  health,
  pendingReviewsCount,
}) => {
  return (
    <header className="sticky top-0 z-50 bg-dark-900/90 backdrop-blur-md border-b border-dark-800 select-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-18 flex items-center justify-between">
        {/* Brand Logo & Wordmark */}
        <div
          onClick={() => onSelectTab('studio')}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gold-500 flex items-center justify-center shadow-lg shadow-gold-500/20 group-hover:scale-105 transition-transform duration-200">
            <Eye className="w-5 h-5 text-dark-950 stroke-[2.5]" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center space-x-2">
              <span className="text-xl font-black tracking-wider text-white uppercase font-sans">
                NETRA<span className="text-gold-400">VAN</span>
              </span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase tracking-wider bg-gold-500/10 text-gold-400 border border-gold-500/30">
                AI
              </span>
            </div>
            <span className="text-[10px] text-slate-400 tracking-wider uppercase font-medium">
              Wildlife Intelligence Platform
            </span>
          </div>
        </div>

        {/* Clean 3 Navigation Tabs */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          <button
            onClick={() => onSelectTab('studio')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold tracking-wide transition-all duration-150 flex items-center space-x-2 ${
              currentTab === 'studio'
                ? 'bg-dark-800 text-gold-400 border border-dark-700 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-dark-850'
            }`}
          >
            <Sparkles className="w-4 h-4 text-gold-400" />
            <span>AI Recognition Studio</span>
          </button>

          <button
            onClick={() => onSelectTab('explore')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold tracking-wide transition-all duration-150 flex items-center space-x-2 ${
              currentTab === 'explore'
                ? 'bg-dark-800 text-gold-400 border border-dark-700 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-dark-850'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>Sightings & Map</span>
          </button>

          <button
            onClick={() => onSelectTab('review')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold tracking-wide transition-all duration-150 flex items-center space-x-2 ${
              currentTab === 'review'
                ? 'bg-dark-800 text-gold-400 border border-dark-700 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-dark-850'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Review Queue</span>
            {pendingReviewsCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                {pendingReviewsCount}
              </span>
            )}
          </button>
        </nav>

        {/* Right Status */}
        <div className="hidden md:flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-dark-800 border border-dark-700 text-xs text-slate-300 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Device: {health?.device?.toUpperCase() || 'CPU'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
