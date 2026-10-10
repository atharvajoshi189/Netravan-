import math
import datetime
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from scipy.stats import gaussian_kde

try:
    from ..occupancy.home_range import HomeRangeAnalyzer
    from ..occupancy.pench_gis_data import PENCH_VILLAGES, PENCH_CAMERA_STATIONS
except ImportError:
    from src.occupancy.home_range import HomeRangeAnalyzer
    from src.occupancy.pench_gis_data import PENCH_VILLAGES, PENCH_CAMERA_STATIONS

class TigerMovementPredictor:
    """
    Offline, CPU-optimized behavioral movement prediction and spatial heatmap generator
    for individual tigers in Pench Tiger Reserve.
    
    Features:
    1. Time-Weighted Kernel Density Estimation (KDE) predictive spatial surface.
    2. Discrete Markov Chain station-to-station transition model.
    3. Recent trajectory and directional trend analysis toward conflict villages.
    4. Resilient sparse-data and zero-variance handling.
    """

    def __init__(self, lat_km_ratio: float = 111.0):
        self.analyzer = HomeRangeAnalyzer(lat_km_ratio=lat_km_ratio)
        self.lat_km = self.analyzer.lat_km
        self.lon_km = self.analyzer.lon_km

        # Station lookup dictionary by ID for quick GPS mapping
        self.station_lookup = {
            stn["station_id"]: stn for stn in PENCH_CAMERA_STATIONS
        }

    # -------------------------------------------------------------------------
    # Helper: Datetime Parser
    # -------------------------------------------------------------------------
    def _parse_timestamp(self, ts: Any) -> Optional[datetime.datetime]:
        """Parse various timestamp representations into a Python datetime."""
        if isinstance(ts, datetime.datetime):
            return ts
        if isinstance(ts, (int, float)):
            try:
                return datetime.datetime.fromtimestamp(ts)
            except Exception:
                return None
        if isinstance(ts, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d-%m-%Y %H:%M:%S"):
                try:
                    return datetime.datetime.strptime(ts.strip(), fmt)
                except ValueError:
                    continue
        return None

    # -------------------------------------------------------------------------
    # A. Time-Weighted Predictive KDE Heatmap
    # -------------------------------------------------------------------------
    def compute_predictive_heatmap(
        self,
        tiger_id: str,
        sightings: List[Dict[str, Any]],
        decay_half_life_days: float = 30.0,
        grid_resolution: int = 40,
        min_bandwidth_km: float = 1.2
    ) -> Dict[str, Any]:
        """
        Computes a time-weighted 2D spatial density surface for a tiger.
        
        Recent sightings are exponentially prioritized over older captures using:
            weight = 2 ^ (-delta_days / decay_half_life_days)
            
        Coordinates are projected into Cartesian kilometer space using HomeRangeAnalyzer,
        smoothed via Gaussian KDE, and converted back to GPS coordinates.
        
        :param tiger_id: Identifier of the target tiger.
        :param sightings: List of sighting records containing 'latitude', 'longitude', and 'timestamp'.
        :param decay_half_life_days: Half-life in days for exponential time decay.
        :param grid_resolution: Number of grid evaluation points along each axis.
        :param min_bandwidth_km: Minimum spatial kernel smoothing bandwidth in kilometers.
        :return: Dict containing 'density_grid', 'lat_grid', 'lon_grid', 'heatmap_points', 'peak_location'.
        """
        if not sightings:
            return {
                "tiger_id": tiger_id,
                "status": "insufficient_data",
                "density_grid": np.zeros((grid_resolution, grid_resolution)),
                "lat_grid": np.array([]),
                "lon_grid": np.array([]),
                "heatmap_points": [],
                "peak_location": (None, None)
            }

        valid_records = []
        parsed_dates = []

        for s in sightings:
            lat = s.get("latitude")
            lon = s.get("longitude")
            if lat is None or lon is None:
                # Attempt to resolve from station_id if available
                stn_id = s.get("station_id")
                if stn_id in self.station_lookup:
                    lat = self.station_lookup[stn_id]["lat"]
                    lon = self.station_lookup[stn_id]["lon"]

            if lat is not None and lon is not None:
                dt = self._parse_timestamp(s.get("timestamp"))
                valid_records.append((float(lat), float(lon), dt))
                if dt:
                    parsed_dates.append(dt)

        if not valid_records:
            return {
                "tiger_id": tiger_id,
                "status": "insufficient_data",
                "density_grid": np.zeros((grid_resolution, grid_resolution)),
                "lat_grid": np.array([]),
                "lon_grid": np.array([]),
                "heatmap_points": [],
                "peak_location": (None, None)
            }

        # 1. Compute time-decay weights
        ref_time = max(parsed_dates) if parsed_dates else datetime.datetime.now()
        lats = []
        lons = []
        weights = []

        for lat, lon, dt in valid_records:
            lats.append(lat)
            lons.append(lon)
            if dt:
                days_diff = max(0.0, (ref_time - dt).total_seconds() / 86400.0)
                # Exponential decay formula: 2^(-delta_t / half_life)
                w = math.pow(2.0, -days_diff / max(1.0, decay_half_life_days))
            else:
                w = 1.0
            weights.append(max(0.05, float(w)))

        weights = np.array(weights, dtype=float)
        weights_sum = np.sum(weights)
        if weights_sum > 0:
            norm_weights = weights / weights_sum
        else:
            norm_weights = np.ones(len(weights)) / len(weights)

        # 2. Convert coordinates to local Cartesian (x, y) km
        xy_pts = [self.analyzer.latlon_to_xy_km(lat, lon) for lat, lon in zip(lats, lons)]
        xs = np.array([p[0] for p in xy_pts], dtype=float)
        ys = np.array([p[1] for p in xy_pts], dtype=float)

        # 3. Grid envelope definition (Pench landscape boundary or padded tiger bbox)
        padding_km = 6.0
        x_min, x_max = float(np.min(xs) - padding_km), float(np.max(xs) + padding_km)
        y_min, y_max = float(np.min(ys) - padding_km), float(np.max(ys) + padding_km)

        # Ensure minimal bounding span
        if x_max - x_min < 8.0:
            cx = (x_min + x_max) / 2.0
            x_min, x_max = cx - 4.0, cx + 4.0
        if y_max - y_min < 8.0:
            cy = (y_min + y_max) / 2.0
            y_min, y_max = cy - 4.0, cy + 4.0

        grid_x = np.linspace(x_min, x_max, grid_resolution)
        grid_y = np.linspace(y_min, y_max, grid_resolution)
        mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)
        eval_pts = np.vstack([mesh_x.ravel(), mesh_y.ravel()])

        # 4. Density estimation with singularity safeguards
        # Add tiny synthetic jitter if all points are collinear or singular
        unique_xy = np.unique(np.column_stack((xs, ys)), axis=0)
        if len(unique_xy) < 3 or np.var(xs) < 1e-4 or np.var(ys) < 1e-4:
            # Manual weighted radial basis kernel for sparse / single-station records
            bandwidth_sq = max(min_bandwidth_km ** 2, 4.0)
            density = np.zeros(eval_pts.shape[1], dtype=float)
            for i in range(len(xs)):
                dx = eval_pts[0] - xs[i]
                dy = eval_pts[1] - ys[i]
                dist_sq = dx * dx + dy * dy
                density += norm_weights[i] * np.exp(-dist_sq / (2.0 * bandwidth_sq))
        else:
            try:
                kde = gaussian_kde(np.vstack([xs, ys]), weights=norm_weights)
                # Ensure bandwidth is not excessively narrow
                kde.set_bandwidth(bw_method=max(kde.factor, 0.45))
                density = kde(eval_pts)
            except Exception:
                # Fallback manual kernel on numerical exception
                bandwidth_sq = 4.0
                density = np.zeros(eval_pts.shape[1], dtype=float)
                for i in range(len(xs)):
                    dist_sq = (eval_pts[0] - xs[i]) ** 2 + (eval_pts[1] - ys[i]) ** 2
                    density += norm_weights[i] * np.exp(-dist_sq / (2.0 * bandwidth_sq))

        density_grid = density.reshape((grid_resolution, grid_resolution))
        max_d = float(np.max(density_grid))
        if max_d > 0:
            density_norm = density_grid / max_d
        else:
            density_norm = density_grid

        # 5. Convert grid back to GPS (Lat, Lon) coordinates
        lat_grid = np.zeros((grid_resolution, grid_resolution))
        lon_grid = np.zeros((grid_resolution, grid_resolution))
        heatmap_points = []

        for i in range(grid_resolution):
            for j in range(grid_resolution):
                g_lat, g_lon = self.analyzer.xy_km_to_latlon(grid_x[j], grid_y[i])
                lat_grid[i, j] = g_lat
                lon_grid[i, j] = g_lon
                val = float(density_norm[i, j])
                if val >= 0.08:  # Filter near-zero tails to keep heatmap lightweight
                    heatmap_points.append([round(g_lat, 5), round(g_lon, 5), round(val, 3)])

        # Determine peak location
        max_idx = np.unravel_index(np.argmax(density_grid), density_grid.shape)
        peak_lat = float(lat_grid[max_idx])
        peak_lon = float(lon_grid[max_idx])

        return {
            "tiger_id": tiger_id,
            "status": "success",
            "density_grid": density_norm,
            "lat_grid": lat_grid,
            "lon_grid": lon_grid,
            "heatmap_points": heatmap_points,
            "peak_location": (round(peak_lat, 5), round(peak_lon, 5)),
            "sighting_count": len(valid_records),
            "effective_weights": weights.tolist()
        }

    # -------------------------------------------------------------------------
    # B. Station-to-Station Markov Transition Model
    # -------------------------------------------------------------------------
    def build_transition_matrix(
        self,
        sightings: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Constructs a Markov transition probability matrix from chronological station sightings.
        
        :param sightings: List of sighting records for a specific tiger.
        :return: Nested dictionary mapping station_from -> {station_to: probability}
        """
        # Sort sightings chronologically
        sorted_sightings = []
        for s in sightings:
            stn = s.get("station_id")
            ts = self._parse_timestamp(s.get("timestamp"))
            if stn:
                sorted_sightings.append((ts if ts else datetime.datetime.min, stn))

        sorted_sightings.sort(key=lambda x: x[0])
        
        transition_counts: Dict[str, Dict[str, int]] = {}
        
        for idx in range(len(sorted_sightings) - 1):
            curr_stn = sorted_sightings[idx][1]
            next_stn = sorted_sightings[idx + 1][1]

            if curr_stn not in transition_counts:
                transition_counts[curr_stn] = {}
            transition_counts[curr_stn][next_stn] = transition_counts[curr_stn].get(next_stn, 0) + 1

        # Normalize into probabilities
        transition_probs: Dict[str, Dict[str, float]] = {}
        for stn_from, dest_map in transition_counts.items():
            total_visits = sum(dest_map.values())
            transition_probs[stn_from] = {
                stn_to: round(count / total_visits, 4) for stn_to, count in dest_map.items()
            }

        return transition_probs

    def predict_next_likely_stations(
        self,
        tiger_id: str,
        sightings: List[Dict[str, Any]],
        current_station: Optional[str] = None,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Predicts top-K most probable next camera stations based on historical transitions.
        
        If no explicit current station is supplied, the tiger's most recent sighting station is used.
        If transition history from current_station is unavailable, falls back to proximity-informed
        historical station frequencies.
        
        :param tiger_id: Target tiger identifier.
        :param sightings: Historical sighting records.
        :param current_station: Optional starting station ID.
        :param top_k: Maximum number of candidate stations to return.
        :return: List of (station_id, probability) tuples.
        """
        if not sightings:
            return []

        # Sort sightings by timestamp to find last observed station
        sorted_sightings = []
        for s in sightings:
            stn = s.get("station_id")
            ts = self._parse_timestamp(s.get("timestamp"))
            if stn:
                sorted_sightings.append((ts if ts else datetime.datetime.min, stn))

        if not sorted_sightings:
            return []

        sorted_sightings.sort(key=lambda x: x[0])

        if current_station is None:
            current_station = sorted_sightings[-1][1]

        # 1. Check empirical Markov transitions
        transition_matrix = self.build_transition_matrix(sightings)
        
        if current_station in transition_matrix and transition_matrix[current_station]:
            dest_probs = transition_matrix[current_station]
            sorted_candidates = sorted(dest_probs.items(), key=lambda x: x[1], reverse=True)
            return sorted_candidates[:top_k]

        # 2. Fallback for sparse transitions: Frequency of other visited stations
        if len(sorted_sightings) >= 2:
            stn_counts: Dict[str, int] = {}
            for _, stn in sorted_sightings:
                if stn != current_station:
                    stn_counts[stn] = stn_counts.get(stn, 0) + 1

            if stn_counts:
                total = sum(stn_counts.values())
                ranked = sorted(
                    [(stn, round(cnt / total, 4)) for stn, cnt in stn_counts.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                return ranked[:top_k]

        return []

    # -------------------------------------------------------------------------
    # C. Directional Trend & Conflict Village Convergence
    # -------------------------------------------------------------------------
    def compute_directional_trend(
        self,
        sightings: List[Dict[str, Any]],
        recent_window_size: int = 3
    ) -> Dict[str, Any]:
        """
        Calculates recent directional shift vector using sliding-window centroids.
        Evaluates whether movement trajectory converges toward any human settlement in PENCH_VILLAGES.
        
        :param sightings: Historical sightings for the tiger.
        :param recent_window_size: Number of recent captures to construct current vector.
        :return: Dict containing 'displacement_km', 'compass_heading', 'vector_xy_km', 'approaching_villages'.
        """
        valid = []
        for s in sightings:
            lat = s.get("latitude")
            lon = s.get("longitude")
            stn_id = s.get("station_id")
            if (lat is None or lon is None) and stn_id in self.station_lookup:
                lat = self.station_lookup[stn_id]["lat"]
                lon = self.station_lookup[stn_id]["lon"]

            if lat is not None and lon is not None:
                ts = self._parse_timestamp(s.get("timestamp"))
                valid.append((ts if ts else datetime.datetime.min, float(lat), float(lon), stn_id))

        if len(valid) < 2:
            return {
                "status": "insufficient_data",
                "displacement_km": 0.0,
                "compass_heading": "STATIONARY",
                "vector_xy_km": (0.0, 0.0),
                "approaching_villages": []
            }

        valid.sort(key=lambda x: x[0])

        # Separate baseline history vs recent window
        if len(valid) >= 4:
            recent_pts = valid[-recent_window_size:]
            past_pts = valid[:-recent_window_size] if len(valid) > recent_window_size else valid[:2]
        else:
            recent_pts = valid[1:]
            past_pts = valid[:1]

        # Compute baseline and recent centroids
        base_lat = float(np.mean([p[1] for p in past_pts]))
        base_lon = float(np.mean([p[2] for p in past_pts]))
        rec_lat = float(np.mean([p[1] for p in recent_pts]))
        rec_lon = float(np.mean([p[2] for p in recent_pts]))

        # Calculate Cartesian vector in km
        base_x, base_y = self.analyzer.latlon_to_xy_km(base_lat, base_lon)
        rec_x, rec_y = self.analyzer.latlon_to_xy_km(rec_lat, rec_lon)
        dx = round(rec_x - base_x, 2)
        dy = round(rec_y - base_y, 2)
        displacement_km = round(math.hypot(dx, dy), 2)

        # Compass heading
        compass_heading = self._calculate_compass_heading(dx, dy)

        # Check convergence with vulnerable villages
        approaching_villages = []
        if displacement_km >= 0.5:
            for vil in PENCH_VILLAGES:
                v_lat, v_lon = vil["lat"], vil["lon"]
                vx, vy = self.analyzer.latlon_to_xy_km(v_lat, v_lon)
                
                dist_base = math.hypot(vx - base_x, vy - base_y)
                dist_recent = math.hypot(vx - rec_x, vy - rec_y)
                delta_d = dist_base - dist_recent

                if delta_d > 0.4 and dist_recent <= 4.0:
                    approaching_villages.append({
                        "village_id": vil["village_id"],
                        "village_name": vil["name"],
                        "current_distance_km": round(dist_recent, 2),
                        "distance_closed_km": round(delta_d, 2),
                        "risk_level": vil["risk_level"]
                    })

        return {
            "status": "success",
            "baseline_centroid": (round(base_lat, 5), round(base_lon, 5)),
            "recent_centroid": (round(rec_lat, 5), round(rec_lon, 5)),
            "vector_xy_km": (dx, dy),
            "displacement_km": displacement_km,
            "compass_heading": compass_heading,
            "approaching_villages": approaching_villages
        }

    def _calculate_compass_heading(self, dx: float, dy: float) -> str:
        """Determines cardinal/intercardinal compass heading from Cartesian delta (dx, dy)."""
        if math.hypot(dx, dy) < 0.3:
            return "STATIONARY"

        # Angle in degrees where 0 = East, 90 = North
        angle_deg = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        
        # Map angle to 8-point compass
        directions = ["E", "NE", "N", "NW", "W", "SW", "S", "SE", "E"]
        idx = int(round(angle_deg / 45.0))
        return directions[idx]

    # -------------------------------------------------------------------------
    # D. Unified Comprehensive Prediction Engine
    # -------------------------------------------------------------------------
    def predict_tiger_movement(
        self,
        tiger_id: str,
        sightings: List[Dict[str, Any]],
        decay_half_life_days: float = 30.0,
        top_k_stations: int = 3
    ) -> Dict[str, Any]:
        """
        Executes end-to-end behavioral analysis and movement prediction for an individual tiger.
        
        Returns:
            Dict containing:
            - status ('success' | 'insufficient_data')
            - confidence_note
            - sighting_count
            - current_station
            - predicted_next_stations: List[(station_id, probability)]
            - directional_trend: Dict
            - heatmap_points: List[[lat, lon, weight]] for Folium HeatMap
            - peak_location: (lat, lon)
        """
        s_count = len(sightings)
        
        if s_count == 0:
            return {
                "tiger_id": tiger_id,
                "status": "insufficient_data",
                "confidence_note": "No sightings recorded for this tiger.",
                "sighting_count": 0,
                "current_station": None,
                "predicted_next_stations": [],
                "directional_trend": {
                    "status": "insufficient_data",
                    "displacement_km": 0.0,
                    "compass_heading": "UNKNOWN",
                    "approaching_villages": []
                },
                "heatmap_points": [],
                "peak_location": (None, None)
            }

        # 1. Compute time-weighted KDE surface
        heatmap_res = self.compute_predictive_heatmap(
            tiger_id=tiger_id,
            sightings=sightings,
            decay_half_life_days=decay_half_life_days
        )

        # 2. Extract current station
        sorted_sightings = []
        for s in sightings:
            stn = s.get("station_id")
            ts = self._parse_timestamp(s.get("timestamp"))
            if stn:
                sorted_sightings.append((ts if ts else datetime.datetime.min, stn))
        sorted_sightings.sort(key=lambda x: x[0])
        current_station = sorted_sightings[-1][1] if sorted_sightings else None

        # 3. Predict next likely stations
        predicted_stations = self.predict_next_likely_stations(
            tiger_id=tiger_id,
            sightings=sightings,
            current_station=current_station,
            top_k=top_k_stations
        )

        # 4. Compute directional trend
        trend = self.compute_directional_trend(sightings)

        # 5. Formulate confidence note
        if s_count == 1:
            status = "insufficient_data"
            confidence_note = "Single sighting only: Heatmap shows radial uncertainty buffer around initial camera station; transition model requires >= 2 sightings."
        elif len(predicted_stations) == 0:
            status = "partial_data"
            confidence_note = f"Observed {s_count} captures across single station ({current_station}). Transition model active once dispersal occurs."
        else:
            status = "success"
            top_stn, top_prob = predicted_stations[0]
            confidence_note = f"High-confidence transition model based on {s_count} chronological captures. Next likely station: {top_stn} ({top_prob * 100:.1f}% probability)."

        return {
            "tiger_id": tiger_id,
            "status": status,
            "confidence_note": confidence_note,
            "sighting_count": s_count,
            "current_station": current_station,
            "predicted_next_stations": predicted_stations,
            "directional_trend": trend,
            "heatmap_points": heatmap_res.get("heatmap_points", []),
            "peak_location": heatmap_res.get("peak_location", (None, None))
        }
