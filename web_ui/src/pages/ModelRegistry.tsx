import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ModelEntry } from '../types';
import { Cpu, CheckCircle2, AlertCircle, Clock, ShieldCheck, Filter, Search, Copy, Check } from 'lucide-react';

export const ModelRegistry: React.FC = () => {
  const [models, setModels] = useState<ModelEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      setLoading(true);
      try {
        const res = await api.getModels();
        setModels(res.models || []);
      } catch (err) {
        console.error('Failed to load model registry:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  const handleCopy = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const categories = Array.from(new Set(models.map((m) => m.category))).filter(Boolean);

  const filteredModels = models.filter((m) => {
    const matchesCat = categoryFilter === 'ALL' || m.category === categoryFilter;
    const matchesSearch =
      m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.model_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.architecture.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const getStatusBadge = (status: string, enabled: boolean) => {
    if (enabled && status === 'production_verified') {
      return {
        bg: 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40',
        text: 'Production Active',
        icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
      };
    }
    if (status.includes('external') || status.includes('training')) {
      return {
        bg: 'bg-amber-950/60 text-amber-400 border-amber-500/40',
        text: 'External Training',
        icon: <Clock className="w-3.5 h-3.5 text-amber-400" />,
      };
    }
    return {
      bg: 'bg-blue-950/60 text-blue-400 border-blue-500/40',
      text: status.replace(/_/g, ' '),
      icon: <AlertCircle className="w-3.5 h-3.5 text-blue-400" />,
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-6 h-6 text-emerald-400" />
            <h1 className="text-2xl font-bold text-ivory">AI/ML Model Registry & Diagnostics</h1>
          </div>
          <p className="text-sm text-sage-300 mt-1">
            Verified weight artifacts, SHA-256 cryptographic provenance & 10-stage evaluation gates
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-sage-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search model, architecture..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-charcoal-900 border border-charcoal-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-ivory placeholder-sage-500 focus:outline-none focus:border-emerald-500 w-56"
            />
          </div>

          <div className="flex items-center space-x-2 bg-charcoal-900 border border-charcoal-700 rounded-lg px-3 py-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-sage-400" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-transparent text-ivory focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-charcoal-900">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat} className="bg-charcoal-900">
                  {cat.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Security Governance Notice */}
      <div className="card-glass rounded-xl p-4 border-l-4 border-l-emerald-500 flex items-start space-x-3 text-xs">
        <ShieldCheck className="w-5 h-5 text-emerald-400 mt-0.5 shrink-0" />
        <div className="space-y-1">
          <h4 className="font-bold text-ivory">Evaluation Gate Governance Policy</h4>
          <p className="text-sage-300 leading-relaxed">
            In accordance with Phase C security standards, dynamic runtime model replacement and arbitrary filesystem weight loading are strictly blocked. Promotion of staged models (A, B, C, D) requires meeting all 10 evaluation gates including cross-species confusion analysis and CPU latency validation.
          </p>
        </div>
      </div>

      {/* Model Cards / Inventory */}
      {loading ? (
        <div className="card-glass rounded-xl p-12 text-center text-sage-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm">Reading model manifest registry...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredModels.map((m) => {
            const badge = getStatusBadge(m.evaluation_status, m.enabled);
            const sizeMb = (m.file_size_bytes / (1024 * 1024)).toFixed(1);

            return (
              <div
                key={m.model_id}
                className="card-glass rounded-xl p-5 border border-charcoal-800 space-y-4"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-base font-bold text-ivory">{m.name}</h3>
                      <span className="font-mono text-xs text-sage-400">({m.model_id})</span>
                    </div>
                    <p className="text-xs text-sage-300 mt-0.5">
                      Architecture: <span className="font-semibold text-ivory">{m.architecture}</span> • Task:{' '}
                      <span className="font-semibold text-ivory">{m.task}</span>
                    </p>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className={`px-2.5 py-1 rounded text-xs font-semibold border flex items-center space-x-1.5 ${badge.bg}`}>
                      {badge.icon}
                      <span>{badge.text}</span>
                    </span>

                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                        m.enabled
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : 'bg-charcoal-800 text-sage-400 border border-charcoal-700'
                      }`}
                    >
                      {m.enabled ? 'INFERENCE ACTIVE' : 'DISABLED'}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-charcoal-950/70 p-3 rounded-lg border border-charcoal-800 text-xs">
                  <div>
                    <span className="text-[10px] text-sage-400 block uppercase">Primary Path</span>
                    <span className="font-mono text-sage-200 text-[11px] truncate block" title={m.primary_path}>
                      {m.primary_path}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] text-sage-400 block uppercase">Artifact Size</span>
                    <span className="font-mono text-sage-200 text-[11px]">
                      {m.file_size_bytes > 0 ? `${sizeMb} MB` : 'Remote artifact'}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] text-sage-400 block uppercase">Taxonomy / Classes</span>
                    <span className="font-mono text-sage-200 text-[11px]">
                      {m.class_count} registered classes
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] text-sage-400 block uppercase">Compatibility</span>
                    <span className="font-mono text-emerald-400 text-[11px]">
                      {m.compatibility_status}
                    </span>
                  </div>
                </div>

                {/* Cryptographic SHA-256 */}
                {m.sha256 && (
                  <div className="flex items-center justify-between bg-charcoal-900/60 px-3 py-2 rounded border border-charcoal-800 text-xs font-mono">
                    <div className="flex items-center space-x-2 truncate">
                      <span className="text-sage-400 text-[10px]">SHA-256:</span>
                      <span className="text-sage-200 text-[11px] truncate">{m.sha256}</span>
                    </div>
                    <button
                      onClick={() => handleCopy(m.sha256)}
                      className="ml-2 text-sage-400 hover:text-ivory shrink-0"
                      title="Copy Checksum"
                    >
                      {copiedHash === m.sha256 ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                )}

                {/* Notes and Constraints */}
                <div className="text-[11px] text-sage-400 italic">
                  Note: {m.notes}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
