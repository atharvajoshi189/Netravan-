// TigerTraceAI Web UI TypeScript Interfaces

export interface TelemetryData {
  status: string;
  station_count: number;
  total_tigers: number;
  total_sightings: number;
  pending_reviews: number;
  critical_alerts: number;
  warning_alerts: number;
  quarantined_blanks: number;
  active_cameras_pct: number;
}

export interface HealthData {
  status: string;
  service: string;
  version: string;
  device: string;
  timestamp_utc: string;
  models: Record<string, string>;
  active_models: Record<string, string>;
}

export interface CandidateIdentity {
  tiger_id: string;
  name: string;
  score: number;
  sift_score: number;
  cosine_score: number;
  flank: string;
}

export interface LocationInfo {
  station_id: string;
  range_name: string;
  zone: string;
  latitude: number;
  longitude: number;
}

export interface DetectionBox {
  class_id?: number;
  class_name?: string;
  confidence: number;
  bbox_xyxy?: [number, number, number, number];
  bbox_xywhn?: [number, number, number, number];
}

export interface AnalysisResponse {
  status: string;
  observation_id?: number | null;
  image_name: string;
  image_url?: string;
  crop_url?: string | null;
  is_blank: boolean;
  species: string;
  species_confidence: number;
  identity_status: string;
  assigned_identity?: string | null;
  assigned_name?: string | null;
  top_score: number;
  sift_score: number;
  cosine_score: number;
  flank_side: string;
  candidate_identities: CandidateIdentity[];
  decision_reason: string;
  review_status: string;
  behaviour_estimate?: {
    status: string;
    current_station?: string;
    predicted_next_stations?: Array<[string, number]>;
    directional_trend?: Record<string, any>;
    notes?: string;
    evidence_type?: string;
    prediction_source?: string;
    time_horizon?: string;
    limitations?: string;
    visual_behaviour?: {
      available: boolean;
      status: string;
      message?: string;
      sample_classes?: string[];
    };
    scientific_ethogram?: any;
  } | null;
  location?: LocationInfo;
  timestamp: string;
  model_versions: Record<string, string>;
  image_dimensions?: { width: number; height: number };
  animal_group?: string;
  bbox_xyxy?: [number, number, number, number] | null;
  detections?: DetectionBox[];
  error?: string;
}

export interface HabitatZone {
  name: string;
  center: [number, number];
  radius_meters: number;
  suitability: number;
  features: string;
}

export interface HabitatContext {
  status: string;
  reserve_name: string;
  center: [number, number];
  zoom: number;
  disclaimer: string;
  zones: HabitatZone[];
  chota_dadhiyal_reference?: {
    identity_id: string;
    name: string;
    status: string;
    disclaimer: string;
    approximate_envelope: [number, number][];
  };
}

export interface ObservationRecord {
  observation_id: number;
  image_name: string;
  image_path: string;
  image_url?: string;
  crop_url?: string;
  station_id: string;
  timestamp: string;
  species: string;
  assigned_identity?: string | null;
  assigned_name?: string | null;
  flank_side: string;
  reid_score?: number;
  review_status: string;
  range_name?: string;
  zone?: string;
  latitude?: number;
  longitude?: number;
}

export interface TigerRecord {
  tiger_id: string;
  name: string;
  gender: string;
  flank_side_registered: string;
  first_seen_date?: string;
  last_seen_date?: string;
  status: string;
  reference_crop_path?: string;
  notes?: string;
  sighting_count?: number;
}

export interface ReviewQueueItem {
  review_id: number;
  sighting_id: number;
  image_name: string;
  image_path: string;
  image_url?: string;
  flank_crop_path?: string;
  crop_url?: string;
  station_id: string;
  timestamp: string;
  species: string;
  suggested_tiger_id?: string;
  suggested_name?: string;
  suggested_score?: number;
  query_flank?: string;
  ref_flank?: string;
  sift_inliers?: number;
  geometric_status?: string;
  raw_cosine_sim?: number;
  ref_crop_url?: string;
  status: string;
}

export interface StationRecord {
  station_id: string;
  grid_id: string;
  range_name: string;
  zone: string;
  latitude: number;
  longitude: number;
  is_active: number;
  total_sightings: number;
  last_seen_timestamp?: string;
}

export interface AlertRecord {
  alert_id: number;
  alert_type: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  tiger_id: string;
  station_id?: string;
  detected_change: string;
  supporting_evidence: string;
  confidence_score: number;
  created_at: string;
  is_acknowledged?: number;
}

export interface SpeciesClass {
  canonical_id: number;
  canonical_name: string;
  display_name: string;
  scientific_name: string;
  order: string;
  family: string;
  iucn_status: string;
  diet_category: string;
  tadoba_diet_relevance: string;
  trainable_status: string;
  morphology_notes?: string;
  ir_camera_trap_profile?: string;
}

export interface ModelEntry {
  model_id: string;
  name: string;
  category: string;
  primary_path: string;
  organized_path: string;
  file_size_bytes: number;
  sha256: string;
  architecture: string;
  task: string;
  classes: Record<number, string> | string;
  class_count: number;
  evaluation_status: string;
  compatibility_status: string;
  enabled: boolean;
  notes: string;
}
