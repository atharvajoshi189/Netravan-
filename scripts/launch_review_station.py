"""
TigerTraceAI — Step 15D: Dedicated Review Station Local Server.

Launches a zero-dependency local HTTP server providing:
- Web Review UI at http://127.0.0.1:8085
- REST API for auto-persisting human review decisions to disk
- Image streaming from isolated staging directory
- Real-time audit metrics (pending, verified, rejected, unknown)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from TigerTrace_AI.src.datasets.gold_standard_builder import GoldStandardBuilder

logger = logging.getLogger("review_station_server")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


class ReviewStationHandler(SimpleHTTPRequestHandler):
    staging_dir: Path
    builder: GoldStandardBuilder

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            ui_path = self.staging_dir / "review_ui" / "index.html"
            self._serve_file(ui_path, "text/html")
            return

        elif path.startswith("/images/"):
            filename = Path(path).name
            img_path = self.staging_dir / "images" / filename
            self._serve_file(img_path, "image/jpeg")
            return

        elif path == "/api/samples":
            self._handle_get_samples()
            return

        elif path == "/api/status":
            self._handle_get_status()
            return

        elif path == "/api/reviews":
            self._handle_get_reviews()
            return

        # Fallback to standard static file serving if within staging_dir
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/save_review":
            self._handle_save_review()
            return

        elif path == "/api/export_yolo":
            self._handle_export_yolo()
            return

        self.send_error(HTTPStatus.NOT_FOUND, f"Endpoint {path} not found")

    def _serve_file(self, filepath: Path, content_type: str):
        if not filepath.exists():
            self.send_error(HTTPStatus.NOT_FOUND, f"File {filepath.name} not found")
            return
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Error reading file: {e}")

    def _send_json(self, data: dict, status: int = HTTPStatus.OK):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _handle_get_samples(self):
        # 1. Staging manifest
        manifest_file = self.staging_dir / "manifests" / "staging_manifest.json"
        if not manifest_file.exists():
            self._send_json({"error": "staging_manifest.json not found"}, HTTPStatus.NOT_FOUND)
            return

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        samples = manifest_data.get("samples", [])

        # 2. Proposals
        proposals_file = self.staging_dir / "provisional_proposals" / "provisional_proposals.json"
        proposals_by_sample = {}
        if proposals_file.exists():
            with open(proposals_file, "r", encoding="utf-8") as f:
                p_data = json.load(f)
            for p in p_data.get("proposals", []):
                proposals_by_sample.setdefault(p["sample_id"], []).append(p)

        # 3. Existing reviews from builder
        self.builder._load_existing_reviews()
        existing_reviews = self.builder.reviews

        enriched_samples = []
        for s in samples:
            s_id = s["sample_id"]
            rev = existing_reviews.get(s_id)
            review_dict = None
            if rev:
                review_dict = {
                    "status": rev.status,
                    "reviewer_id": rev.reviewer_id,
                    "reviewed_at_utc": rev.reviewed_at_utc,
                    "boxes": [
                        {
                            "box_id": b.box_id,
                            "species_name": b.species_name,
                            "canonical_class_id": b.canonical_class_id,
                            "bbox_norm_xywh": b.bbox_norm_xywh,
                            "bbox_pixel_xyxy": b.bbox_pixel_xyxy,
                            "review_action": b.review_action,
                        }
                        for b in rev.boxes
                    ],
                    "notes": rev.notes,
                }

            enriched_samples.append({
                "metadata": s,
                "proposals": proposals_by_sample.get(s_id, []),
                "review": review_dict,
            })

        self._send_json({"total_samples": len(enriched_samples), "samples": enriched_samples})

    def _handle_save_review(self):
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            self._send_json({"error": "Empty request body"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body)

            sample_id = data.get("sample_id")
            reviewer_id = data.get("reviewer_id", "web_reviewer")
            decision = data.get("review_decision", "human_verified")
            boxes = data.get("boxes", [])
            notes = data.get("notes")

            success, err = self.builder.record_human_review(
                sample_id=sample_id,
                reviewer_id=reviewer_id,
                review_decision=decision,
                boxes=boxes,
                notes=notes,
            )

            if not success:
                self._send_json({"success": False, "error": err}, HTTPStatus.BAD_REQUEST)
                return

            saved_rec = self.builder.reviews[sample_id]
            self._send_json({
                "success": True,
                "sample_id": sample_id,
                "status": saved_rec.status,
                "boxes_saved": len(saved_rec.boxes),
            })

        except Exception as e:
            logger.error(f"Failed to save review: {e}")
            self._send_json({"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_get_status(self):
        self.builder._load_existing_reviews()
        total_samples = len(self.builder.manifest_samples)
        reviewed = len(self.builder.reviews)
        verified = sum(1 for r in self.builder.reviews.values() if r.status == "human_verified")
        rejected = sum(1 for r in self.builder.reviews.values() if r.status == "rejected_entirely")
        unknown = sum(1 for r in self.builder.reviews.values() if r.status == "unknown_uncertain")
        verified_boxes = sum(len(r.boxes) for r in self.builder.reviews.values() if r.status == "human_verified")

        self._send_json({
            "total_samples": total_samples,
            "reviewed_samples": reviewed,
            "pending_samples": total_samples - reviewed,
            "verified_samples": verified,
            "rejected_samples": rejected,
            "unknown_samples": unknown,
            "verified_boxes_count": verified_boxes,
        })

    def _handle_get_reviews(self):
        self.builder._load_existing_reviews()
        reviews_data = [
            {
                "sample_id": r.sample_id,
                "status": r.status,
                "reviewer_id": r.reviewer_id,
                "reviewed_at_utc": r.reviewed_at_utc,
                "boxes_count": len(r.boxes),
            }
            for r in self.builder.reviews.values()
        ]
        self._send_json({"total_reviews": len(reviews_data), "reviews": reviews_data})

    def _handle_export_yolo(self):
        try:
            summary = self.builder.export_yolo_detection_ready_dataset()
            self._send_json({"success": True, "summary": summary})
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def run_server(staging_dir: Path, port: int = 8085):
    staging_path = Path(staging_dir).resolve()
    builder = GoldStandardBuilder(staging_dir=staging_path)

    ReviewStationHandler.staging_dir = staging_path
    ReviewStationHandler.builder = builder

    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, ReviewStationHandler)

    print("\n" + "=" * 65)
    print("  TIGERTRACEAI — STEP 15D HUMAN REVIEW STATION RUNNING")
    print("=" * 65)
    print(f"  Local Review URL: http://127.0.0.1:{port}/")
    print(f"  Staging Directory: {staging_path}")
    print(f"  Total Staging Images: {len(builder.manifest_samples)}")
    print(f"  Auto-Persistence: Enabled -> human_verified_annotations.json")
    print("=" * 65)
    print("  Press Ctrl+C to stop the server at any time.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Review station server shut down gracefully.")
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="TigerTraceAI Step 15D Review Station Server")
    parser.add_argument(
        "--staging-dir",
        type=str,
        default="TigerTrace_AI/data/staging_wildlife_pilot",
        help="Path to staging pilot directory",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8085,
        help="Local HTTP port (default: 8085)",
    )
    args = parser.parse_args()
    run_server(staging_dir=Path(args.staging_dir), port=args.port)


if __name__ == "__main__":
    main()
