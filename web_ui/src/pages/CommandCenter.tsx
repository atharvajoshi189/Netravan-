import React, { useEffect, useState } from 'react';
import {
  Binoculars,
  Fingerprint,
  Radio,
  ClipboardCheck,
  AlertTriangle,
  ShieldCheck,
  TrendingUp,
  Download,
  ScanEye,
  RefreshCw,
  Clock,
  MapPin,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../services/api';
import { TelemetryData, ObservationRecord, AlertRecord } from '../types';

interface CommandCenterProps {
  telemetry: TelemetryData | null;
  onNavigate: (tab: any) => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  telemetry,
  onNavigate,
}) => {
  const [recentSightings, setRecentSightings] = useState<ObservationRecord[]>([]);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [obsRes, alertRes] = await Promise.all([
        api.getObservations(6),
        api.getAlerts(),
      ]);
      setRecentSightings(obsRes.observations || []);
      setAlerts(alertRes.alerts || []);
    } catch (err) {
      console.error('Failed to load command center data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-xl bg-gradient-to-r from-forest-900 via-charcoal-900 to-forest-950 border border-forest-700/50 shadow-lg">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
              NATIONAL PARK GRID
            </span>
            <span className="text-xs text-sage-300">Tadoba Core & Buffer Territory</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-ivory">
            Central Wildlife Intelligence & Tiger Biometrics
          </h1>
          <p className="text-xs text-ivory-dim mt-1 max-w-2xl">
            Autonomous camera-trap triage, stripe pattern re-identification, spatial
            movement forecasting, and human-wildlife conflict mitigation.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-shrink-0">
          <button
            onClick={() => onNavigate('live-analysis')}
            className="px-4 py-2 rounded-lg bg-forest-700 hover:bg-forest-600 text-ivory text-xs font-semibold flex items-center gap-2 transition-colors border border-forest-500/40 shadow-sm"
          >
            <ScanEye className="w-4 h-4 text-amber-400" />
            <span>Launch Image Scan</span>
          </button>
          <a
            href="/api/export_report"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-2 rounded-lg bg-charcoal-800 hover:bg-charcoal-700 text-ivory-muted text-xs font-medium flex items-center gap-1.5 transition-colors border border-charcoal-700"
          >
            <Download className="w-3.5 h-3.5 text-sage-400" />
            <span>Export Briefing</span>
          </a>
          <button
            onClick={loadData}
            title="Refresh"
            className="p-2 rounded-lg bg-charcoal-800 hover:bg-charcoal-700 text-ivory-muted text-xs transition-colors border border-charcoal-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="p-4 rounded-xl bg-charcoal-900/90 border border-charcoal-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-ivory-dim mb-2">
            <span>Sightings</span>
            <Binoculars className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-ivory">
            {telemetry?.total_sightings ?? 420}
          </div>
          <div className="text-[11px] text-emerald-400/90 mt-1 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Recorded Sightings</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-charcoal-900/90 border border-charcoal-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-ivory-dim mb-2">
            <span>Resident Tigers</span>
            <Fingerprint className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400">
            {telemetry?.total_tigers ?? 8}
          </div>
          <div className="text-[11px] text-ivory-dim mt-1">
            Catalogue profiles
          </div>
        </div>

        <div className="p-4 rounded-xl bg-charcoal-900/90 border border-charcoal-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-ivory-dim mb-2">
            <span>Camera Stations</span>
            <Radio className="w-4 h-4 text-sage-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-ivory">
            {telemetry?.station_count ?? 18}
          </div>
          <div className="text-[11px] text-sage-400 mt-1">
            {telemetry?.active_cameras_pct ?? 100}% Operational
          </div>
        </div>

        <div
          onClick={() => onNavigate('review-queue')}
          className="p-4 rounded-xl bg-charcoal-900/90 border border-amber-500/30 hover:border-amber-500/60 cursor-pointer transition-all flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between text-xs text-amber-400 mb-2">
            <span>Review Queue</span>
            <ClipboardCheck className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400">
            {telemetry?.pending_reviews ?? 123}
          </div>
          <div className="text-[11px] text-amber-400/80 mt-1">
            Pending Human Decisions
          </div>
        </div>

        <div
          onClick={() => onNavigate('alert-center')}
          className="p-4 rounded-xl bg-charcoal-900/90 border border-red-500/30 hover:border-red-500/60 cursor-pointer transition-all flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between text-xs text-red-400 mb-2">
            <span>Active Alerts</span>
            <AlertTriangle className="w-4 h-4 text-red-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold font-mono text-red-400">
            {(telemetry?.critical_alerts || 0) + (telemetry?.warning_alerts || 0)}
          </div>
          <div className="text-[11px] text-red-400/80 mt-1">
            {telemetry?.critical_alerts ?? 0} Critical Dispersals
          </div>
        </div>

        <div className="p-4 rounded-xl bg-charcoal-900/90 border border-charcoal-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-ivory-dim mb-2">
            <span>Quarantined Blanks</span>
            <ShieldCheck className="w-4 h-4 text-sage-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-ivory-muted">
            {telemetry?.quarantined_blanks ?? 74}
          </div>
          <div className="text-[11px] text-sage-400 mt-1">
            False Triggers Filtered
          </div>
        </div>
      </div>

      {/* Main Two-Column View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Detections & Observations Feed */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-wide text-ivory flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" />
              <span>Latest Camera Trap Sightings</span>
            </h2>
            <button
              onClick={() => onNavigate('observations')}
              className="text-xs text-sage-400 hover:text-ivory transition-colors"
            >
              View All Observations &rarr;
            </button>
          </div>

          <div className="space-y-2.5">
            {recentSightings.length === 0 ? (
              <div className="p-8 text-center text-xs text-ivory-dim bg-charcoal-900 border border-charcoal-800 rounded-xl">
                No recent sightings recorded yet.
              </div>
            ) : (
              recentSightings.map((s) => (
                <div
                  key={s.observation_id}
                  className="p-3 rounded-xl bg-charcoal-900/90 border border-charcoal-800 hover:border-charcoal-700 transition-all flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-charcoal-950 border border-charcoal-800 overflow-hidden flex-shrink-0 flex items-center justify-center">
                      {s.crop_url || s.image_url ? (
                        <img
                          src={s.crop_url || s.image_url}
                          alt={s.species}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <span className="text-lg">🐾</span>
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-ivory capitalize">
                          {s.assigned_name || s.assigned_identity || s.species}
                        </span>
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-forest-900 border border-forest-700 text-sage-300 uppercase">
                          {s.species}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-ivory-dim mt-0.5">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-sage-500" />
                          {s.station_id} ({s.range_name || 'Tadoba'})
                        </span>
                        <span>&bull;</span>
                        <span>{s.timestamp}</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right flex-shrink-0">
                    <span
                      className={`text-[10px] font-semibold font-mono px-2 py-0.5 rounded-full ${
                        s.review_status === 'confirmed'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {s.review_status.toUpperCase()}
                    </span>
                    {s.reid_score !== undefined && (
                      <div className="text-[10px] font-mono text-ivory-dim mt-1">
                        Score: {(s.reid_score * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Active Territorial & Behavioral Alerts */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-wide text-ivory flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span>Critical Territory Alerts</span>
            </h2>
            <button
              onClick={() => onNavigate('alert-center')}
              className="text-xs text-sage-400 hover:text-ivory transition-colors"
            >
              Alert Center &rarr;
            </button>
          </div>

          <div className="space-y-2.5">
            {alerts.slice(0, 5).map((a) => (
              <div
                key={a.alert_id}
                className="p-3.5 rounded-xl bg-charcoal-900/90 border border-charcoal-800 hover:border-red-500/30 transition-all"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                      a.severity === 'CRITICAL'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                    }`}
                  >
                    {a.alert_type}
                  </span>
                  <span className="text-[10px] text-ivory-dim font-mono">
                    {a.created_at?.slice(11, 16) || 'LIVE'}
                  </span>
                </div>
                <div className="text-xs font-semibold text-ivory">
                  Tiger {a.tiger_id} at {a.station_id || 'Buffer Boundary'}
                </div>
                <p className="text-[11px] text-ivory-dim mt-1 line-clamp-2">
                  {a.detected_change}
                </p>
              </div>
            ))}
          </div>

          {/* Quick System Policy Card */}
          <div className="p-4 rounded-xl bg-forest-950/80 border border-forest-800 text-xs space-y-2">
            <div className="font-semibold text-forest-300 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Step 13/14 Conservation Safeguards</span>
            </div>
            <p className="text-[11px] text-ivory-dim leading-relaxed">
              Automatic tiger identity confirmation is disabled. All candidates require
              human review verification. Strict left/right flank compatibility
              guards prevent cross-flank false matches.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
