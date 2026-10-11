import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AlertRecord } from '../types';
import { Bell, AlertOctagon, AlertTriangle, Info, Download, RefreshCw, Search } from 'lucide-react';

export const AlertCenter: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.getAlerts();
      setAlerts(res.alerts || []);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const filteredAlerts = alerts.filter((a) => {
    const matchesSev = severityFilter === 'ALL' || a.severity === severityFilter;
    const matchesSearch =
      a.tiger_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (a.station_id && a.station_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      a.alert_type.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSev && matchesSearch;
  });

  const downloadJsonBriefing = () => {
    const blob = new Blob([JSON.stringify(filteredAlerts, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tigertrace_alerts_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return {
          bg: 'bg-red-950/60 border-red-500/50 text-red-400',
          icon: <AlertOctagon className="w-4 h-4 text-red-400" />,
        };
      case 'WARNING':
        return {
          bg: 'bg-amber-950/60 border-amber-500/50 text-amber-400',
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
        };
      default:
        return {
          bg: 'bg-blue-950/60 border-blue-500/50 text-blue-400',
          icon: <Info className="w-4 h-4 text-blue-400" />,
        };
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Bell className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl font-bold text-ivory">Wildlife Alerts & Conflict Monitoring</h1>
          </div>
          <p className="text-sm text-sage-300 mt-1">
            Real-time biometric anomalies, corridor displacement triggers & conflict warnings
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-sage-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search tiger, station, type..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-charcoal-900 border border-charcoal-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-ivory placeholder-sage-500 focus:outline-none focus:border-amber-500 w-56"
            />
          </div>

          <div className="flex items-center space-x-1 bg-charcoal-900 border border-charcoal-700 rounded-lg p-1 text-xs">
            {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1 rounded font-medium transition-colors ${
                  severityFilter === sev
                    ? 'bg-forest-800 text-ivory font-bold'
                    : 'text-sage-400 hover:text-ivory'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          <button
            onClick={downloadJsonBriefing}
            disabled={filteredAlerts.length === 0}
            className="px-3 py-1.5 bg-charcoal-900 hover:bg-charcoal-800 border border-charcoal-700 rounded-lg text-xs font-medium text-sage-300 hover:text-ivory transition-colors flex items-center space-x-1.5"
            title="Download Incident Report"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Briefing</span>
          </button>

          <button
            onClick={fetchAlerts}
            disabled={loading}
            className="p-2 bg-charcoal-900 hover:bg-charcoal-800 border border-charcoal-700 rounded-lg text-sage-300 hover:text-ivory transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Alert Stats Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card-glass rounded-xl p-4 flex items-center justify-between border-l-4 border-l-red-500">
          <div>
            <span className="text-xs text-sage-400">Critical Incidents</span>
            <p className="text-2xl font-bold text-red-400 font-mono">
              {alerts.filter((a) => a.severity === 'CRITICAL').length}
            </p>
          </div>
          <AlertOctagon className="w-8 h-8 text-red-500/30" />
        </div>

        <div className="card-glass rounded-xl p-4 flex items-center justify-between border-l-4 border-l-amber-500">
          <div>
            <span className="text-xs text-sage-400">Behavior Warnings</span>
            <p className="text-2xl font-bold text-amber-400 font-mono">
              {alerts.filter((a) => a.severity === 'WARNING').length}
            </p>
          </div>
          <AlertTriangle className="w-8 h-8 text-amber-500/30" />
        </div>

        <div className="card-glass rounded-xl p-4 flex items-center justify-between border-l-4 border-l-blue-500">
          <div>
            <span className="text-xs text-sage-400">Informational Logs</span>
            <p className="text-2xl font-bold text-blue-400 font-mono">
              {alerts.filter((a) => a.severity === 'INFO').length}
            </p>
          </div>
          <Info className="w-8 h-8 text-blue-500/30" />
        </div>
      </div>

      {/* Alert Feed */}
      {loading ? (
        <div className="card-glass rounded-xl p-12 text-center text-sage-400">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm">Fetching active alert logs...</p>
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="card-glass rounded-xl p-12 text-center space-y-3">
          <Bell className="w-10 h-10 text-sage-500 mx-auto" />
          <h3 className="text-base font-semibold text-ivory">No Active Wildlife Alerts</h3>
          <p className="text-xs text-sage-400 max-w-sm mx-auto">
            All camera trap corridors operating within standard baseline activity parameters.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => {
            const badge = getSeverityBadge(alert.severity);
            const confPct = Math.round((alert.confidence_score || 0) * 100);

            return (
              <div
                key={alert.alert_id}
                className="card-glass rounded-xl p-5 border border-charcoal-800 transition-all hover:border-charcoal-700"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                  <div className="flex items-center space-x-3">
                    <span className={`px-2.5 py-1 rounded text-xs font-bold border flex items-center space-x-1.5 ${badge.bg}`}>
                      {badge.icon}
                      <span>{alert.severity}</span>
                    </span>
                    <h3 className="text-base font-bold text-ivory">{alert.alert_type.replace(/_/g, ' ')}</h3>
                  </div>

                  <span className="text-xs text-sage-400 font-mono">
                    {new Date(alert.created_at).toLocaleString()}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs mb-3">
                  <div>
                    <span className="text-sage-400 block text-[10px] uppercase">Tiger Target</span>
                    <span className="font-bold text-amber-400 font-mono">{alert.tiger_id}</span>
                  </div>

                  {alert.station_id && (
                    <div>
                      <span className="text-sage-400 block text-[10px] uppercase">Monitoring Station</span>
                      <span className="font-semibold text-ivory">{alert.station_id}</span>
                    </div>
                  )}

                  <div>
                    <span className="text-sage-400 block text-[10px] uppercase">Model Confidence</span>
                    <span className="font-semibold text-emerald-400 font-mono">{confPct}%</span>
                  </div>
                </div>

                <div className="bg-charcoal-900/60 p-3 rounded-lg border border-charcoal-800 text-xs space-y-1">
                  <p className="text-ivory font-medium">{alert.detected_change}</p>
                  {alert.supporting_evidence && (
                    <p className="text-sage-400 text-[11px]">{alert.supporting_evidence}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
