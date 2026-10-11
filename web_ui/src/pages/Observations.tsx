import React, { useEffect, useState } from 'react';
import {
  Binoculars,
  Search,
  Filter,
  Eye,
  RefreshCw,
  X,
  MapPin,
  Calendar,
  Map,
  Maximize2,
  Compass,
  Table,
} from 'lucide-react';
import { api } from '../services/api';
import { ObservationRecord } from '../types';
import { GeographicMap } from './GeographicMap';

export const Observations: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'map' | 'ledger'>('map');
  const [observations, setObservations] = useState<ObservationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [speciesFilter, setSpeciesFilter] = useState('ALL');
  const [selectedObs, setSelectedObs] = useState<ObservationRecord | null>(null);
  const [mapModalOpen, setMapModalOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getObservations(100);
      setObservations(res.observations || []);
    } catch (err) {
      console.error('Failed to load observations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filtered = observations.filter((o) => {
    const matchesSearch =
      (o.assigned_name || o.assigned_identity || o.species || '')
        .toLowerCase()
        .includes(searchTerm.toLowerCase()) ||
      o.station_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSpecies =
      speciesFilter === 'ALL' ||
      o.species?.toLowerCase() === speciesFilter.toLowerCase();
    return matchesSearch && matchesSpecies;
  });

  const uniqueSpecies = Array.from(new Set(observations.map((o) => o.species))).filter(Boolean);

  return (
    <div className="space-y-6 text-stone-100">
      {/* Header with View Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center space-x-2">
            <Binoculars className="w-7 h-7 text-amber-400" />
            <span>Field Observations & Habitat Cartography</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time verified wildlife sightings ledger, spatial habitat GIS, and sanctuary cartography
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          {/* Sub-view Switcher */}
          <div className="flex items-center bg-slate-900/80 backdrop-blur-md p-1 rounded-2xl border border-slate-700/60">
            <button
              onClick={() => setActiveTab('map')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 ${
                activeTab === 'map'
                  ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Habitat GIS & Heatmap</span>
            </button>

            <button
              onClick={() => setActiveTab('ledger')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 ${
                activeTab === 'ledger'
                  ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Table className="w-3.5 h-3.5" />
              <span>Sightings Ledger</span>
            </button>
          </div>

          <button
            onClick={() => setMapModalOpen(true)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-teal-400 flex items-center space-x-1.5 transition-colors"
          >
            <Map className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Artwork Map</span>
          </button>
        </div>
      </div>

      {/* VIEW A: INTERACTIVE HABITAT GIS & HEATMAP */}
      {activeTab === 'map' && (
        <div className="space-y-6">
          <GeographicMap />

          {/* Featured Artwork Map Banner */}
          <div className="p-5 rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-700/40 shadow-xl shadow-slate-950/40 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white text-sm">Sanctuary Biodiversity Illustrated Artwork Map</span>
                <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
                  Rohan Chakravarty Art
                </span>
              </div>
              <button
                onClick={() => setMapModalOpen(true)}
                className="text-xs text-amber-400 hover:underline flex items-center space-x-1"
              >
                <Maximize2 className="w-3 h-3" />
                <span>Expand Full Artwork</span>
              </button>
            </div>

            <div
              onClick={() => setMapModalOpen(true)}
              className="relative h-44 rounded-xl overflow-hidden cursor-pointer border border-slate-800 group"
            >
              <img
                src="/biodiversity_map.jpg"
                alt="Illustrated Wildlife Map"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 filter brightness-90"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent flex items-end p-4">
                <span className="text-xs font-mono text-slate-300">
                  Click to inspect high-resolution sanctuary biodiversity cartography
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW B: SIGHTINGS LEDGER */}
      {activeTab === 'ledger' && (
        <div className="space-y-4">
          {/* Search & Filter Toolbar */}
          <div className="p-4 rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-700/40 shadow-xl shadow-slate-950/40 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search tiger name, taxon, station..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-950/70 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:border-amber-400 focus:outline-none"
              />
            </div>

            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <div className="flex items-center space-x-2 bg-slate-950/70 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={speciesFilter}
                  onChange={(e) => setSpeciesFilter(e.target.value)}
                  className="bg-transparent text-white focus:outline-none cursor-pointer"
                >
                  <option value="ALL" className="bg-slate-900">All Species</option>
                  {uniqueSpecies.map((s) => (
                    <option key={s} value={s} className="bg-slate-900">
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={loadData}
                disabled={loading}
                className="px-3.5 py-2 rounded-xl bg-slate-950/70 hover:bg-slate-900 border border-slate-700/80 text-xs font-semibold text-white flex items-center space-x-1.5 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {/* Observations Table */}
          <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-700/40 shadow-xl shadow-slate-950/40 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3">Observation</th>
                    <th className="px-5 py-3">Species Taxon</th>
                    <th className="px-5 py-3">Resident Identity</th>
                    <th className="px-5 py-3">Station & Zone</th>
                    <th className="px-5 py-3">Timestamp</th>
                    <th className="px-5 py-3">Review Status</th>
                    <th className="px-5 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {filtered.length > 0 ? (
                    filtered.map((obs) => {
                      const isTiger = obs.species?.toLowerCase() === 'tiger';
                      return (
                        <tr
                          key={obs.observation_id}
                          className="hover:bg-slate-850/50 transition-colors"
                        >
                          <td className="px-5 py-3.5">
                            <div className="flex items-center space-x-3">
                              <div className="w-9 h-9 rounded-lg overflow-hidden bg-slate-950 border border-slate-800 shrink-0 flex items-center justify-center">
                                <img
                                  src={obs.crop_url || obs.image_url || '/biodiversity_map.jpg'}
                                  alt={obs.species}
                                  className="w-full h-full object-cover"
                                />
                              </div>
                              <span className="font-mono text-slate-400">#{obs.observation_id}</span>
                            </div>
                          </td>

                          <td className="px-5 py-3.5">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                                isTiger
                                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              }`}
                            >
                              {obs.species}
                            </span>
                          </td>

                          <td className="px-5 py-3.5">
                            <span className="font-semibold text-white">
                              {obs.assigned_name || obs.assigned_identity || '—'}
                            </span>
                            {obs.reid_score && (
                              <span className="block text-[10px] font-mono text-teal-400">
                                Match: {Math.round(obs.reid_score * 100)}%
                              </span>
                            )}
                          </td>

                          <td className="px-5 py-3.5 font-mono text-slate-300">
                            <div>{obs.station_id}</div>
                            <span className="text-[10px] text-slate-500">
                              {obs.range_name} • {obs.zone}
                            </span>
                          </td>

                          <td className="px-5 py-3.5 text-slate-400 font-mono text-[11px]">
                            {new Date(obs.timestamp).toLocaleDateString()} {new Date(obs.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </td>

                          <td className="px-5 py-3.5">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                obs.review_status === 'confirmed'
                                  ? 'bg-emerald-500/20 text-emerald-300'
                                  : 'bg-amber-500/20 text-amber-300'
                              }`}
                            >
                              {obs.review_status}
                            </span>
                          </td>

                          <td className="px-5 py-3.5 text-right">
                            <button
                              onClick={() => setSelectedObs(obs)}
                              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium transition-colors"
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={7} className="px-5 py-10 text-center text-slate-500">
                        {loading ? 'Loading observation ledger...' : 'No observation records match your filters.'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Observation Detail Inspection Modal */}
      {selectedObs && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="max-w-lg w-full bg-slate-900 border border-slate-700 rounded-2xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <span>Observation #{selectedObs.observation_id}</span>
                  <span className="text-xs uppercase text-amber-400 font-mono">({selectedObs.species})</span>
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  Captured at {selectedObs.station_id}
                </span>
              </div>
              <button
                onClick={() => setSelectedObs(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 h-64 flex items-center justify-center">
              <img
                src={selectedObs.crop_url || selectedObs.image_url || '/biodiversity_map.jpg'}
                alt={selectedObs.species}
                className="w-full h-full object-cover"
              />
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div>Station: <span className="text-white">{selectedObs.station_id}</span></div>
              <div>Flank: <span className="text-white">{selectedObs.flank_side.toUpperCase()}</span></div>
              <div>Status: <span className="text-amber-400">{selectedObs.review_status}</span></div>
              <div>Date: <span className="text-white">{new Date(selectedObs.timestamp).toLocaleDateString()}</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Map Artwork Modal */}
      {mapModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex flex-col p-4 sm:p-8">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-lg font-bold text-white">Sanctuary Biodiversity Illustrated Artwork Map</h3>
              <p className="text-xs text-slate-400">By Rohan Chakravarty • High Resolution Wildlife Illustrated Cartography</p>
            </div>
            <button
              onClick={() => setMapModalOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs font-bold"
            >
              Close ✕
            </button>
          </div>
          <div className="flex-1 overflow-auto flex items-center justify-center p-4">
            <img
              src="/biodiversity_map.jpg"
              alt="Biodiversity Map Full"
              className="max-h-[85vh] w-auto rounded-xl object-contain shadow-2xl border border-slate-800"
            />
          </div>
        </div>
      )}
    </div>
  );
};
