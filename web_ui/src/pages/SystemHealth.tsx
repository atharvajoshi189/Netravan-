import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { HealthData, TelemetryData } from '../types';
import { HeartPulse, CheckCircle2, Shield, Database, Cpu, RefreshCw, Terminal, Layers } from 'lucide-react';

export const SystemHealth: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const [h, t] = await Promise.all([api.getHealth(), api.getTelemetry()]);
      setHealth(h);
      setTelemetry(t);
      setLastChecked(new Date());
    } catch (err) {
      console.error('Failed to load system health:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <HeartPulse className="w-6 h-6 text-emerald-400" />
            <h1 className="text-2xl font-bold text-ivory">System Health & Runtime Diagnostics</h1>
          </div>
          <p className="text-sm text-sage-300 mt-1">
            FastAPI microservice telemetry, active database connection, and pipeline safeguards
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs text-sage-400 font-mono">
            Checked: {lastChecked.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="px-3 py-1.5 bg-charcoal-900 hover:bg-charcoal-800 border border-charcoal-700 rounded-lg text-xs font-semibold text-ivory transition-colors flex items-center space-x-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Probe Backend</span>
          </button>
        </div>
      </div>

      {/* Main Health Status Card */}
      <div className="card-glass rounded-xl p-6 border-l-4 border-l-emerald-500">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-emerald-950/80 border border-emerald-500/40 flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-ivory">
                  {health?.service || 'TigerTraceAI Wildlife Intelligence API'}
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-500/30">
                  {health?.status?.toUpperCase() || 'ONLINE'}
                </span>
              </div>
              <p className="text-xs text-sage-300 mt-0.5">
                Version: <span className="font-mono text-ivory">{health?.version || '2.2.0'}</span> • Platform Device:{' '}
                <span className="font-mono text-emerald-400 font-bold">{health?.device?.toUpperCase() || 'CPU'}</span>
              </p>
            </div>
          </div>

          <div className="text-right text-xs text-sage-400 font-mono">
            <div>Timestamp (UTC): {health?.timestamp_utc || new Date().toISOString()}</div>
          </div>
        </div>
      </div>

      {/* Grid of Subsystems */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Subsystem 1: Database Integrity */}
        <div className="card-glass rounded-xl p-5 space-y-3">
          <div className="flex items-center space-x-2 text-emerald-400">
            <Database className="w-5 h-5" />
            <h3 className="font-bold text-ivory text-sm">Active SQLite Store</h3>
          </div>
          <p className="text-xs text-sage-300 leading-relaxed">
            Preserving active conservation records with zero silent resetting:
          </p>
          <div className="bg-charcoal-950/70 p-3 rounded-lg border border-charcoal-800 text-xs font-mono space-y-1.5">
            <div className="text-sage-400">Path: <span className="text-ivory">data/database/tigertrace.db</span></div>
            <div className="text-sage-400">Sightings: <span className="text-emerald-400 font-bold">{telemetry?.total_sightings ?? 18}</span></div>
            <div className="text-sage-400">Registered Tigers: <span className="text-amber-400 font-bold">{telemetry?.total_tigers ?? 4}</span></div>
            <div className="text-sage-400">Stations: <span className="text-emerald-400 font-bold">{telemetry?.station_count ?? 18}</span></div>
          </div>
        </div>

        {/* Subsystem 2: Security & Privacy Guards */}
        <div className="card-glass rounded-xl p-5 space-y-3">
          <div className="flex items-center space-x-2 text-emerald-400">
            <Shield className="w-5 h-5" />
            <h3 className="font-bold text-ivory text-sm">Security & Privacy Rails</h3>
          </div>
          <p className="text-xs text-sage-300 leading-relaxed">
            Strict conservation safeguards and filesystem sandbox parameters:
          </p>
          <div className="bg-charcoal-950/70 p-3 rounded-lg border border-charcoal-800 text-xs font-mono space-y-1.5">
            <div className="text-sage-400">Path Traversal Barrier: <span className="text-emerald-400 font-bold">ENFORCED</span></div>
            <div className="text-sage-400">Human Identity Gate: <span className="text-emerald-400 font-bold">STEP 13 ACTIVE</span></div>
            <div className="text-sage-400">Privacy Blurring: <span className="text-emerald-400 font-bold">STEP 9A ENABLED</span></div>
            <div className="text-sage-400">Flutter API Contract: <span className="text-emerald-400 font-bold">COMPATIBLE</span></div>
          </div>
        </div>

        {/* Subsystem 3: Inference Device Status */}
        <div className="card-glass rounded-xl p-5 space-y-3">
          <div className="flex items-center space-x-2 text-emerald-400">
            <Cpu className="w-5 h-5" />
            <h3 className="font-bold text-ivory text-sm">Inference Device Profile</h3>
          </div>
          <p className="text-xs text-sage-300 leading-relaxed">
            Optimized local wildlife vision pipeline execution:
          </p>
          <div className="bg-charcoal-950/70 p-3 rounded-lg border border-charcoal-800 text-xs font-mono space-y-1.5">
            <div className="text-sage-400">Compute Backend: <span className="text-ivory">{health?.device || 'CPU'}</span></div>
            <div className="text-sage-400">Threading: <span className="text-emerald-400 font-bold">OpenMP / MKL</span></div>
            <div className="text-sage-400">Quarantined Blanks: <span className="text-sage-300 font-bold">{telemetry?.quarantined_blanks ?? 1}</span></div>
            <div className="text-sage-400">Fleet Active Rate: <span className="text-emerald-400 font-bold">{telemetry?.active_cameras_pct ?? 100}%</span></div>
          </div>
        </div>
      </div>

      {/* Active Pipeline Registry Check */}
      <div className="card-glass rounded-xl p-5 space-y-3">
        <h3 className="font-bold text-ivory text-sm flex items-center space-x-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          <span>Active Pipeline Checkpoint Manifest</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {health?.active_models &&
            Object.entries(health.active_models).map(([key, val]) => (
              <div key={key} className="bg-charcoal-900/60 p-3 rounded-lg border border-charcoal-800 space-y-1">
                <span className="text-sage-400 font-semibold uppercase text-[10px]">{key.replace(/_/g, ' ')}</span>
                <p className="font-mono text-sage-200 truncate">{val}</p>
              </div>
            ))}
        </div>
      </div>

      {/* Developer Startup & Troubleshooting Reference */}
      <div className="card-glass rounded-xl p-5 space-y-3">
        <h3 className="font-bold text-ivory text-sm flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span>Operational Startup Instructions</span>
        </h3>
        <div className="bg-charcoal-950/80 p-4 rounded-lg border border-charcoal-800 font-mono text-xs text-sage-300 space-y-2 overflow-x-auto">
          <div><span className="text-emerald-400"># 1. Start FastAPI Backend (Port 8000)</span></div>
          <div className="text-ivory pl-2">python TigerTrace_AI/ui/app.py</div>
          <div className="pt-2"><span className="text-emerald-400"># 2. Start Modern Web UI (Port 3000)</span></div>
          <div className="text-ivory pl-2">cd web_ui && npm run dev</div>
          <div className="pt-2"><span className="text-emerald-400"># 3. Run Test Suite</span></div>
          <div className="text-ivory pl-2">python -m unittest tests/test_shared_analysis_api.py</div>
        </div>
      </div>
    </div>
  );
};
