import React from 'react';
import { Shield, Eye, Cpu, Database, CheckCircle2, Lock, Leaf, FileCheck } from 'lucide-react';

export const About: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto space-y-12 pb-16 text-ivory">
      {/* Header */}
      <div className="text-center space-y-3 pt-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-900/60 border border-gold-500/30 text-xs font-mono font-bold text-gold-400 uppercase">
          <span>RESPONSIBLE CONSERVATION TECHNOLOGY</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-ivory">
          About NETRAVAN
        </h1>
        <p className="text-sm sm:text-base text-sage-200 max-w-2xl mx-auto font-light leading-relaxed">
          NETRAVAN is an open, autonomous wildlife intelligence and biometric conservation platform designed to monitor, protect, and understand endangered species through ethical, non-invasive artificial intelligence.
        </p>
      </div>

      {/* Core Principles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-teal-900/30 border border-teal-800/60 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-gold-500/10 border border-gold-500/30 flex items-center justify-center text-gold-400">
            <Eye className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-ivory">Non-Invasive Observation</h3>
          <p className="text-xs text-sage-300 leading-relaxed font-light">
            We reject physical tranquilization or invasive tagging whenever computer vision can recognize individuals naturally by coat patterns and stripe geometry.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-teal-900/30 border border-teal-800/60 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Shield className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-ivory">Anti-Poaching Privacy</h3>
          <p className="text-xs text-sage-300 leading-relaxed font-light">
            Exact geolocation coordinates of vulnerable animals are strictly restricted to authorized rangers and researchers, shielding endangered populations from illicit exploitation.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-teal-900/30 border border-teal-800/60 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <FileCheck className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-ivory">Verifiable Accountability</h3>
          <p className="text-xs text-sage-300 leading-relaxed font-light">
            Every biometric identification candidate includes raw keypoint matches, inlier counts, and cosine distances so biologists can independently verify decisions before cataloging.
          </p>
        </div>
      </div>

      {/* Technology Stack & Model Governance */}
      <div className="p-8 rounded-3xl bg-teal-900/20 border border-teal-800/60 space-y-6">
        <h2 className="text-xl font-bold text-ivory">Model Governance & Cryptographic Verification</h2>
        <p className="text-xs sm:text-sm text-sage-300 leading-relaxed font-light">
          NETRAVAN mandates 10-stage evaluation gates for all vision models. Checkpoints are verified via SHA-256 cryptographic fingerprints, benchmarked on localized CPU and GPU hardware, and inspected for cross-species confusion before receiving inference promotion.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-teal-950/70 border border-teal-800 space-y-1">
            <span className="text-gold-400 font-bold block">HotSpotter SIFT Engine</span>
            <span className="text-sage-300">Viewpoint-invariant affine geometric matching for stripe identification</span>
          </div>
          <div className="p-4 rounded-xl bg-teal-950/70 border border-teal-800 space-y-1">
            <span className="text-gold-400 font-bold block">Deep Biometric Embedding</span>
            <span className="text-sage-300">ArcFace cosine feature similarity extraction on CLAHE normalized flanks</span>
          </div>
          <div className="p-4 rounded-xl bg-teal-950/70 border border-teal-800 space-y-1">
            <span className="text-gold-400 font-bold block">Dual-Stage False Trigger Filter</span>
            <span className="text-sage-300">Automatic quarantine of wind/rain blank camera frames</span>
          </div>
          <div className="p-4 rounded-xl bg-teal-950/70 border border-teal-800 space-y-1">
            <span className="text-gold-400 font-bold block">Markov Movement Corridors</span>
            <span className="text-sage-300">Spatial-temporal transition modeling across camera telemetry points</span>
          </div>
        </div>
      </div>
    </div>
  );
};
