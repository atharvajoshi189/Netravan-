import {
  TelemetryData,
  HealthData,
  AnalysisResponse,
  ObservationRecord,
  TigerRecord,
  ReviewQueueItem,
  StationRecord,
  AlertRecord,
  SpeciesClass,
  ModelEntry,
  HabitatContext
} from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    let errMsg = `Request failed: ${res.status} ${res.statusText}`;
    try {
      const errObj = await res.json();
      if (errObj.detail) errMsg = errObj.detail;
    } catch {
      // ignore
    }
    throw new Error(errMsg);
  }
  return res.json();
}

export const api = {
  // 1. Health & Telemetry
  getHealth: () => fetchJson<HealthData>(`${API_BASE}/health`),
  getTelemetry: () => fetchJson<TelemetryData>(`${API_BASE}/telemetry`),

  // 2. Observations
  getObservations: (limit: number = 50) =>
    fetchJson<{ status: string; count: number; observations: ObservationRecord[] }>(
      `${API_BASE}/mobile/observations?limit=${limit}`
    ),

  // 3. Tigers
  getTigers: () => fetchJson<TigerRecord[]>(`${API_BASE}/tigers`),

  // 4. Stations
  getStations: () => fetchJson<{ stations: StationRecord[] }>(`${API_BASE}/stations`),

  // 5. Review Queue
  getReviewQueue: async () => {
    const res = await fetchJson<any>(`${API_BASE}/review_queue`);
    if (Array.isArray(res)) {
      return { status: 'success', count: res.length, reviews: res as ReviewQueueItem[] };
    }
    return res as { status: string; count: number; reviews: ReviewQueueItem[] };
  },

  submitReviewAction: (
    reviewId: number,
    action: 'accept' | 'reject' | 'inconclusive',
    reviewerId: string = 'senior_field_officer',
    reason: string = 'Verified stripe pattern in command center'
  ) =>
    fetchJson<{ status: string; message: string; sighting_id: number }>(
      `${API_BASE}/review_queue/${reviewId}/action`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, reviewer_id: reviewerId, reason }),
      }
    ),

  // 6. Alerts
  getAlerts: () =>
    fetchJson<{ status: string; count: number; alerts: AlertRecord[] }>(`${API_BASE}/alerts`),

  // 7. Movement / Behavior
  getBehaviorPredictions: async () => {
    const raw = await fetchJson<any>(`${API_BASE}/behavior_predictions`);
    if (raw && raw.predictions) {
      return raw as {
        status: string;
        tiger_count: number;
        predictions: Record<string, any>;
      };
    }
    return {
      status: 'success',
      tiger_count: Object.keys(raw || {}).length,
      predictions: raw || {},
    };
  },

  // 8. Species Taxonomy
  getSpecies: () =>
    fetchJson<{ taxonomy_version: string; classes: SpeciesClass[] }>(`${API_BASE}/species`),

  // 9. Model Registry
  getModels: () =>
    fetchJson<{ registry_version: string; models: ModelEntry[] }>(`${API_BASE}/models`),

  // 10. Live Image Analysis
  analyzeImage: async (
    file: File,
    stationId?: string,
    lat?: number,
    lon?: number,
    flankHint?: string
  ): Promise<AnalysisResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (stationId) formData.append('station_id', stationId);
    if (lat !== undefined) formData.append('latitude', lat.toString());
    if (lon !== undefined) formData.append('longitude', lon.toString());
    if (flankHint) formData.append('flank_hint', flankHint);

    return fetchJson<AnalysisResponse>(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData,
    });
  },

  // 11. Habitat Context
  getHabitatContext: () =>
    fetchJson<HabitatContext>(`${API_BASE}/habitat/context`),

  // 12. Reserve Official GIS Boundaries and Villages
  getReserveGis: () =>
    fetchJson<{
      status: string;
      core_boundary: [number, number][];
      buffer_boundary: [number, number][];
      villages: {
        village_id: string;
        name: string;
        lat: number;
        lon: number;
        zone: string;
        risk_level: string;
        description: string;
      }[];
      camera_stations: any[];
    }>(`${API_BASE}/reserve/gis`),
};
