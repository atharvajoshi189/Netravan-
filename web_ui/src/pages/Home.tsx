import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  Shield,
  Eye,
  Camera,
  Activity,
  Layers,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Compass,
  TrendingUp,
  Maximize2,
  FileCheck2,
  Database,
  Cpu
} from 'lucide-react';
import { NavTab } from '../components/layout/Navbar';
import { TelemetryData } from '../types';

interface HomeProps {
  onNavigate: (tab: any) => void;
  telemetry: TelemetryData | null;
}

export const Home: React.FC<HomeProps> = ({ onNavigate, telemetry }) => {
  const [mapModalOpen, setMapModalOpen] = useState(false);

  return (
    <div className="space-y-24 pb-20 text-ivory">
      {/* =========================================================================
          HERO SECTION — CINEMATIC WILDLIFE EDITORIAL
         ========================================================================= */}
      <section className="relative min-h-[85vh] -mt-6 -mx-4 sm:-mx-6 lg:-mx-8 flex items-center justify-center overflow-hidden">
        {/* Background Image with Deep Teal Vignette Gradient */}
        <div className="absolute inset-0 z-0">
          <img
            src="/netravan_hero.jpg"
            alt="Royal Bengal Tiger in Natural Habitat"
            className="w-full h-full object-cover object-center filter brightness-[0.75] contrast-[1.08] scale-[1.02] transform transition-transform duration-1000"
          />
          {/* Deep Teal and Dark Forest overlays */}
          <div className="absolute inset-0 bg-gradient-to-t from-teal-950 via-teal-950/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-teal-950/80 via-transparent to-teal-950/70" />
          <div className="absolute inset-0 bg-radial-gradient from-transparent via-teal-950/30 to-teal-950" />
        </div>

        {/* Hero Content */}
        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center space-y-6 pt-12">
          {/* Subtle Platform Tag */}
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-teal-900/75 border border-gold-500/30 backdrop-blur-md text-xs font-semibold tracking-widest text-gold-400 uppercase shadow-lg shadow-gold-500/10">
            <span className="w-2 h-2 rounded-full bg-gold-400 animate-pulse"></span>
            <span>NEXT-GENERATION WILDLIFE INTELLIGENCE</span>
          </div>

          {/* Main Editorial Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[1.08] uppercase font-sans text-ivory drop-shadow-xl">
            SAVE WILDLIFE.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 via-gold-500 to-amber-300">
              PROTECT TOMORROW.
            </span>
          </h1>

          {/* Supporting Text */}
          <p className="text-base sm:text-xl text-sage-200 max-w-2xl mx-auto font-light leading-relaxed drop-shadow">
            AI-powered wildlife intelligence for a safer future where every species matters. Non-invasive computer vision, biometric stripe identification, and predictive habitat analytics.
          </p>

          {/* Call-to-Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <button
              onClick={() => onNavigate('explore')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gold-500 hover:bg-gold-400 text-charcoal-950 font-bold text-sm tracking-wider uppercase transition-all duration-200 shadow-xl shadow-gold-500/25 flex items-center justify-center space-x-2 group"
            >
              <span>Explore NETRAVAN</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={() => onNavigate('analysis')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-teal-900/80 hover:bg-teal-800/90 border border-teal-700/70 text-ivory font-bold text-sm tracking-wider uppercase transition-all duration-200 backdrop-blur-md flex items-center justify-center space-x-2"
            >
              <Sparkles className="w-4 h-4 text-gold-400" />
              <span>Launch AI Analysis</span>
            </button>
          </div>
        </div>

        {/* Bottom Fade */}
        <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-teal-950 to-transparent" />
      </section>

      {/* =========================================================================
          SECTION 1 — MISSION & CONSERVATION IMPACT
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-12">
          <span className="text-xs font-mono font-bold tracking-widest text-gold-400 uppercase">
            CONSERVATION PHILOSOPHY
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-ivory">
            Precision Intelligence for Vanishing Wilderness
          </h2>
          <p className="text-sm sm:text-base text-sage-300 leading-relaxed font-light">
            Conventional camera-trap surveillance produces terabytes of uncataloged imagery. NETRAVAN replaces manual sorting with privacy-preserving computer vision, ensuring rapid threat mitigation and individual animal welfare.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-teal-900/40 border border-teal-800/50 space-y-3 backdrop-blur-sm hover:border-gold-500/30 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-emerald-950 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Shield className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-ivory">Zero-Intrusion Conservation</h3>
            <p className="text-xs text-sage-300 leading-relaxed">
              Monitors wildlife behavior and territorial movements purely through camera traps and passive infrared sensors without darting, collaring, or disturbing natural habitat routines.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-teal-900/40 border border-teal-800/50 space-y-3 backdrop-blur-sm hover:border-gold-500/30 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-gold-950 border border-gold-500/40 flex items-center justify-center text-gold-400">
              <Camera className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-ivory">Edge-Ready Biometric Vision</h3>
            <p className="text-xs text-sage-300 leading-relaxed">
              Equipped with SIFT keypoint stripe-matching and deep feature embeddings capable of operating 100% offline at remote field stations without internet dependencies.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-teal-900/40 border border-teal-800/50 space-y-3 backdrop-blur-sm hover:border-gold-500/30 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-blue-950 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-ivory">Responsible AI Governance</h3>
            <p className="text-xs text-sage-300 leading-relaxed">
              Strict ethical protections prevent automated misidentification. Borderline identity cases require expert human sign-off with verifiable audit trails before entering catalogues.
            </p>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 2 — HOW AI-ASSISTED WILDLIFE MONITORING WORKS
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-12">
          <span className="text-xs font-mono font-bold tracking-widest text-gold-400 uppercase">
            OPERATIONAL ARCHITECTURE
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-ivory">
            The 5-Stage Intelligence Pipeline
          </h2>
          <p className="text-sm text-sage-300 font-light">
            From raw camera-trap triggers to verified biological alerts in milliseconds.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {[
            {
              step: '01',
              title: 'Triage & Blank Filter',
              desc: 'Dual-stage filtering quenches false alarms caused by moving foliage, wind, or rain.',
              tag: 'YOLOv8 Cls',
            },
            {
              step: '02',
              title: 'Privacy Safeguard',
              desc: 'Automatically blurs detected human presence and eco-tourist vehicles in field footage.',
              tag: 'Step 9A Guard',
            },
            {
              step: '03',
              title: 'Flank Extraction',
              desc: 'Scales target bounding boxes and extracts contrast-enhanced (CLAHE) flank patches.',
              tag: 'Step 9B Crop',
            },
            {
              step: '04',
              title: 'Stripe Re-ID Matching',
              desc: 'Combines HotSpotter SIFT keypoint inliers with deep cosine similarity.',
              tag: 'HotSpotter + ArcFace',
            },
            {
              step: '05',
              title: 'Human Review Gate',
              desc: 'Audited senior wildlife officer verification for unmatched or ambiguous individuals.',
              tag: 'Step 13/14 Rails',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-teal-900/30 border border-teal-800/50 flex flex-col justify-between space-y-3 hover:border-teal-700 transition-colors"
            >
              <div>
                <span className="text-2xl font-black font-mono text-gold-400">{item.step}</span>
                <h4 className="text-sm font-bold text-ivory mt-1">{item.title}</h4>
                <p className="text-[11px] text-sage-300 mt-1 leading-relaxed">{item.desc}</p>
              </div>
              <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-teal-950/70 text-sage-300 border border-teal-800 w-fit">
                {item.tag}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* =========================================================================
          SECTION 3 — WILDLIFE DETECTION & SPECIES IDENTIFICATION
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div className="space-y-5">
            <span className="text-xs font-mono font-bold tracking-widest text-gold-400 uppercase">
              SPECIES VISION ENGINE
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-ivory leading-tight">
              Beyond Apex Predators:<br />Full Ecosystem Observation
            </h2>
            <p className="text-sm text-sage-300 leading-relaxed font-light">
              Ecosystem balance depends on prey population health. NETRAVAN is designed with a canonical 17-class wildlife taxonomy to identify herbivores, cervids, bovids, primates, and competitor carnivores across daytime and infrared night flashes.
            </p>

            <div className="space-y-3 text-xs">
              <div className="flex items-center space-x-3 text-sage-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Primary Prey Biomass: Chital, Sambar, Gaur, and Wild Boar classification</span>
              </div>
              <div className="flex items-center space-x-3 text-sage-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Secondary & Rare Prey: Nilgai, Barking Deer (Muntjac), and Chousingha</span>
              </div>
              <div className="flex items-center space-x-3 text-sage-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Competitor Coexistence: Leopard, Dhole (Wild Dog), and Sloth Bear</span>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={() => onNavigate('wildlife')}
                className="px-5 py-2.5 rounded-xl bg-teal-900 hover:bg-teal-800 border border-teal-700 text-ivory text-xs font-bold uppercase tracking-wider flex items-center space-x-2 transition-colors"
              >
                <span>View Species Taxonomy Catalog</span>
                <ArrowRight className="w-3.5 h-3.5 text-gold-400" />
              </button>
            </div>
          </div>

          {/* Feature Showcase Card */}
          <div className="p-6 rounded-3xl bg-gradient-to-br from-teal-900/50 to-charcoal-900 border border-teal-800/80 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-teal-800/60 pb-3">
              <div className="flex items-center space-x-2">
                <Eye className="w-4 h-4 text-gold-400" />
                <span className="text-xs font-bold uppercase tracking-wider text-ivory">Taxonomy Radar</span>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">
                17 Classes Configured
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-teal-950/70 border border-teal-800/70">
                <span className="text-[10px] text-sage-400 uppercase">Apex Predator</span>
                <p className="font-bold text-gold-400 text-sm mt-0.5">Tiger (Panthera tigris)</p>
                <span className="text-[10px] text-sage-400">SIFT Re-ID Enabled</span>
              </div>
              <div className="p-3 rounded-xl bg-teal-950/70 border border-teal-800/70">
                <span className="text-[10px] text-sage-400 uppercase">Primary Cervid</span>
                <p className="font-bold text-ivory text-sm mt-0.5">Chital (Axis axis)</p>
                <span className="text-[10px] text-sage-400">Abundance Indicator</span>
              </div>
              <div className="p-3 rounded-xl bg-teal-950/70 border border-teal-800/70">
                <span className="text-[10px] text-sage-400 uppercase">Heavy Bovid</span>
                <p className="font-bold text-ivory text-sm mt-0.5">Gaur (Bos gaurus)</p>
                <span className="text-[10px] text-sage-400">Vulnerable IUCN</span>
              </div>
              <div className="p-3 rounded-xl bg-teal-950/70 border border-teal-800/70">
                <span className="text-[10px] text-sage-400 uppercase">Nocturnal Suid</span>
                <p className="font-bold text-ivory text-sm mt-0.5">Wild Boar (Sus scrofa)</p>
                <span className="text-[10px] text-sage-400">Foraging Dynamics</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 4 — TIGER STRIPE RE-IDENTIFICATION
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-teal-950 via-teal-900/60 to-teal-950 border border-teal-800/60 shadow-2xl">
          <div className="max-w-3xl space-y-4">
            <span className="text-xs font-mono font-bold tracking-widest text-gold-400 uppercase">
              BIOMETRIC FINGERPRINTING
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-ivory">
              Tiger Stripe Geometry:<br />Nature's Unique Barcode
            </h2>
            <p className="text-sm text-sage-200 leading-relaxed font-light">
              Just like human fingerprints, every tiger carries a unique, lifelong stripe pattern. NETRAVAN matches left and right flank crops against historical photo catalogues using viewpoint-invariant SIFT keypoint homographies combined with deep cosine feature vectors.
            </p>

            <div className="flex flex-wrap gap-3 pt-2">
              <span className="px-3 py-1 rounded-lg bg-teal-950 border border-teal-800 text-xs text-sage-300 font-mono">
                Flank Viewpoint Separation (Left vs Right)
              </span>
              <span className="px-3 py-1 rounded-lg bg-teal-950 border border-teal-800 text-xs text-sage-300 font-mono">
                RANSAC Geometric Verification
              </span>
              <span className="px-3 py-1 rounded-lg bg-teal-950 border border-teal-800 text-xs text-sage-300 font-mono">
                HotSpotter SIFT Inliers
              </span>
            </div>

            <div className="pt-4">
              <button
                onClick={() => onNavigate('intelligence')}
                className="px-6 py-3 rounded-xl bg-gold-500 hover:bg-gold-400 text-charcoal-950 font-bold text-xs uppercase tracking-wider transition-colors shadow-lg shadow-gold-500/20"
              >
                Inspect Resident Tiger Catalogue
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 5 — ILLUSTRATED BIODIVERSITY MAP & SANCTUARY INTELLIGENCE
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <span className="text-xs font-mono font-bold tracking-widest text-gold-400 uppercase">
              SANCTUARY ATLAS & CARTOGRAPHY
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-ivory">
              Ecosystem Biodiversity Map
            </h2>
            <p className="text-sm text-sage-300 max-w-xl font-light mt-1">
              Illustrated reserve map by naturalist Rohan Chakravarty depicting indigenous flora, fauna habitats, and crucial wildlife movement corridors.
            </p>
          </div>

          <button
            onClick={() => setMapModalOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-teal-900 hover:bg-teal-800 border border-teal-700 text-ivory text-xs font-bold uppercase tracking-wider flex items-center space-x-2 transition-colors w-fit"
          >
            <Maximize2 className="w-3.5 h-3.5 text-gold-400" />
            <span>Expand Full Artwork Map</span>
          </button>
        </div>

        {/* Featured Artwork Display Banner */}
        <div
          onClick={() => setMapModalOpen(true)}
          className="relative rounded-3xl overflow-hidden border border-teal-700/60 shadow-2xl cursor-pointer group max-h-[500px]"
        >
          <img
            src="/biodiversity_map.jpg"
            alt="Illustrated Wildlife Biodiversity Map"
            className="w-full h-full object-cover object-center group-hover:scale-[1.02] transition-transform duration-700 filter brightness-[0.95]"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-teal-950 via-teal-950/20 to-transparent opacity-80 group-hover:opacity-60 transition-opacity" />

          {/* Floating Caption Overlay */}
          <div className="absolute bottom-6 left-6 right-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-ivory pointer-events-none">
            <div>
              <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded bg-gold-500/20 text-gold-400 border border-gold-500/30 text-[10px] font-bold uppercase tracking-wider mb-1">
                Original Naturalist Cartography
              </div>
              <h3 className="text-xl font-bold">Biodiversity Sanctuary Map — Rohan Chakravarty</h3>
              <p className="text-xs text-sage-300">Click to explore high-resolution wildlife illustrated species</p>
            </div>
            <div className="px-4 py-2 rounded-xl bg-charcoal-950/80 backdrop-blur-md border border-teal-700/60 text-xs font-bold text-gold-400">
              Interactive Zoom Available 🔍
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 6 — VISUAL BEHAVIOR VS MOVEMENT FORECASTING
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center max-w-3xl mx-auto space-y-3 mb-10">
          <span className="text-xs font-mono font-bold tracking-widest text-gold-400 uppercase">
            SCIENTIFIC RIGOR & HONESTY
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-ivory">
            Visual Behavior vs. Spatial Trajectory Forecasting
          </h2>
          <p className="text-sm text-sage-300 font-light">
            NETRAVAN strictly separates spatial corridor modeling from visual animal pose classification to avoid scientific fabrication.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Spatial Markov Movement */}
          <div className="p-6 rounded-2xl bg-teal-900/40 border-l-4 border-l-emerald-500 border border-teal-800/60 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-emerald-400">
                <Compass className="w-5 h-5" />
                <h3 className="font-bold text-ivory text-base">Spatial Movement Predictor</h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-500/30">
                ACTIVE PIPELINE
              </span>
            </div>
            <p className="text-xs text-sage-300 leading-relaxed">
              Calculates Markov chain transition probabilities and Kernel Density Estimations (KDE) across historical camera-trap telemetry points. Projects which neighboring grid cell an animal is most likely to enter next.
            </p>
            <div className="pt-2 text-[11px] font-mono text-sage-400">
              Status: Markov transition matrices operational for resident individuals.
            </div>
          </div>

          {/* Visual Behavior Model */}
          <div className="p-6 rounded-2xl bg-teal-900/40 border-l-4 border-l-amber-500 border border-teal-800/60 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-amber-400">
                <AlertTriangle className="w-5 h-5" />
                <h3 className="font-bold text-ivory text-base">Visual Behavior Classifier</h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 text-amber-400 border border-amber-500/30">
                AWAITING CHECKPOINT
              </span>
            </div>
            <p className="text-xs text-sage-300 leading-relaxed">
              Visual action posture recognition (e.g., resting, stalking, scent-marking) requires the specialized YOLO action checkpoint. To uphold conservation integrity, labels are never fabricated when weights are external.
            </p>
            <div className="pt-2 text-[11px] font-mono text-amber-400">
              Status: Evaluated honestly as "Unavailable" until trained weights are promoted.
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 7 — HUMAN REVIEW & RESPONSIBLE AI
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="p-8 rounded-3xl bg-teal-900/30 border border-teal-800/60 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <FileCheck2 className="w-5 h-5 text-gold-400" />
              <h3 className="text-xl font-bold text-ivory">Human-in-the-Loop Review Station</h3>
            </div>
            <p className="text-xs sm:text-sm text-sage-300 max-w-xl font-light">
              Machine similarity metrics are uncalibrated heuristics. Borderline matches and unknown individuals are placed in an audited human queue for confirmation before entering the official database.
            </p>
          </div>

          <button
            onClick={() => onNavigate('review')}
            className="px-6 py-3 rounded-xl bg-gold-500 hover:bg-gold-400 text-charcoal-950 font-bold text-xs uppercase tracking-wider shrink-0 transition-colors shadow-lg shadow-gold-500/20"
          >
            Open Review Station
          </button>
        </div>
      </section>

      {/* =========================================================================
          SECTION 8 — LIVE CONSERVATION TELEMETRY
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center space-y-2 mb-8">
          <span className="text-xs font-mono font-bold tracking-widest text-gold-400 uppercase">
            LIVE PLATFORM TELEMETRY
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-ivory">
            Active Intelligence Telemetry
          </h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-teal-900/40 border border-teal-800/60 text-center">
            <span className="text-xs text-sage-400 uppercase">Recorded Sightings</span>
            <p className="text-3xl font-black text-ivory font-mono mt-1">
              {telemetry?.total_sightings ?? '18+'}
            </p>
            <span className="text-[10px] text-emerald-400">Verified Database Records</span>
          </div>

          <div className="p-5 rounded-2xl bg-teal-900/40 border border-teal-800/60 text-center">
            <span className="text-xs text-sage-400 uppercase">Resident Tigers</span>
            <p className="text-3xl font-black text-gold-400 font-mono mt-1">
              {telemetry?.total_tigers ?? '6'}
            </p>
            <span className="text-[10px] text-sage-300">Biometrically Enrolled</span>
          </div>

          <div className="p-5 rounded-2xl bg-teal-900/40 border border-teal-800/60 text-center">
            <span className="text-xs text-sage-400 uppercase">Camera Stations</span>
            <p className="text-3xl font-black text-ivory font-mono mt-1">
              {telemetry?.station_count ?? '18'}
            </p>
            <span className="text-[10px] text-emerald-400">Active Telemetry Grids</span>
          </div>

          <div className="p-5 rounded-2xl bg-teal-900/40 border border-teal-800/60 text-center">
            <span className="text-xs text-sage-400 uppercase">Pending Review</span>
            <p className="text-3xl font-black text-amber-400 font-mono mt-1">
              {telemetry?.pending_reviews ?? '1'}
            </p>
            <span className="text-[10px] text-amber-300">Human Verification Queue</span>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 9 — FINAL CTA & CLEAN FOOTER
         ========================================================================= */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="p-10 sm:p-14 rounded-3xl bg-gradient-to-r from-teal-950 via-teal-900 to-teal-950 border border-teal-700/60 text-center space-y-6 shadow-2xl">
          <h2 className="text-3xl sm:text-5xl font-black uppercase text-ivory tracking-tight">
            Ready to Analyze Wildlife Imagery?
          </h2>
          <p className="text-sm sm:text-base text-sage-200 max-w-xl mx-auto font-light">
            Upload any camera-trap image to evaluate detection bounding boxes, species probability, and biometric stripe re-identification.
          </p>
          <div>
            <button
              onClick={() => onNavigate('analysis')}
              className="px-8 py-4 rounded-xl bg-gold-500 hover:bg-gold-400 text-charcoal-950 font-black text-sm uppercase tracking-wider transition-all duration-200 shadow-xl shadow-gold-500/25"
            >
              Launch Live AI Analysis Studio
            </button>
          </div>
        </div>
      </section>

      {/* Clean Global Footer */}
      <footer className="border-t border-teal-800/50 pt-10 text-xs text-sage-400">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 rounded-lg bg-gold-500 flex items-center justify-center">
              <Eye className="w-3.5 h-3.5 text-charcoal-950 stroke-[2.5]" />
            </div>
            <span className="font-bold tracking-wider text-ivory uppercase">NETRAVAN</span>
            <span>— Autonomous Wildlife Intelligence Platform</span>
          </div>

          <div className="flex items-center space-x-6 text-[11px]">
            <button onClick={() => onNavigate('about')} className="hover:text-ivory transition-colors">
              About & Ethics
            </button>
            <button onClick={() => onNavigate('system')} className="hover:text-ivory transition-colors">
              Model Diagnostics
            </button>
            <button onClick={() => onNavigate('explore')} className="hover:text-ivory transition-colors">
              Wildlife Explorer
            </button>
          </div>
        </div>
      </footer>

      {/* High-Resolution Illustrated Map Modal */}
      {mapModalOpen && (
        <div className="fixed inset-0 z-50 bg-charcoal-950/95 backdrop-blur-xl flex flex-col p-4 sm:p-8">
          <div className="flex items-center justify-between pb-4 border-b border-teal-800">
            <div>
              <h3 className="text-lg font-bold text-ivory">Sanctuary Biodiversity Illustrated Artwork Map</h3>
              <p className="text-xs text-sage-400">By Rohan Chakravarty • High Resolution Wildlife Illustrated Cartography</p>
            </div>
            <button
              onClick={() => setMapModalOpen(false)}
              className="px-4 py-2 rounded-xl bg-teal-900 hover:bg-teal-800 border border-teal-700 text-ivory text-xs font-bold"
            >
              Close Fullscreen ✕
            </button>
          </div>
          <div className="flex-1 overflow-auto flex items-center justify-center p-4">
            <img
              src="/biodiversity_map.jpg"
              alt="Biodiversity Map Large"
              className="max-h-[85vh] w-auto rounded-xl object-contain shadow-2xl border border-teal-800"
            />
          </div>
        </div>
      )}
    </div>
  );
};
