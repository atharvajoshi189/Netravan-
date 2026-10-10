import unittest
import os
import datetime
import numpy as np

from src.behavior.movement_predictor import TigerMovementPredictor
from src.occupancy.map_generator import PenchMapGenerator

class TestTigerMovementPredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = TigerMovementPredictor()
        self.map_gen = PenchMapGenerator()

        # 1. Synthetic Tiger with strict sequential pattern:
        # PTR_STN_01 -> PTR_STN_02 -> PTR_STN_03 -> PTR_STN_01 -> PTR_STN_02 -> PTR_STN_03
        base_time = datetime.datetime(2026, 8, 1, 6, 0, 0)
        self.pattern_tiger_sightings = [
            {"station_id": "PTR_STN_01", "latitude": 21.6845, "longitude": 79.2561, "timestamp": (base_time + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")},
            {"station_id": "PTR_STN_02", "latitude": 21.6950, "longitude": 79.2780, "timestamp": (base_time + datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")},
            {"station_id": "PTR_STN_03", "latitude": 21.7120, "longitude": 79.2610, "timestamp": (base_time + datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")},
            {"station_id": "PTR_STN_01", "latitude": 21.6845, "longitude": 79.2561, "timestamp": (base_time + datetime.timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")},
            {"station_id": "PTR_STN_02", "latitude": 21.6950, "longitude": 79.2780, "timestamp": (base_time + datetime.timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")},
            {"station_id": "PTR_STN_03", "latitude": 21.7120, "longitude": 79.2610, "timestamp": (base_time + datetime.timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S")},
        ]

        # 2. Synthetic Tiger with single capture (sparse data edge case)
        self.sparse_tiger_sightings = [
            {"station_id": "PTR_STN_04", "latitude": 21.7340, "longitude": 79.2890, "timestamp": "2026-08-10 08:30:00"}
        ]

        # 3. Synthetic Tiger with strong directional shift toward a buffer village
        self.dispersing_tiger_sightings = [
            {"station_id": "PTR_STN_04", "latitude": 21.7340, "longitude": 79.2890, "timestamp": "2026-08-01 10:00:00"},
            {"station_id": "PTR_STN_05", "latitude": 21.7450, "longitude": 79.3080, "timestamp": "2026-08-03 12:00:00"},
            {"station_id": "PTR_STN_10", "latitude": 21.7820, "longitude": 79.3650, "timestamp": "2026-08-06 14:00:00"},
            {"station_id": "PTR_STN_15", "latitude": 21.7910, "longitude": 79.3710, "timestamp": "2026-08-09 16:00:00"},  # Khawasa Fringe
        ]

    def test_01_markov_transition_dominant_prediction(self):
        """Verify Markov transition model discovers dominant destination for sequential transitions."""
        # Current station is PTR_STN_01 -> Expected next: PTR_STN_02
        pred_stn_01 = self.predictor.predict_next_likely_stations(
            tiger_id="TIGER_PATTERN",
            sightings=self.pattern_tiger_sightings,
            current_station="PTR_STN_01",
            top_k=3
        )
        self.assertTrue(len(pred_stn_01) > 0, "Should return candidate transition stations")
        top_dest, prob = pred_stn_01[0]
        self.assertEqual(top_dest, "PTR_STN_02", f"Expected PTR_STN_02 from PTR_STN_01, got {top_dest}")
        self.assertAlmostEqual(prob, 1.0, places=2)

        # Current station is PTR_STN_02 -> Expected next: PTR_STN_03
        pred_stn_02 = self.predictor.predict_next_likely_stations(
            tiger_id="TIGER_PATTERN",
            sightings=self.pattern_tiger_sightings,
            current_station="PTR_STN_02",
            top_k=3
        )
        self.assertTrue(len(pred_stn_02) > 0)
        self.assertEqual(pred_stn_02[0][0], "PTR_STN_03")

    def test_02_time_weighted_kde_density_near_recent_sightings(self):
        """Verify time-weighted KDE has higher density at recently visited stations."""
        # Create sightings where STN_01 was 60 days ago and STN_03 was yesterday
        now = datetime.datetime.now()
        decay_sightings = [
            {"station_id": "PTR_STN_01", "latitude": 21.6845, "longitude": 79.2561, "timestamp": (now - datetime.timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")},
            {"station_id": "PTR_STN_01", "latitude": 21.6845, "longitude": 79.2561, "timestamp": (now - datetime.timedelta(days=55)).strftime("%Y-%m-%d %H:%M:%S")},
            {"station_id": "PTR_STN_03", "latitude": 21.7120, "longitude": 79.2610, "timestamp": (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")},
            {"station_id": "PTR_STN_03", "latitude": 21.7120, "longitude": 79.2610, "timestamp": (now - datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")},
        ]
        
        heatmap_res = self.predictor.compute_predictive_heatmap(
            tiger_id="TIGER_TIME_TEST",
            sightings=decay_sightings,
            decay_half_life_days=30.0,
            grid_resolution=40
        )
        
        self.assertEqual(heatmap_res["status"], "success")
        self.assertTrue(len(heatmap_res["heatmap_points"]) > 0)
        
        # Peak density should be located closer to recent STN_03 than old STN_01
        peak_lat, peak_lon = heatmap_res["peak_location"]
        dist_to_recent = (peak_lat - 21.7120)**2 + (peak_lon - 79.2610)**2
        dist_to_old = (peak_lat - 21.6845)**2 + (peak_lon - 79.2561)**2
        self.assertLess(dist_to_recent, dist_to_old, "Heatmap peak should be closer to recent sightings")

    def test_03_sparse_data_clean_handling(self):
        """Verify robust non-crashing handling of sparse single-sighting tiger."""
        res = self.predictor.predict_tiger_movement(
            tiger_id="TIGER_SPARSE_01",
            sightings=self.sparse_tiger_sightings
        )
        self.assertEqual(res["status"], "insufficient_data")
        self.assertEqual(res["sighting_count"], 1)
        self.assertEqual(res["current_station"], "PTR_STN_04")
        self.assertEqual(len(res["predicted_next_stations"]), 0)
        self.assertIn("requires >= 2 sightings", res["confidence_note"])
        self.assertIsNotNone(res["peak_location"])

        # Test with empty list
        empty_res = self.predictor.predict_tiger_movement(tiger_id="TIGER_EMPTY", sightings=[])
        self.assertEqual(empty_res["status"], "insufficient_data")
        self.assertEqual(empty_res["sighting_count"], 0)

    def test_04_directional_trend_and_village_convergence(self):
        """Verify directional shift calculation and village approach warning."""
        trend = self.predictor.compute_directional_trend(self.dispersing_tiger_sightings)
        self.assertEqual(trend["status"], "success")
        self.assertGreater(trend["displacement_km"], 2.0)
        self.assertIn(trend["compass_heading"], ["NE", "N", "E"])
        
        # Should detect approach toward Khawasa Village
        approaching = trend.get("approaching_villages", [])
        self.assertTrue(any("Khawasa" in v["village_name"] for v in approaching), "Should flag convergence toward Khawasa Village")

    def test_05_map_generation_with_predictive_layers(self):
        """Verify interactive map generation incorporating predictive heatmap and station layers."""
        sightings_dict = {
            "TIGER_PATTERN": self.pattern_tiger_sightings,
            "TIGER_DISPERSING": self.dispersing_tiger_sightings
        }

        predictions = {}
        for tid, s_list in sightings_dict.items():
            predictions[tid] = self.predictor.predict_tiger_movement(tid, s_list)

        output_map, hrs, overlaps = self.map_gen.generate_interactive_reserve_map(
            tiger_sightings_by_id=sightings_dict,
            output_filename="test_predictive_map.html",
            behavior_predictions=predictions
        )

        self.assertTrue(os.path.exists(output_map), "Output HTML map file should exist")
        with open(output_map, "r", encoding="utf-8") as f:
            html_content = f.read()

        self.assertIn("Predictive Heatmap", html_content, "Map HTML should contain Predictive Heatmap layer")
        self.assertIn("Predicted Next Station", html_content, "Map HTML should contain predicted station markers")

if __name__ == "__main__":
    unittest.main()
