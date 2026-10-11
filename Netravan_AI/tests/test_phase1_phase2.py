import unittest
import os
import shutil
import sqlite3
import json

from src.db.schema import init_db, seed_sample_stations, get_connection
from src.ingest.sd_loader import SDCardLoader
from src.blank_filter.triage_detector import CameraTrapTriageDetector
from src.blank_filter.quarantine import QuarantineManager
from src.privacy.human_blur import HumanPrivacyBlurrer
from src.reid.flank_extractor import FlankExtractor
from src.reid.stripe_matcher import StripeReIDMatcher
from src.reid.enrollment import TigerEnrollmentEngine
from src.occupancy.home_range import HomeRangeAnalyzer
from src.occupancy.map_generator import PenchMapGenerator
from src.alerts.deviation_engine import DeviationAlertEngine
from src.pipeline import TigerTracePipeline

class TestTigerTraceFullPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.catalogue_dir = os.path.join(cls.base_dir, "data", "reference_catalogue")
        cls.raw_sd_dir = os.path.join(cls.base_dir, "data", "raw_sd_cards", "SD_CARD_PTR_STN_02")

    def test_01_db_initialization(self):
        """Verify SQLite database schema creation with GIS stations and villages."""
        init_db()
        seed_sample_stations()
        
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        
        expected_tables = ["stations", "villages", "tigers", "sightings", "review_queue", "alerts", "triage_logs"]
        for t in expected_tables:
            self.assertIn(t, tables, f"Table {t} missing from schema")
            
        cur.execute("SELECT COUNT(*) FROM stations;")
        stn_count = cur.fetchone()[0]
        self.assertGreaterEqual(stn_count, 18, "Expected 18 seeded Pench stations")

        cur.execute("SELECT COUNT(*) FROM villages;")
        vil_count = cur.fetchone()[0]
        self.assertGreaterEqual(vil_count, 8, "Expected 8 seeded Pench buffer villages")
        conn.close()

    def test_02_sd_card_ingestion(self):
        """Verify SD card scanner and EXIF timestamp extraction."""
        loader = SDCardLoader(default_station="PTR_STN_02")
        records = loader.scan_sd_card_folder(self.raw_sd_dir)
        self.assertGreater(len(records), 0, "SD Card ingestion returned no records")
        self.assertTrue(all(r["station_id"] == "PTR_STN_02" for r in records))
        self.assertTrue(all("timestamp" in r and len(r["timestamp"]) > 0 for r in records))

    def test_03_stripe_reid_matching(self):
        """Verify HotSpotter SIFT and deep embedding stripe matcher."""
        matcher = StripeReIDMatcher(use_deep_embedding=True)
        img1 = os.path.join(self.raw_sd_dir, "IMG_0101_Bajirao.png")
        
        if os.path.exists(img1):
            res = matcher.compare_flanks(img1, img1, query_flank="left", ref_flank="left")
            self.assertGreaterEqual(res["combined_score"], 0.70, "Self-comparison score should be high")
            self.assertGreater(res["good_matches_count"], 10, "SIFT inliers should be high for identical images")

    def test_04_spatial_home_range_and_overlaps(self):
        """Verify Minimum Convex Polygon (MCP), Centroid, and Overlap calculations."""
        analyzer = HomeRangeAnalyzer()
        sample_sightings = [
            {"station_id": "PTR_STN_01", "latitude": 21.6845, "longitude": 79.2561, "timestamp": "2026-08-10 10:00:00"},
            {"station_id": "PTR_STN_02", "latitude": 21.6950, "longitude": 79.2780, "timestamp": "2026-08-11 11:00:00"},
            {"station_id": "PTR_STN_03", "latitude": 21.7120, "longitude": 79.2610, "timestamp": "2026-08-12 12:00:00"},
        ]
        hr = analyzer.calculate_tiger_home_range(sample_sightings)
        self.assertEqual(hr["sighting_count"], 3)
        self.assertGreater(hr["area_sq_km"], 0.0)
        self.assertIsNotNone(hr["centroid"][0])

    def test_05_map_generation(self):
        """Verify generation of interactive Folium HTML map."""
        map_gen = PenchMapGenerator()
        sample_sightings = {
            "BAJIRAO": [
                {"station_id": "PTR_STN_04", "latitude": 21.7340, "longitude": 79.2890},
                {"station_id": "PTR_STN_05", "latitude": 21.7450, "longitude": 79.3080},
                {"station_id": "PTR_STN_06", "latitude": 21.7280, "longitude": 79.3250},
            ]
        }
        map_path, hrs, overlaps = map_gen.generate_interactive_reserve_map(sample_sightings, "test_map.html")
        self.assertTrue(os.path.exists(map_path))

    def test_06_end_to_end_full_pipeline(self):
        """Verify end-to-end execution of all 4 phases."""
        pipeline = TigerTracePipeline()
        pipeline.seed_reference_catalogue(self.catalogue_dir)
        report = pipeline.process_sd_card_folder(self.raw_sd_dir, batch_id="TEST_RUN_E2E")
        
        self.assertIn("batch_id", report)
        self.assertIn("triage_savings", report)
        self.assertIn("reid_results", report)
        self.assertIn("home_ranges", report)
        self.assertIn("alerts", report)
        self.assertTrue(os.path.exists(report["interactive_map_path"]))

if __name__ == "__main__":
    unittest.main()
