import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Activity, AlertTriangle, Compass, CheckCircle2, TrendingUp, Info } from 'lucide-react';

export const BehaviorIntelligence: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] = useState<{
    status: string;
    tiger_count: number;
    predictions: Record<string, any>;
  } | null>(null);

  const fetchBehaviorData = async () => {
    setLoading(true);
    try {
      const res = await api.getBehaviorPredictions();
      setData(res);
    } catch (err) {
      console.error('Failed to load behavior intelligence:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBehaviorData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Activity className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl font-bold text-ivory">Movement & Behavior Intelligence</h1>
          </div>
          <p className="text-sm text-sage-300 mt-1">
            Spatial-temporal Markov corridor modeling and visual action classification subsystem
          </p>
        </div>

        <button
          onClick={fetchBehaviorData}
          className="px-4 py-2 bg-charcoal-900 hover:bg-charcoal-800 border border-charcoal-700 rounded-lg text-xs font-semibold text-ivory transition-colors flex items-center space-x-2"
        >
          <span>Refresh Predictions</span>
        </button>
      </div>

      {/* Critical Architecture Separation Alert */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Subsystem 1: Spatial Movement Forecasting */}
        <div className="card-glass rounded-xl p-5 border-l-4 border-l-emerald-500">
          <div className="flex items-start space-x-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-ivory">Spatial & Temporal Movement Predictor (ACTIVE)</h3>
              <p className="text-xs text-sage-300 mt-1">
                Operates via Markov Chain transition matrices and Kernel Density Estimation (KDE) over historical camera trap timestamps. Computes transition probabilities to neighboring monitoring grids.
              </p>
              <div className="mt-3 inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-emerald-950/60 border border-emerald-500/30 text-[11px] text-emerald-300">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Markov Predictor v1.4 Operational</span>
              </div>
            </div>
          </div>
        </div>

        {/* Subsystem 2: Visual Behavior Classification */}
        <div className="card-glass rounded-xl p-5 border-l-4 border-l-amber-500">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-ivory">Visual Behavior Classifier (AWAITING CHECKPOINT)</h3>
              <p className="text-xs text-sage-300 mt-1">
                Visual action pose recognition (e.g. resting, stalking, feeding, pacing) requires the trained YOLO visual behavior checkpoint. To maintain strict scientific integrity, labels are not fabricated.
              </p>
              <div className="mt-3 inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-amber-950/60 border border-amber-500/30 text-[11px] text-amber-300">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <span>Candidate Checkpoint: Google Drive Stage</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Real Markov Predictions Display */}
      {loading ? (
        <div className="card-glass rounded-xl p-12 text-center text-sage-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm">Evaluating spatial Markov chain models...</p>
        </div>
      ) : !data || Object.keys(data.predictions || {}).length === 0 ? (
        <div className="card-glass rounded-xl p-10 text-center space-y-3">
          <Info className="w-8 h-8 text-sage-400 mx-auto" />
          <h3 className="text-base font-semibold text-ivory">No Active Trajectories Logged</h3>
          <p className="text-xs text-sage-400 max-w-md mx-auto">
            The spatial predictor requires at least two verified sightings at different camera stations to construct transition vectors.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Object.entries(data.predictions).map(([tigerId, pred]: [string, any]) => {
            const nextStations = pred.predicted_next_stations || [];
            const trends = pred.directional_trend || {};

            return (
              <div key={tigerId} className="card-glass rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-charcoal-800 pb-3">
                  <div>
                    <span className="text-xs font-mono text-amber-400 uppercase tracking-wider">Identified Individual</span>
                    <h3 className="text-lg font-bold text-ivory">{tigerId}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-sage-400 uppercase">Current Station</span>
                    <p className="text-sm font-bold text-emerald-400">{pred.current_station || 'Unknown'}</p>
                  </div>
                </div>

                {/* Transition Probabilities */}
                <div>
                  <h4 className="text-xs font-semibold text-sage-300 mb-2 flex items-center space-x-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Predicted Next Camera Stations (Transition Matrix)</span>
                  </h4>
                  {nextStations.length > 0 ? (
                    <div className="space-y-2">
                      {nextStations.map(([st, prob]: [string, number], idx: number) => {
                        const pct = Math.round(prob * 100);
                        return (
                          <div key={idx} className="bg-charcoal-900/60 p-2.5 rounded-lg border border-charcoal-800">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="font-bold text-ivory">{st}</span>
                              <span className="font-mono text-emerald-400 font-semibold">{pct}% probability</span>
                            </div>
                            <div className="w-full bg-charcoal-800 rounded-full h-1.5">
                              <div
                                className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
                                style={{ width: `${pct}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-sage-500 italic">Uniform prior transition distribution.</p>
                  )}
                </div>

                {/* Directional Trend */}
                <div>
                  <h4 className="text-xs font-semibold text-sage-300 mb-2 flex items-center space-x-1.5">
                    <Compass className="w-3.5 h-3.5 text-amber-400" />
                    <span>Directional Movement Vector</span>
                  </h4>
                  <div className="grid grid-cols-4 gap-2 text-center">
                    {['North', 'East', 'South', 'West'].map((dir) => {
                      const val = trends[dir] || 0;
                      return (
                        <div key={dir} className="bg-charcoal-900/40 p-2 rounded border border-charcoal-800/80">
                          <span className="text-[10px] text-sage-400 block">{dir}</span>
                          <span className="text-xs font-bold text-ivory">{(val * 100).toFixed(0)}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Footnote */}
                <div className="pt-2 border-t border-charcoal-800 text-[11px] text-sage-400 flex items-center justify-between">
                  <span>Horizon: Next 6–12 Hours</span>
                  <span className="text-sage-500">{pred.evidence_type || 'Markov Trajectory Estimator'}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
