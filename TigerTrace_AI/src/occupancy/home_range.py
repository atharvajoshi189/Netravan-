import numpy as np
from shapely.geometry import MultiPoint, Polygon, Point
from shapely.ops import unary_union
import math

class HomeRangeAnalyzer:
    def __init__(self, lat_km_ratio=111.0):
        """
        Geospatial analyzer for tiger home ranges, centroids, and territorial overlaps.
        At Pench latitude (21.7°N), 1 deg Lat ≈ 111 km, 1 deg Lon ≈ 103.2 km.
        """
        self.lat_km = lat_km_ratio
        self.lon_km = lat_km_ratio * math.cos(math.radians(21.7))

    def latlon_to_xy_km(self, lat, lon, ref_lat=21.60, ref_lon=79.15):
        """Convert Lat/Lon coordinates into local Cartesian KM from Pench origin."""
        x = (lon - ref_lon) * self.lon_km
        y = (lat - ref_lat) * self.lat_km
        return x, y

    def xy_km_to_latlon(self, x, y, ref_lat=21.60, ref_lon=79.15):
        """Convert local Cartesian KM back into Lat/Lon coordinates."""
        lat = ref_lat + (y / self.lat_km)
        lon = ref_lon + (x / self.lon_km)
        return lat, lon

    def calculate_tiger_home_range(self, sightings_records):
        """
        Computes MCP (Minimum Convex Polygon), activity centroid, and estimated area (km²)
        for a given tiger's sightings.
        :param sightings_records: List of dicts with {'latitude', 'longitude', 'timestamp', 'station_id'}
        """
        if not sightings_records:
            return {
                "sighting_count": 0,
                "centroid": (None, None),
                "area_sq_km": 0.0,
                "mcp_polygon_coords": [],
                "stations_used": []
            }

        points = [(r["latitude"], r["longitude"]) for r in sightings_records]
        unique_stations = list(set(r["station_id"] for r in sightings_records))

        # 1. Compute Activity Centroid (mean center)
        mean_lat = float(np.mean([p[0] for p in points]))
        mean_lon = float(np.mean([p[1] for p in points]))

        # 2. Compute Minimum Convex Polygon (MCP)
        if len(points) >= 3:
            # Check if points are collinear
            mp = MultiPoint([(p[1], p[0]) for p in points])  # (lon, lat) for shapely
            hull = mp.convex_hull
            
            if isinstance(hull, Polygon):
                # Polygon coordinates in (lat, lon) for Leaflet/Folium
                poly_coords = [(pt[1], pt[0]) for pt in list(hull.exterior.coords)]
                
                # Compute area in sq km
                xy_points = [self.latlon_to_xy_km(p[0], p[1]) for p in poly_coords]
                xy_poly = Polygon(xy_points)
                area_sq_km = round(xy_poly.area, 2)
            else:
                # 3 collinear points -> buffer around line
                poly_coords = self._create_point_buffer_polygon(mean_lat, mean_lon, buffer_km=1.5)
                area_sq_km = round(math.pi * (1.5 ** 2), 2)
        elif len(points) == 2:
            # 2 points -> buffer around line between 2 stations
            poly_coords = self._create_line_buffer_polygon(points[0], points[1], buffer_km=1.5)
            d_km = math.sqrt((points[0][0] - points[1][0])**2 + (points[0][1] - points[1][1])**2) * 111.0
            area_sq_km = round(d_km * 3.0, 2)
        else:
            # 1 single sighting point -> standard resident patrol radius buffer (2 km)
            poly_coords = self._create_point_buffer_polygon(mean_lat, mean_lon, buffer_km=2.0)
            area_sq_km = round(math.pi * (2.0 ** 2), 2)

        return {
            "sighting_count": len(sightings_records),
            "centroid": (round(mean_lat, 5), round(mean_lon, 5)),
            "area_sq_km": area_sq_km,
            "mcp_polygon_coords": poly_coords,
            "stations_used": unique_stations
        }

    def compute_territorial_overlaps(self, tiger_home_ranges):
        """
        Computes geometric overlaps (collapsing zones) between all pairs of tiger home ranges.
        :param tiger_home_ranges: dict of {tiger_id: home_range_dict}
        """
        overlaps = []
        tiger_ids = list(tiger_home_ranges.keys())

        for i in range(len(tiger_ids)):
            for j in range(i + 1, len(tiger_ids)):
                id1, id2 = tiger_ids[i], tiger_ids[j]
                hr1, hr2 = tiger_home_ranges[id1], tiger_home_ranges[id2]

                coords1 = hr1.get("mcp_polygon_coords", [])
                coords2 = hr2.get("mcp_polygon_coords", [])

                if len(coords1) >= 3 and len(coords2) >= 3:
                    # Shapely expects (lon, lat)
                    p1 = Polygon([(c[1], c[0]) for c in coords1])
                    p2 = Polygon([(c[1], c[0]) for c in coords2])

                    if p1.intersects(p2):
                        intersection = p1.intersection(p2)
                        if isinstance(intersection, Polygon) and not intersection.is_empty:
                            inter_coords = [(pt[1], pt[0]) for pt in list(intersection.exterior.coords)]
                            # Area calculation
                            xy_points = [self.latlon_to_xy_km(c[0], c[1]) for c in inter_coords]
                            inter_area = round(Polygon(xy_points).area, 2)
                            
                            if inter_area > 0.1:
                                overlaps.append({
                                    "tiger_1": id1,
                                    "tiger_2": id2,
                                    "overlap_area_sq_km": inter_area,
                                    "overlap_coords": inter_coords,
                                    "conflict_risk": "HIGH" if inter_area > 5.0 else "MODERATE"
                                })

        return overlaps

    def _create_point_buffer_polygon(self, lat, lon, buffer_km=2.0, num_pts=16):
        """Generates a circular polygon around a single point."""
        coords = []
        for i in range(num_pts):
            theta = 2.0 * math.pi * (i / num_pts)
            dx = buffer_km * math.cos(theta)
            dy = buffer_km * math.sin(theta)
            p_lat, p_lon = self.xy_km_to_latlon(dx, dy, ref_lat=lat, ref_lon=lon)
            coords.append((round(p_lat, 5), round(p_lon, 5)))
        coords.append(coords[0])
        return coords

    def _create_line_buffer_polygon(self, p1, p2, buffer_km=1.5):
        """Generates an expanded capsule polygon around two points."""
        poly1 = self._create_point_buffer_polygon(p1[0], p1[1], buffer_km=buffer_km, num_pts=8)
        poly2 = self._create_point_buffer_polygon(p2[0], p2[1], buffer_km=buffer_km, num_pts=8)
        combined = unary_union([Polygon([(c[1], c[0]) for c in poly1]), Polygon([(c[1], c[0]) for c in poly2])])
        hull = combined.convex_hull
        return [(pt[1], pt[0]) for pt in list(hull.exterior.coords)]
