import React, { useEffect, useState } from 'react';
import {
  ClipboardCheck,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  Info,
} from 'lucide-react';
import { api } from '../services/api';
import { ReviewQueueItem } from '../types';

export const ReviewQueue: React.FC = () => {
  const [reviews, setReviews] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState<number | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const res = await api.getReviewQueue();
      setReviews(res.reviews || []);
    } catch (err) {
      console.error('Failed to load review queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleAction = async (
    reviewId: number,
    action: 'accept' | 'reject' | 'inconclusive'
  ) => {
    setActionInProgress(reviewId);
    try {
      await api.submitReviewAction(
        reviewId,
        action,
        'senior_officer',
        `Human review decision: ${action}`
      );
      setToastMsg(`Decision '${action.toUpperCase()}' recorded successfully.`);
      setTimeout(() => setToastMsg(null), 3000);
      loadQueue();
    } catch (err: any) {
      setToastMsg(`Action failed: ${err.message}`);
      setTimeout(() => setToastMsg(null), 4000);
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div className="space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center space-x-2">
            <ClipboardCheck className="w-7 h-7 text-gold-400" />
            <span>Human Review Queue</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Verified officer adjudication station for borderline biometric tiger stripe matches
          </p>
        </div>

        <button
          onClick={loadQueue}
          disabled={loading}
          className="px-3.5 py-2 rounded-xl bg-dark-800 hover:bg-dark-700 border border-dark-700 text-xs font-semibold text-white flex items-center space-x-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {toastMsg && (
        <div className="p-3 rounded-xl bg-dark-800 border border-gold-500/40 text-xs text-gold-300 font-semibold shadow-md">
          {toastMsg}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-400 rounded-2xl bg-dark-900 border border-dark-800">
          <div className="w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm">Loading pending verification items...</p>
        </div>
      ) : reviews.length === 0 ? (
        <div className="p-12 text-center text-slate-400 rounded-2xl bg-dark-900 border border-dark-800 space-y-2">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
          <h3 className="text-base font-semibold text-white">Review Queue Clear</h3>
          <p className="text-xs">All candidate tiger identifications have been resolved.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((item) => (
            <div
              key={item.review_id}
              className="p-5 rounded-2xl bg-dark-900 border border-dark-800 space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-dark-800 pb-3">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase">
                    Review Item #{item.review_id} • Sighting #{item.sighting_id}
                  </span>
                  <h3 className="text-lg font-bold text-white">
                    Candidate: <span className="text-gold-400">{item.suggested_name || item.suggested_tiger_id || 'Novel Individual'}</span>
                  </h3>
                </div>

                <div className="text-right text-xs font-mono">
                  <span className="text-slate-400 block">Match Score</span>
                  <span className="text-gold-400 font-bold text-sm">
                    {Math.round((item.suggested_score || 0) * 100)}%
                  </span>
                </div>
              </div>

              {/* Side-by-side Image Inspection */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3 rounded-xl bg-dark-950 border border-dark-800 space-y-1.5">
                  <span className="text-[10px] font-mono uppercase text-slate-400">
                    Query Camera Trap Crop ({item.query_flank || 'unknown'} flank)
                  </span>
                  <div className="rounded-lg overflow-hidden bg-dark-900 h-40 flex items-center justify-center border border-dark-800">
                    <img
                      src={item.crop_url || item.image_url || '/biodiversity_map.jpg'}
                      alt="Query Flank"
                      className="max-h-full object-contain"
                    />
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-dark-950 border border-dark-800 space-y-1.5">
                  <span className="text-[10px] font-mono uppercase text-slate-400">
                    Registered Catalogue Reference ({item.ref_flank || 'both'} flank)
                  </span>
                  <div className="rounded-lg overflow-hidden bg-dark-900 h-40 flex items-center justify-center border border-dark-800">
                    <img
                      src={item.ref_crop_url || '/biodiversity_map.jpg'}
                      alt="Reference Flank"
                      className="max-h-full object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/biodiversity_map.jpg';
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Inlier Biometric Details */}
              <div className="grid grid-cols-3 gap-2 text-xs font-mono p-3 rounded-xl bg-dark-950 border border-dark-800 text-center">
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase">SIFT Inliers</span>
                  <span className="font-bold text-white">{item.sift_inliers ?? 0}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase">Cosine Sim</span>
                  <span className="font-bold text-white">{((item.raw_cosine_sim || 0) * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase">Geometry</span>
                  <span className="font-bold text-emerald-400">{item.geometric_status || 'Verified'}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
                <button
                  onClick={() => handleAction(item.review_id, 'accept')}
                  disabled={actionInProgress === item.review_id}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase flex items-center space-x-1.5 transition-colors"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Confirm Match</span>
                </button>

                <button
                  onClick={() => handleAction(item.review_id, 'inconclusive')}
                  disabled={actionInProgress === item.review_id}
                  className="px-4 py-2 rounded-xl bg-dark-800 hover:bg-dark-700 text-slate-300 font-bold text-xs uppercase flex items-center space-x-1.5 transition-colors border border-dark-700"
                >
                  <HelpCircle className="w-4 h-4 text-amber-400" />
                  <span>Inconclusive</span>
                </button>

                <button
                  onClick={() => handleAction(item.review_id, 'reject')}
                  disabled={actionInProgress === item.review_id}
                  className="px-4 py-2 rounded-xl bg-rose-900/40 hover:bg-rose-900/60 text-rose-300 font-bold text-xs uppercase flex items-center space-x-1.5 transition-colors border border-rose-800"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Reject</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
