import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StationRecord } from '../types';
import { MapPin, Search, Filter, RefreshCw, Eye, Signal, Compass, Radio } from 'lucide-react';

export const StationsRegistry: React.FC = () => {
  const [stations, setStations] = useState<StationRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [zoneFilter, setZoneFilter] = useState<string>('ALL');

  const fetchStations = async () => {
    setLoading(true);
    try {
      const res = await api.getStations();
      setStations(res.stations || []);
    } catch (err) {
      console.error('Failed to load stations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStations();
  }, []);

  const filteredStations = stations.filter((st) => {
    const matchesSearch =
      st.station_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      st.range_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      st.grid_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesZone = zoneFilter === 'ALL' || st.zone === zoneFilter;
    return matchesSearch && matchesZone;
  });

  const coreCount = stations.filter((s) => s.zone === 'Core').length;
  const bufferCount = stations.filter((s) => s.zone === 'Buffer').length;
  const activeCount = stations.filter((s) => s.is_active === 1).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Radio className="w-6 h-6 text-emerald-400" />
            <h1 className="text-2xl font-bold text-ivory">Camera Trap Stations Registry</h1>
          </div>
          <p className="text-sm text-sage-300 mt-1">
            Tadoba-Andhari Tiger Reserve telemetry grid — synchronized infrared camera monitoring network
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-sage-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search station ID, range, grid..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-charcoal-900 border border-charcoal-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-ivory placeholder-sage-500 focus:outline-none focus:border-emerald-500 w-56"
            />
          </div>

          <div className="flex items-center space-x-2 bg-charcoal-900 border border-charcoal-700 rounded-lg px-3 py-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-sage-400" />
            <select
              value={zoneFilter}
              onChange={(e) => setZoneFilter(e.target.value)}
              className="bg-transparent text-ivory focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-charcoal-900">All Zones ({stations.length})</option>
              <option value="Core" className="bg-charcoal-900">Core Protected ({coreCount})</option>
              <option value="Buffer" className="bg-charcoal-900">Buffer Corridor ({bufferCount})</option>
            </select>
          </div>

          <button
            onClick={fetchStations}
            disabled={loading}
            className="p-2 bg-charcoal-900 hover:bg-charcoal-800 border border-charcoal-700 rounded-lg text-sage-300 hover:text-ivory transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="card-glass rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs text-sage-400">Total Deployment</span>
            <p className="text-2xl font-bold text-ivory font-mono">{stations.length}</p>
          </div>
          <Radio className="w-7 h-7 text-emerald-400/30" />
        </div>

        <div className="card-glass rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs text-sage-400">Core Stations</span>
            <p className="text-2xl font-bold text-emerald-400 font-mono">{coreCount}</p>
          </div>
          <Compass className="w-7 h-7 text-emerald-500/30" />
        </div>

        <div className="card-glass rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs text-sage-400">Buffer Stations</span>
            <p className="text-2xl font-bold text-amber-400 font-mono">{bufferCount}</p>
          </div>
          <MapPin className="w-7 h-7 text-amber-500/30" />
        </div>

        <div className="card-glass rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-xs text-sage-400">Fleet Uptime</span>
            <p className="text-2xl font-bold text-emerald-400 font-mono">
              {stations.length > 0 ? Math.round((activeCount / stations.length) * 100) : 100}%
            </p>
          </div>
          <Signal className="w-7 h-7 text-emerald-400/30" />
        </div>
      </div>

      {/* Stations Card Grid */}
      {loading ? (
        <div className="card-glass rounded-xl p-12 text-center text-sage-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm">Loading monitoring telemetry...</p>
        </div>
      ) : filteredStations.length === 0 ? (
        <div className="card-glass rounded-xl p-12 text-center text-sage-400">
          <p>No stations match your criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredStations.map((station) => {
            const isCore = station.zone === 'Core';

            return (
              <div
                key={station.station_id}
                className="card-glass rounded-xl p-4 border border-charcoal-800 hover:border-emerald-500/40 transition-all space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <h3 className="text-base font-bold text-ivory">{station.station_id}</h3>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      isCore
                        ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-950/60 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {station.zone} Zone
                  </span>
                </div>

                <div>
                  <p className="text-sm text-ivory font-medium">{station.range_name} Range</p>
                  <p className="text-xs text-sage-400 font-mono">Grid Cell: {station.grid_id}</p>
                </div>

                <div className="bg-charcoal-950/70 p-2.5 rounded-lg border border-charcoal-800 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-[10px] text-sage-400 block">Coordinates</span>
                    <span className="font-mono text-sage-200 text-[11px]">
                      {Number(station.latitude).toFixed(4)}, {Number(station.longitude).toFixed(4)}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] text-sage-400 block">Sightings Logged</span>
                    <span className="font-mono text-emerald-400 font-bold flex items-center space-x-1">
                      <Eye className="w-3 h-3 text-emerald-400" />
                      <span>{station.total_sightings} logs</span>
                    </span>
                  </div>
                </div>

                {station.last_seen_timestamp && (
                  <p className="text-[10px] text-sage-500 truncate">
                    Last activity: {new Date(station.last_seen_timestamp).toLocaleString()}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
