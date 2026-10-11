import React, { useEffect, useState } from 'react';
import {
  Fingerprint,
  ShieldAlert,
  Calendar,
  Layers,
  Sparkles,
  Info,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { api } from '../services/api';
import { TigerRecord } from '../types';

export const TigerIdentity: React.FC = () => {
  const [tigers, setTigers] = useState<TigerRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTigers = async () => {
    setLoading(true);
    try {
      const data = await api.getTigers();
      setTigers(data);
    } catch (err) {
      console.error('Failed to load tigers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTigers();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-ivory flex items-center gap-2">
            <Fingerprint className="w-5 h-5 text-amber-400" />
            <span>Resident Tiger Catalogue & Biometric Reference Profiles</span>
          </h1>
          <p className="text-xs text-ivory-dim mt-1">
            Registered wild Bengal tigers (Panthera tigris tigris) monitored across
            Tadoba-Andhari Tiger Reserve via lateral flank stripe biometric Re-ID.
          </p>
        </div>

        <button
          onClick={loadTigers}
          className="px-3 py-1.5 rounded-lg bg-charcoal-800 hover:bg-charcoal-700 text-xs text-ivory flex items-center gap-1.5 transition-colors border border-charcoal-700 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Biometric Guard Notice */}
      <div className="p-4 rounded-xl bg-forest-950/70 border border-forest-700/60 flex items-start gap-3">
        <Info className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <div className="font-bold text-forest-300">
            Biometric Stripe Asymmetry & Flank Protection
          </div>
          <p className="text-ivory-dim text-[11px] leading-relaxed">
            Every tiger exhibits unique, asymmetric stripe patterns on its left versus
            right flanks. TigerTraceAI strictly enforces Step 9A flank orientation
            guards: left-to-right comparisons are mathematically rejected (score 0.0)
            to prevent false identity confirmation.
          </p>
        </div>
      </div>

      {/* Tigers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {loading ? (
          <div className="col-span-full py-16 text-center text-xs text-ivory-dim">
            Loading tiger reference catalogue from SQLite...
          </div>
        ) : (
          tigers.map((t) => (
            <div
              key={t.tiger_id}
              className="rounded-xl bg-charcoal-900 border border-charcoal-800 overflow-hidden hover:border-amber-500/40 transition-all flex flex-col justify-between group"
            >
              <div>
                {/* Image Header */}
                <div className="h-44 bg-charcoal-950 border-b border-charcoal-800 relative overflow-hidden flex items-center justify-center">
                  {t.reference_crop_path ? (
                    <img
                      src={`/api/image?path=${t.reference_crop_path}`}
                      alt={t.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="text-4xl text-amber-500/30">🐅</div>
                  )}

                  <div className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-md bg-black/75 backdrop-blur-sm border border-charcoal-700 text-[10px] font-mono font-bold text-amber-400">
                    {t.status.toUpperCase()}
                  </div>

                  <div className="absolute bottom-2.5 left-2.5 px-2 py-0.5 rounded bg-black/75 backdrop-blur-sm border border-charcoal-700 text-[10px] text-ivory font-mono">
                    Registered: {t.flank_side_registered.toUpperCase()}
                  </div>
                </div>

                {/* Profile Details */}
                <div className="p-4 space-y-3">
                  <div>
                    <h3 className="text-base font-bold text-ivory flex items-center justify-between">
                      <span>{t.name}</span>
                      <span className="font-mono text-xs text-sage-400 font-normal">
                        {t.tiger_id}
                      </span>
                    </h3>
                    <div className="text-[11px] text-ivory-dim mt-0.5">
                      Gender: {t.gender === 'M' ? 'Male' : t.gender === 'F' ? 'Female' : 'Unknown'}
                    </div>
                  </div>

                  {t.notes && (
                    <p className="text-[11px] text-ivory-dim line-clamp-2 bg-charcoal-950/60 p-2 rounded border border-charcoal-800">
                      {t.notes}
                    </p>
                  )}

                  <div className="grid grid-cols-2 gap-2 text-[11px] font-mono pt-1">
                    <div className="p-2 rounded bg-charcoal-950 border border-charcoal-800">
                      <span className="text-ivory-dim text-[10px] block font-sans">
                        SIGHTINGS
                      </span>
                      <span className="text-ivory font-bold text-sm">
                        {t.sighting_count ?? 1}
                      </span>
                    </div>
                    <div className="p-2 rounded bg-charcoal-950 border border-charcoal-800">
                      <span className="text-ivory-dim text-[10px] block font-sans">
                        FIRST SEEN
                      </span>
                      <span className="text-sage-400 text-[11px]">
                        {t.first_seen_date?.slice(0, 10) || '2026-08'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-charcoal-950/60 border-t border-charcoal-800 text-[11px] text-ivory-dim flex items-center justify-between">
                <span>Catalogue verified profile</span>
                <span className="text-emerald-400 font-mono text-[10px]">✓ Enrolled</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
