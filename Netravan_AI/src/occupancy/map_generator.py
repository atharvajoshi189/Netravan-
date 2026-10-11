import os
from typing import Optional, Dict, Any, List
import folium
from folium import plugins
from .pench_gis_data import PENCH_CORE_BOUNDARY, PENCH_BUFFER_BOUNDARY, PENCH_VILLAGES, PENCH_CAMERA_STATIONS
from .home_range import HomeRangeAnalyzer

# Distinct color palette for individual tigers
TIGER_COLORS = {
    "BAJIRAO": "#2ecc71",         # Emerald Green
    "T15_COLLARWALI": "#ff7f0e",  # Vibrant Orange
    "T40_PATDEV": "#e74c3c",      # Crimson Red
    "T_74_L_MARK": "#9b59b6",     # Amethyst Purple
    "SWASTIK": "#3498db",         # Ocean Blue
    "KARMAJHIRI_CORE_TIGERS": "#e67e22", # Amber
    "PTR_T_007": "#1abc9c",       # Turquoise
    "PTR_T_008": "#f1c40f",       # Gold
}
DEFAULT_TIGER_COLOR = "#00bcd4"   # Cyan/Teal for new individuals

class PenchMapGenerator:
    def __init__(self, output_dir=None):
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "outputs", "occupancy_maps")
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.analyzer = HomeRangeAnalyzer()
        self.station_lookup = {stn["station_id"]: stn for stn in PENCH_CAMERA_STATIONS}

    def add_predictive_heatmap_layer(
        self,
        folium_map: folium.Map,
        tiger_id: str,
        heatmap_points: List[List[float]],
        predicted_stations: Optional[List[tuple]] = None,
        directional_trend: Optional[Dict[str, Any]] = None
    ) -> folium.FeatureGroup:
        """
        Adds a toggleable predictive density heatmap and next-likely-station markers for an individual tiger.
        """
        layer_name = f"🔮 Predictive Heatmap: {tiger_id}"
        pred_group = folium.FeatureGroup(name=layer_name, show=False)

        # 1. Overlay HeatMap surface if data points are available
        if heatmap_points:
            plugins.HeatMap(
                data=heatmap_points,
                radius=28,
                blur=20,
                min_opacity=0.35,
                gradient={
                    0.2: '#00ffff',   # Electric Cyan (low density)
                    0.45: '#2ecc71',  # Forest Green
                    0.7: '#f39c12',   # Amber Orange
                    0.9: '#e74c3c',   # Crimson Red
                    1.0: '#ff007f'    # Hot Magenta Peak
                }
            ).add_to(pred_group)

        # 2. Predicted Next-Likely Camera Stations
        if predicted_stations:
            for rank, (stn_id, prob) in enumerate(predicted_stations, 1):
                stn_info = self.station_lookup.get(stn_id)
                if stn_info:
                    stn_lat, stn_lon = stn_info["lat"], stn_info["lon"]
                    pct = round(prob * 100, 1)

                    # Distinct purple-gold target marker
                    folium.Marker(
                        location=[stn_lat, stn_lon],
                        icon=folium.Icon(color="purple", icon="bullseye", prefix="fa"),
                        tooltip=f"🎯 [{tiger_id}] Predicted Next Station #{rank}: {stn_id} ({pct}%)",
                        popup=f"""
                        <div style='font-family: Arial, sans-serif; width: 230px; line-height:1.4;'>
                            <div style='background:#8e44ad; color:#fff; padding:6px 10px; border-radius:6px 6px 0 0; margin:-10px -10px 8px -10px; font-weight:bold;'>
                                🎯 Predicted Station Transition
                            </div>
                            <p style='margin:3px 0;'><b>Tiger:</b> <span style='color:#8e44ad; font-weight:bold;'>{tiger_id}</span></p>
                            <p style='margin:3px 0;'><b>Station:</b> {stn_id} ({stn_info.get('range', 'Unknown')})</p>
                            <p style='margin:3px 0;'><b>Transition Probability:</b> <span style='color:#27ae60; font-weight:bold; font-size:14px;'>{pct}%</span> (Rank #{rank})</p>
                            <p style='font-size:11px; color:#666; margin-top:6px;'>Estimated by discrete Markov movement model</p>
                        </div>
                        """
                    ).add_to(pred_group)

        # 3. Directional Trajectory Marker if available
        if directional_trend and directional_trend.get("status") == "success":
            rec_lat, rec_lon = directional_trend.get("recent_centroid", (None, None))
            heading = directional_trend.get("compass_heading", "STATIONARY")
            disp_km = directional_trend.get("displacement_km", 0.0)
            if rec_lat and rec_lon and disp_km >= 0.5:
                approaching = directional_trend.get("approaching_villages", [])
                appr_str = ", ".join([v["village_name"] for v in approaching]) if approaching else "Interior Corridor"
                folium.Marker(
                    location=[rec_lat, rec_lon],
                    icon=folium.Icon(color="darkpurple", icon="location-arrow", prefix="fa"),
                    tooltip=f"🧭 [{tiger_id}] Directional Trend: {heading} ({disp_km} km)",
                    popup=f"""
                    <div style='font-family: Arial, sans-serif; width: 220px; line-height:1.4;'>
                        <div style='background:#4a235a; color:#fff; padding:6px 10px; border-radius:6px 6px 0 0; margin:-10px -10px 8px -10px; font-weight:bold;'>
                            🧭 Recent Trajectory Vector
                        </div>
                        <p style='margin:3px 0;'><b>Tiger:</b> {tiger_id}</p>
                        <p style='margin:3px 0;'><b>Heading:</b> <span style='font-weight:bold; color:#e67e22;'>{heading}</span></p>
                        <p style='margin:3px 0;'><b>Displacement:</b> {disp_km} km</p>
                        <p style='margin:3px 0;'><b>Converging Toward:</b> <span style='color:#c0392b;'>{appr_str}</span></p>
                    </div>
                    """
                ).add_to(pred_group)

        pred_group.add_to(folium_map)
        return pred_group

    def generate_interactive_reserve_map(
        self,
        tiger_sightings_by_id: Dict[str, List[Dict[str, Any]]],
        output_filename: str = "pench_tiger_occupancy_map.html",
        behavior_predictions: Optional[Dict[str, Any]] = None,
        recent_batch_sightings: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Generates a comprehensive interactive Folium map of Pench Tiger Reserve with real street,
        satellite, and terrain tile layers, live batch capture indicators, and trajectory paths.
        """
        # Pench Center Coordinates (approx 21.7350°N, 79.3050°E)
        pench_map = folium.Map(
            location=[21.7350, 79.3050],
            zoom_start=11,
            tiles=None,
            control_scale=True,
            prefer_canvas=True
        )

        # -------------------------------------------------------------
        # Base Map Tile Providers (Street View, Satellite, Topo, Dark)
        # -------------------------------------------------------------
        # 1. Detailed Street Map (OpenStreetMap)
        folium.TileLayer(
            tiles="OpenStreetMap",
            name="🗺️ Detailed Street Map (OpenStreetMap)",
            show=True,
            control=True,
            overlay=False
        ).add_to(pench_map)

        # 2. High-Resolution Satellite View (Esri World Imagery)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="🛰️ High-Res Satellite View (Esri Imagery)",
            show=False,
            control=True,
            overlay=False,
            max_zoom=18
        ).add_to(pench_map)

        # 3. Topographic Forest & Elevation Contours
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Topo",
            name="🌲 Topographic Forest & Terrain (Esri Topo)",
            show=False,
            control=True,
            overlay=False,
            max_zoom=18
        ).add_to(pench_map)

        # 4. Tactical Dark Mode View
        folium.TileLayer(
            tiles="CartoDB dark_matter",
            name="🌙 Tactical Dark Mode (CartoDB)",
            show=False,
            control=True,
            overlay=False
        ).add_to(pench_map)

        # -------------------------------------------------------------
        # 1. Pench Core & Buffer Zone Boundary Polygons
        # -------------------------------------------------------------
        boundary_group = folium.FeatureGroup(name="Reserve Boundaries (Core & Buffer)", show=True)
        
        # Buffer Zone Boundary (Golden outer envelope)
        folium.Polygon(
            locations=PENCH_BUFFER_BOUNDARY,
            color="#f39c12",
            weight=2.5,
            fill=True,
            fill_color="#f9e79f",
            fill_opacity=0.18,
            dash_array="6, 6",
            tooltip="<b>Pench Buffer Zone Boundary</b>",
            popup="<b>Pench Buffer Zone</b><br>Multiple-use outer wildlife corridor & eco-sensitive belt (768 sq km)"
        ).add_to(boundary_group)

        # Core Zone Boundary (Emerald green inviolate critical tiger habitat)
        folium.Polygon(
            locations=PENCH_CORE_BOUNDARY,
            color="#27ae60",
            weight=3.5,
            fill=True,
            fill_color="#2ecc71",
            fill_opacity=0.28,
            tooltip="<b>Pench Critical Tiger Habitat (Core Zone)</b>",
            popup="<b>Pench Critical Tiger Habitat (Core Zone)</b><br>Strictly protected inviolate national park (411 sq km)"
        ).add_to(boundary_group)

        boundary_group.add_to(pench_map)

        # -------------------------------------------------------------
        # 2. Surrounding Villages (Human-Wildlife Conflict Alert Layer)
        # -------------------------------------------------------------
        village_group = folium.FeatureGroup(name="Surrounding Villages & Conflict Buffer", show=True)
        for vil in PENCH_VILLAGES:
            v_lat, v_lon = vil["lat"], vil["lon"]
            v_name = vil["name"]
            risk = vil["risk_level"]
            risk_color = "#e74c3c" if risk in ("HIGH", "CRITICAL") else "#f39c12"
            
            # 1.5 km Conflict Risk Warning Circle
            folium.Circle(
                location=[v_lat, v_lon],
                radius=1500,
                color=risk_color,
                weight=1.5,
                fill=True,
                fill_color=risk_color,
                fill_opacity=0.15,
                dash_array="5, 5"
            ).add_to(village_group)

            # Village Pin Marker
            folium.Marker(
                location=[v_lat, v_lon],
                icon=folium.Icon(color="red" if risk in ("HIGH", "CRITICAL") else "orange", icon="home", prefix="fa"),
                tooltip=f"<b>{v_name}</b> (Risk: {risk})",
                popup=f"""
                <div style='font-family: Arial, sans-serif; width: 210px; line-height:1.4;'>
                    <div style='background:{risk_color}; color:#fff; padding:5px 8px; border-radius:4px; font-weight:bold;'>
                        🏡 {v_name}
                    </div>
                    <p style='margin:6px 0 2px 0;'><b>Conflict Risk:</b> <span style='color:{risk_color}; font-weight:bold;'>{risk}</span></p>
                    <p style='font-size:12px; color:#555; margin:0;'>{vil['description']}</p>
                </div>
                """
            ).add_to(village_group)

        village_group.add_to(pench_map)

        # -------------------------------------------------------------
        # 3. Camera Trap Grid Stations
        # -------------------------------------------------------------
        station_group = folium.FeatureGroup(name="Camera Trap Grid Stations (18)", show=True)
        for stn in PENCH_CAMERA_STATIONS:
            s_lat, s_lon = stn["lat"], stn["lon"]
            s_id = stn["station_id"]
            s_zone = stn["zone"]
            zone_color = "#27ae60" if s_zone == "core" else ("#f39c12" if s_zone == "buffer" else "#e74c3c")
            
            folium.CircleMarker(
                location=[s_lat, s_lon],
                radius=7,
                color="#ffffff",
                weight=2,
                fill=True,
                fill_color=zone_color,
                fill_opacity=0.9,
                tooltip=f"📸 Station: {s_id} ({stn['range']} - {s_zone.upper()})",
                popup=f"""
                <div style='font-family: Arial, sans-serif; width: 190px; line-height:1.4;'>
                    <div style='background:{zone_color}; color:#fff; padding:4px 8px; border-radius:4px; font-weight:bold;'>
                        📸 {s_id}
                    </div>
                    <p style='margin:4px 0 2px 0;'><b>Grid:</b> {stn['grid_id']} | <b>Range:</b> {stn['range']}</p>
                    <p style='margin:2px 0;'><b>Zone:</b> {s_zone.upper()}</p>
                    <p style='margin:2px 0;'><b>Camera:</b> {stn['camera_model']}</p>
                    <p style='font-size:11px; color:#777; margin-top:4px;'>GPS: {s_lat:.4f}°N, {s_lon:.4f}°E</p>
                </div>
                """
            ).add_to(station_group)

        station_group.add_to(pench_map)

        # -------------------------------------------------------------
        # 3.5 LIVE / RECENT BATCH INGESTED SIGHTINGS (Dynamic Highlight)
        # -------------------------------------------------------------
        if recent_batch_sightings:
            recent_group = folium.FeatureGroup(name=f"📸 Recent SD Ingestion Feed ({len(recent_batch_sightings)} Detections)", show=True)
            active_stations_seen = set()

            for item in recent_batch_sightings:
                stn_id = item.get("station_id")
                stn_info = self.station_lookup.get(stn_id)
                if not stn_info:
                    continue

                active_stations_seen.add(stn_id)
                s_lat, s_lon = stn_info["lat"], stn_info["lon"]
                t_id = item.get("tiger_id", "Unknown")
                img_name = item.get("image", item.get("image_name", "Photo"))
                conf = float(item.get("confidence", 0.0))
                dec = item.get("decision", "identified")
                t_color = TIGER_COLORS.get(t_id.upper(), "#f39c12")

                # Radiant Camera Trap Sighting Pin
                folium.Marker(
                    location=[s_lat, s_lon],
                    icon=folium.Icon(color="orange", icon="camera", prefix="fa"),
                    tooltip=f"⚡ [NEW BATCH CAPTURE] {t_id} @ {stn_id} ({conf*100:.0f}%)",
                    popup=f"""
                    <div style='font-family: Arial, sans-serif; width: 220px; line-height:1.4;'>
                        <div style='background:linear-gradient(90deg, #f39c12, #e74c3c); color:#fff; padding:6px 10px; border-radius:6px 6px 0 0; margin:-10px -10px 8px -10px; font-weight:bold;'>
                            📸 Recent SD Ingestion Capture
                        </div>
                        <p style='margin:3px 0;'><b>Identified Tiger:</b> <b style='color:{t_color};'>{t_id}</b></p>
                        <p style='margin:3px 0;'><b>Station:</b> {stn_id} ({stn_info.get('range', 'Pench')})</p>
                        <p style='margin:3px 0;'><b>Match Confidence:</b> <span style='color:#27ae60; font-weight:bold;'>{conf*100:.1f}%</span> ({dec.upper()})</p>
                        <p style='margin:3px 0;'><b>Source Frame:</b> <i>{img_name}</i></p>
                    </div>
                    """
                ).add_to(recent_group)

            # Add radiating pulse circle around active ingested stations
            for astn in active_stations_seen:
                stn_info = self.station_lookup.get(astn)
                if stn_info:
                    folium.Circle(
                        location=[stn_info["lat"], stn_info["lon"]],
                        radius=800,
                        color="#f39c12",
                        weight=3,
                        fill=True,
                        fill_color="#f39c12",
                        fill_opacity=0.35,
                        dash_array="3, 3",
                        tooltip=f"⚡ Active Ingested Station: {astn}"
                    ).add_to(recent_group)

            recent_group.add_to(pench_map)

        # -------------------------------------------------------------
        # 4. Individual Tiger Home Ranges & Movement Trajectory Vectors
        # -------------------------------------------------------------
        tiger_home_ranges = {}
        tiger_layers_group = folium.FeatureGroup(name="Individual Tiger Home Ranges (MCP)", show=True)
        trajectory_group = folium.FeatureGroup(name="🐾 Tiger Movement Trajectory Paths", show=True)

        for tiger_id, sightings in tiger_sightings_by_id.items():
            if not sightings:
                continue

            # Compute Home Range
            hr = self.analyzer.calculate_tiger_home_range(sightings)
            tiger_home_ranges[tiger_id] = hr
            
            t_color = TIGER_COLORS.get(tiger_id.upper(), DEFAULT_TIGER_COLOR)
            mcp_coords = hr.get("mcp_polygon_coords", [])
            centroid_lat, centroid_lon = hr.get("centroid", (None, None))
            area_km = hr.get("area_sq_km", 0.0)
            s_count = hr.get("sighting_count", 0)

            # Draw Home Range Polygon
            if len(mcp_coords) >= 3:
                folium.Polygon(
                    locations=mcp_coords,
                    color=t_color,
                    weight=3,
                    fill=True,
                    fill_color=t_color,
                    fill_opacity=0.22,
                    tooltip=f"<b>🐾 Tiger: {tiger_id}</b> | Area: {area_km} km² ({s_count} sightings)",
                    popup=f"""
                    <div style='font-family: Arial, sans-serif; width: 220px; line-height:1.4;'>
                        <h3 style='margin:0; color:{t_color};'>🐅 {tiger_id}</h3>
                        <hr style='margin:4px 0;'>
                        <p style='margin:3px 0;'><b>Home Range Area:</b> <b style='color:{t_color};'>{area_km} km²</b></p>
                        <p style='margin:3px 0;'><b>Total Camera Sightings:</b> {s_count}</p>
                        <p style='margin:3px 0;'><b>Active Grid Stations:</b> {', '.join(hr['stations_used'][:4])}</p>
                    </div>
                    """
                ).add_to(tiger_layers_group)

            # Draw Activity Centroid Marker
            if centroid_lat and centroid_lon:
                folium.Marker(
                    location=[centroid_lat, centroid_lon],
                    icon=folium.Icon(color="black", icon="paw", prefix="fa"),
                    tooltip=f"🐾 Activity Centroid: {tiger_id}",
                    popup=f"<b>Activity Centroid ({tiger_id})</b><br>Lat: {centroid_lat:.4f}°N, Lon: {centroid_lon:.4f}°E<br>Home Range: {area_km} km²"
                ).add_to(tiger_layers_group)

            # 4.5 Draw Trajectory Polyline connecting stations chronologically
            sorted_s = sorted(sightings, key=lambda x: str(x.get("timestamp", "")))
            seen_locs = []
            for s in sorted_s:
                stn = s.get("station_id")
                stn_info = self.station_lookup.get(stn)
                if stn_info:
                    loc = (stn_info["lat"], stn_info["lon"])
                    if not seen_locs or seen_locs[-1] != loc:
                        seen_locs.append(loc)

            if len(seen_locs) >= 2:
                folium.PolyLine(
                    locations=seen_locs,
                    color=t_color,
                    weight=3.5,
                    opacity=0.85,
                    dash_array="6, 6",
                    tooltip=f"🐾 Trajectory Path: {tiger_id} ({len(seen_locs)} Station Shifts)"
                ).add_to(trajectory_group)

        tiger_layers_group.add_to(pench_map)
        trajectory_group.add_to(pench_map)

        # -------------------------------------------------------------
        # 5. Territorial Overlaps / Collapsing Zones Layer
        # -------------------------------------------------------------
        overlaps = self.analyzer.compute_territorial_overlaps(tiger_home_ranges)
        overlap_group = folium.FeatureGroup(name=f"Territorial Overlap & Conflict Zones ({len(overlaps)})", show=True)

        for ov in overlaps:
            t1, t2 = ov["tiger_1"], ov["tiger_2"]
            ov_area = ov["overlap_area_sq_km"]
            ov_coords = ov["overlap_coords"]
            risk = ov["conflict_risk"]

            folium.Polygon(
                locations=ov_coords,
                color="#e74c3c",
                weight=3,
                dash_array="6, 6",
                fill=True,
                fill_color="#c0392b",
                fill_opacity=0.45,
                tooltip=f"<b>⚠️ Territorial Overlap:</b> {t1} ↔ {t2} ({ov_area} km²)",
                popup=f"""
                <div style='font-family: Arial, sans-serif; width: 230px; line-height:1.4;'>
                    <h4 style='margin:0; color:#c0392b;'>⚠️ Territorial Overlap Zone</h4>
                    <hr style='margin:4px 0;'>
                    <p style='margin:3px 0;'><b>Tigers in Conflict:</b><br>{t1} & {t2}</p>
                    <p style='margin:3px 0;'><b>Overlap Area:</b> {ov_area} km²</p>
                    <p style='margin:3px 0;'><b>Management Signal:</b> {risk} territorial pressure</p>
                </div>
                """
            ).add_to(overlap_group)

        overlap_group.add_to(pench_map)

        # -------------------------------------------------------------
        # 6. Behavioral Movement Predictions & Heatmap Layers
        # -------------------------------------------------------------
        if behavior_predictions:
            for tiger_id, pred in behavior_predictions.items():
                heatmap_pts = pred.get("heatmap_points", [])
                pred_stations = pred.get("predicted_next_stations", [])
                trend = pred.get("directional_trend", None)
                if heatmap_pts or pred_stations:
                    self.add_predictive_heatmap_layer(
                        folium_map=pench_map,
                        tiger_id=tiger_id,
                        heatmap_points=heatmap_pts,
                        predicted_stations=pred_stations,
                        directional_trend=trend
                    )

        # -------------------------------------------------------------
        # 7. Map Controls, Measure & Fullscreen Plugins
        # -------------------------------------------------------------
        folium.LayerControl(position="topright", collapsed=False).add_to(pench_map)
        plugins.Fullscreen(position="topleft").add_to(pench_map)
        plugins.MeasureControl(position="bottomleft", primary_length_unit="kilometers").add_to(pench_map)

        # Inject custom styling for Leaflet controls
        custom_css = """
        <style>
            .leaflet-control-layers {
                background: rgba(13, 26, 18, 0.92) !important;
                color: #f0f7f3 !important;
                border: 1px solid rgba(46, 204, 113, 0.4) !important;
                border-radius: 12px !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
                backdrop-filter: blur(12px) !important;
                padding: 12px 16px !important;
                font-family: 'Inter', Arial, sans-serif !important;
                font-size: 12px !important;
                max-height: 480px !important;
                overflow-y: auto !important;
            }
            .leaflet-control-layers label {
                margin-bottom: 6px !important;
                display: flex !important;
                align-items: center !important;
                gap: 6px !important;
                cursor: pointer !important;
            }
            .leaflet-control-layers-separator {
                border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
                margin: 8px 0 !important;
            }
            .leaflet-bar a {
                background-color: rgba(13, 26, 18, 0.9) !important;
                color: #2ecc71 !important;
                border-color: rgba(46, 204, 113, 0.3) !important;
            }
            .leaflet-bar a:hover {
                background-color: #2ecc71 !important;
                color: #070d09 !important;
            }
        </style>
        """
        pench_map.get_root().html.add_child(folium.Element(custom_css))

        output_path = os.path.join(self.output_dir, output_filename)
        pench_map.save(output_path)
        print(f"[MAP GENERATOR] Interactive Pench Tiger Reserve Occupancy Map saved to:\n  {output_path}")
        return output_path, tiger_home_ranges, overlaps
