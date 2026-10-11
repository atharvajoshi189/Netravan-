import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { SpeciesClass, ObservationRecord } from '../types';
import { Shield, Search, Filter, BookOpen, Camera, Maximize2, Map } from 'lucide-react';

export const SpeciesAnalytics: React.FC = () => {
  const [speciesList, setSpeciesList] = useState<SpeciesClass[]>([]);
  const [observations, setObservations] = useState<ObservationRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedDiet, setSelectedDiet] = useState<string>('ALL');
  const [selectedSpecies, setSelectedSpecies] = useState<SpeciesClass | null>(null);
  const [mapModalOpen, setMapModalOpen] = useState<boolean>(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [specRes, obsRes] = await Promise.all([
          api.getSpecies(),
          api.getObservations(100),
        ]);
        setSpeciesList(specRes.classes || []);
        setObservations(obsRes.observations || []);
      } catch (err) {
        console.error('Failed to load species data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const sightingCounts: Record<string, number> = {};
  observations.forEach((o) => {
    const sp = o.species.toLowerCase();
    sightingCounts[sp] = (sightingCounts[sp] || 0) + 1;
  });

  const dietCategories = Array.from(new Set(speciesList.map((s) => s.diet_category))).filter(Boolean);

  const filteredSpecies = speciesList.filter((s) => {
    const matchesSearch =
      s.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.scientific_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.canonical_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDiet = selectedDiet === 'ALL' || s.diet_category === selectedDiet;
    return matchesSearch && matchesDiet;
  });

  const getIucnBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'EN':
      case 'ENDANGERED':
        return 'bg-red-900/40 text-red-400 border-red-500/30';
      case 'VU':
      case 'VULNERABLE':
        return 'bg-amber-900/40 text-amber-400 border-amber-500/30';
      case 'NT':
      case 'NEAR THREATENED':
        return 'bg-yellow-900/40 text-yellow-400 border-yellow-500/30';
      case 'LC':
      case 'LEAST CONCERN':
        return 'bg-emerald-900/40 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-teal-900/60 text-sage-300 border-teal-800';
    }
  };

  return (
    <div className="space-y-8 text-ivory">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Shield className="w-6 h-6 text-gold-400" />
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-ivory">
              Wildlife Species & Biodiversity
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-sage-300 mt-1">
            Canonical 17-class ecosystem taxonomy, diet dependencies & nocturnal IR camera profiles
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-sage-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search common / scientific name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-teal-950/80 border border-teal-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-ivory placeholder-sage-500 focus:outline-none focus:border-gold-500 w-64"
            />
          </div>

          <div className="flex items-center space-x-2 bg-teal-950/80 border border-teal-800 rounded-lg px-3 py-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-sage-400" />
            <select
              value={selectedDiet}
              onChange={(e) => setSelectedDiet(e.target.value)}
              className="bg-transparent text-ivory focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-teal-950">All Diet Categories</option>
              {dietCategories.map((cat) => (
                <option key={cat} value={cat} className="bg-teal-950">
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Featured Illustrated Biodiversity Map Artwork */}
      <div className="rounded-3xl p-6 bg-gradient-to-br from-teal-900/50 to-charcoal-900 border border-teal-800 shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Map className="w-5 h-5 text-gold-400" />
            <h3 className="text-base font-bold text-ivory">Sanctuary Biodiversity Illustrated Artwork Map</h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-gold-500/15 text-gold-400 border border-gold-500/30">
              Rohan Chakravarty Original
            </span>
          </div>

          <button
            onClick={() => setMapModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-teal-950 hover:bg-teal-900 border border-teal-700 text-xs text-gold-400 font-semibold flex items-center space-x-1.5 transition-colors w-fit"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>View Full Map</span>
          </button>
        </div>

        <div
          onClick={() => setMapModalOpen(true)}
          className="relative h-64 rounded-2xl overflow-hidden cursor-pointer border border-teal-800/80 group"
        >
          <img
            src="/biodiversity_map.jpg"
            alt="Illustrated Wildlife Biodiversity Map"
            className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500 filter brightness-95"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-teal-950 via-transparent to-transparent opacity-80" />
          <div className="absolute bottom-3 left-4 text-xs font-semibold text-ivory flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-gold-400 animate-pulse"></span>
            <span>Click to inspect high-resolution biodiversity illustrated art</span>
          </div>
        </div>
      </div>

      {/* Grid of Species */}
      {loading ? (
        <div className="p-12 text-center text-sage-400 rounded-2xl bg-teal-900/20 border border-teal-800">
          <div className="w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm">Loading canonical taxonomy...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredSpecies.map((sp) => {
            const count = sightingCounts[sp.canonical_name.toLowerCase()] || 0;
            const isSelected = selectedSpecies?.canonical_id === sp.canonical_id;

            return (
              <div
                key={sp.canonical_id}
                onClick={() => setSelectedSpecies(sp)}
                className={`p-5 rounded-2xl cursor-pointer transition-all border ${
                  isSelected
                    ? 'border-gold-500/70 bg-teal-900/50 shadow-xl'
                    : 'border-teal-800/60 bg-teal-900/30 hover:border-teal-700 hover:bg-teal-900/40'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="text-[10px] font-mono text-sage-400 uppercase tracking-wider">
                      Taxon #{sp.canonical_id} • {sp.family}
                    </span>
                    <h3 className="text-lg font-bold text-ivory">{sp.display_name}</h3>
                    <p className="text-xs text-sage-400 italic">{sp.scientific_name}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getIucnBadge(sp.iucn_status)}`}>
                    {sp.iucn_status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs mb-3 pt-2 border-t border-teal-800/60">
                  <div>
                    <span className="text-[10px] text-sage-400 block">Diet Category</span>
                    <span className="text-sage-200 font-medium">{sp.diet_category}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-sage-400 block">Logged Observations</span>
                    <span className="text-gold-400 font-bold font-mono">{count} recorded</span>
                  </div>
                </div>

                <div className="bg-teal-950/70 rounded-xl p-2.5 border border-teal-800 text-[11px] space-y-1">
                  <div className="text-sage-300 font-medium flex items-center space-x-1">
                    <BookOpen className="w-3 h-3 text-gold-400" />
                    <span>Ecological Role:</span>
                  </div>
                  <p className="text-sage-300 text-[11px] leading-relaxed">
                    {sp.tadoba_diet_relevance || 'Ecological contributor in tropical deciduous forest ecosystems.'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Selected Species Detail Drawer */}
      {selectedSpecies && (
        <div className="p-6 rounded-2xl bg-teal-950/90 border-l-4 border-l-gold-500 border border-teal-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-ivory flex items-center space-x-2">
              <Camera className="w-5 h-5 text-gold-400" />
              <span>Diagnostic Profile: {selectedSpecies.display_name} ({selectedSpecies.scientific_name})</span>
            </h3>
            <button
              onClick={() => setSelectedSpecies(null)}
              className="text-xs text-sage-400 hover:text-ivory"
            >
              Close Drawer ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-teal-900/40 p-4 rounded-xl border border-teal-800 space-y-2">
              <h4 className="font-semibold text-gold-400">Morphological Characteristics</h4>
              <p className="text-sage-300 leading-relaxed">
                {selectedSpecies.morphology_notes ||
                  'Distinctive coloration, antler structure, and body silhouette documented in wildlife identification keys.'}
              </p>
            </div>

            <div className="bg-teal-900/40 p-4 rounded-xl border border-teal-800 space-y-2">
              <h4 className="font-semibold text-emerald-400">IR Flash Camera-Trap Signature</h4>
              <p className="text-sage-300 leading-relaxed">
                {selectedSpecies.ir_camera_trap_profile ||
                  'Key nocturnal identification features include flank contour, gait dynamics, eye reflection, and antler branching profile.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Map Modal */}
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
              alt="Biodiversity Map Full"
              className="max-h-[85vh] w-auto rounded-xl object-contain shadow-2xl border border-teal-800"
            />
          </div>
        </div>
      )}
    </div>
  );
};
