import React from 'react';
import {
  LayoutDashboard,
  ScanEye,
  Binoculars,
  Fingerprint,
  ClipboardCheck,
  MapPin,
  TrendingUp,
  PawPrint,
  AlertTriangle,
  Radio,
  Boxes,
  Activity,
} from 'lucide-react';
import { TelemetryData } from '../../types';

export type NavigationTab =
  | 'command-center'
  | 'live-analysis'
  | 'observations'
  | 'tiger-identity'
  | 'review-queue'
  | 'geo-map'
  | 'movement-behavior'
  | 'species-analytics'
  | 'alert-center'
  | 'stations'
  | 'model-registry'
  | 'system-health';

interface SidebarProps {
  currentTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  telemetry: TelemetryData | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  telemetry,
}) => {
  const navItems: Array<{
    id: NavigationTab;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: number;
    badgeColor?: string;
  }> = [
    { id: 'command-center', label: 'Command Center', icon: LayoutDashboard },
    { id: 'live-analysis', label: 'Live Camera Analysis', icon: ScanEye },
    {
      id: 'observations',
      label: 'Wildlife Observations',
      icon: Binoculars,
      badge: telemetry?.total_sightings,
      badgeColor: 'bg-charcoal-700 text-ivory-dim',
    },
    {
      id: 'tiger-identity',
      label: 'Tiger Catalogue & Re-ID',
      icon: Fingerprint,
      badge: telemetry?.total_tigers,
      badgeColor: 'bg-forest-800 text-amber-400 border border-amber-500/20',
    },
    {
      id: 'review-queue',
      label: 'Human Review Queue',
      icon: ClipboardCheck,
      badge: telemetry?.pending_reviews,
      badgeColor: 'bg-amber-500/20 text-amber-400 border border-amber-500/40 animate-pulse',
    },
    { id: 'geo-map', label: 'Geographic GIS Map', icon: MapPin },
    {
      id: 'movement-behavior',
      label: 'Movement & Behavior',
      icon: TrendingUp,
    },
    { id: 'species-analytics', label: 'Prey & Species Analytics', icon: PawPrint },
    {
      id: 'alert-center',
      label: 'Conflict Alert Center',
      icon: AlertTriangle,
      badge: (telemetry?.critical_alerts || 0) + (telemetry?.warning_alerts || 0),
      badgeColor: 'bg-red-500/20 text-red-400 border border-red-500/30',
    },
    {
      id: 'stations',
      label: 'Camera Stations',
      icon: Radio,
      badge: telemetry?.station_count,
      badgeColor: 'bg-charcoal-700 text-ivory-dim',
    },
    { id: 'model-registry', label: 'Model Diagnostics', icon: Boxes },
    { id: 'system-health', label: 'System Health & Settings', icon: Activity },
  ];

  return (
    <aside className="w-64 border-r border-charcoal-700 bg-charcoal-900 flex flex-col flex-shrink-0 h-[calc(100vh-4rem)] sticky top-16 select-none">
      <div className="p-4 border-b border-charcoal-800/80">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-sage-400 mb-1">
          OPERATIONAL SUITE
        </div>
        <div className="text-xs text-ivory-dim">
          Tadoba AI Threat & Wildlife Biometrics
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-forest-800/90 text-ivory border border-forest-600/60 shadow-sm shadow-forest-950/50'
                  : 'text-ivory-muted hover:bg-charcoal-800/80 hover:text-ivory'
              }`}
            >
              <div className="flex items-center space-x-2.5 truncate">
                <Icon
                  className={`w-4 h-4 flex-shrink-0 transition-colors ${
                    isActive ? 'text-amber-400' : 'text-sage-400/80'
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span
                  className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-md flex-shrink-0 ml-1.5 ${
                    item.badgeColor || 'bg-charcoal-700 text-ivory-dim'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="p-3 border-t border-charcoal-800 bg-charcoal-950/60 text-[11px] text-ivory-dim">
        <div className="flex items-center justify-between font-mono text-[10px] text-sage-400">
          <span>PIPELINE</span>
          <span className="text-emerald-400 font-semibold">ONLINE</span>
        </div>
        <div className="text-[10px] text-ivory-dim/70 truncate mt-0.5">
          Step 9A/9B + 13/14 Active
        </div>
      </div>
    </aside>
  );
};
