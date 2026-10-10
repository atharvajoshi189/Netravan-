import os
import json
import time
import uuid

from .config import ALERT_PHONE_NUMBER, GAMMU_CONFIG_PATH, SMS_DRY_RUN, SMS_ENABLED_ALERT_TYPES
from .db.schema import get_connection, init_db, seed_sample_stations
from .ingest.sd_loader import SDCardLoader
from .blank_filter.triage_detector import CameraTrapTriageDetector
from .blank_filter.quarantine import QuarantineManager
from .privacy.human_blur import HumanPrivacyBlurrer
from .reid.flank_extractor import FlankExtractor
from .reid.enrollment import TigerEnrollmentEngine
from .occupancy.home_range import HomeRangeAnalyzer
from .occupancy.map_generator import PenchMapGenerator
from .alerts.deviation_engine import DeviationAlertEngine
from .alerts.sms_notifier import SMSNotifier
from .behavior.movement_predictor import TigerMovementPredictor

class TigerTracePipeline:
    def __init__(self, db_path=None, enable_sms_alerts=False, alert_phone_number=None, gammu_config_path=None, sms_dry_run=None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. Initialize Database
        init_db()
        seed_sample_stations()
        self.conn = get_connection()

        # 2. Subsystems (Phases 1-4 + Behavioral Intelligence)
        self.sd_loader = SDCardLoader()
        self.triage_detector = CameraTrapTriageDetector(confidence_threshold=0.20)
        self.quarantine_mgr = QuarantineManager()
        self.privacy_blurrer = HumanPrivacyBlurrer()
        self.flank_extractor = FlankExtractor()
        self.enrollment_engine = TigerEnrollmentEngine(self.conn)
        self.home_range_analyzer = HomeRangeAnalyzer()
        self.map_generator = PenchMapGenerator()
        self.movement_predictor = TigerMovementPredictor()

        sms_enabled = bool(enable_sms_alerts)
        sms_phone_number = (alert_phone_number or ALERT_PHONE_NUMBER).strip()
        sms_config_path = gammu_config_path or GAMMU_CONFIG_PATH
        sms_dry_run_flag = SMS_DRY_RUN if sms_dry_run is None else bool(sms_dry_run)
        self.sms_notifier = None
        sms_callback = None

        if sms_enabled:
            if sms_phone_number:
                self.sms_notifier = SMSNotifier(
                    phone_number=sms_phone_number,
                    gammu_config_path=sms_config_path,
                    dry_run=sms_dry_run_flag,
                )
                sms_callback = self.sms_notifier.send_alert_sms
            else:
                print("[SMS] SMS alerts enabled but ALERT_PHONE_NUMBER is empty; SMS notifications disabled.")

        self.alert_engine = DeviationAlertEngine(
            self.conn,
            on_alert_raised=sms_callback,
            sms_enabled_alert_types=SMS_ENABLED_ALERT_TYPES,
        )

        # Output Directories
        self.flank_crops_dir = os.path.join(self.base_dir, "data", "tiger_crops")
        self.blurred_dir = os.path.join(self.base_dir, "data", "privacy_blurred")
        self.maps_dir = os.path.join(self.base_dir, "data", "outputs", "occupancy_maps")
        self.alerts_dir = os.path.join(self.base_dir, "data", "outputs", "alert_reports")
        
        os.makedirs(self.flank_crops_dir, exist_ok=True)
        os.makedirs(self.blurred_dir, exist_ok=True)
        os.makedirs(self.maps_dir, exist_ok=True)
        os.makedirs(self.alerts_dir, exist_ok=True)

    def configure_sms_alerts(self, enable_sms_alerts=False, alert_phone_number=None, gammu_config_path=None, sms_dry_run=None):
        sms_phone_number = (alert_phone_number or ALERT_PHONE_NUMBER).strip()
        sms_config_path = gammu_config_path or GAMMU_CONFIG_PATH
        sms_dry_run_flag = SMS_DRY_RUN if sms_dry_run is None else bool(sms_dry_run)

        if enable_sms_alerts and sms_phone_number:
            self.sms_notifier = SMSNotifier(
                phone_number=sms_phone_number,
                gammu_config_path=sms_config_path,
                dry_run=sms_dry_run_flag,
            )
            self.alert_engine.on_alert_raised = self.sms_notifier.send_alert_sms
        else:
            self.sms_notifier = None
            self.alert_engine.on_alert_raised = None

    def seed_reference_catalogue(self, catalogue_folder):
        """Seed existing known tiger flank profiles into the catalogue."""
        return self.enrollment_engine.seed_initial_catalogue_from_folder(catalogue_folder)

    def process_sd_card_folder(
        self,
        raw_folder_path,
        batch_id=None,
        generate_maps=True,
        generate_alerts=True,
        enable_behavior_prediction=True
    ):
        """
        Executes full end-to-end processing:
        Phase 1: Ingestion, Triage Quarantine & Human Privacy Blur
        Phase 2: Flank Stripe Re-ID, Auto-Enrollment & SQLite Persistence
        Phase 3: Spatial Occupancy (MCP), Predictive Heatmaps & Interactive Folium Reserve Map
        Phase 4: Behavioral Deviation & Human-Wildlife Conflict Alerting Engine
        """
        start_time = time.time()
        if batch_id is None:
            batch_id = f"BATCH_{time.strftime('%Y%m%d_%H%M%S')}"

        print(f"\n========================================================")
        print(f"      🐅 TIGERTRACE_AI PROCESSING BATCH: {batch_id}     ")
        print(f"========================================================")

        # 1. Ingest SD Card
        raw_records = self.sd_loader.scan_sd_card_folder(raw_folder_path)
        if not raw_records:
            return {"status": "empty", "message": "No valid images found in folder"}

        total_frames = len(raw_records)
        quarantined_records = []
        human_records = []
        subject_sightings = []

        cur = self.conn.cursor()

        # 2. Phase 1: Blank Triage & Privacy Blurring
        print("\n--- [Phase 1] Camera Trap Triage & Staged Quarantine ---")
        for rec in raw_records:
            img_path = rec["file_path"]
            triage_res = self.triage_detector.detect_frame(img_path)

            if triage_res["is_blank"]:
                q_rec = self.quarantine_mgr.stage_blank_frame(
                    img_path, batch_id=batch_id,
                    reason="blank_no_subject",
                    confidence=triage_res["max_confidence"]
                )
                quarantined_records.append(q_rec)
                print(f"  [QUARANTINED BLANK] {rec['filename']:35} (Conf: {triage_res['max_confidence']:.2f})")
            else:
                cat = triage_res["category"]
                final_img_path = img_path
                if cat == "person":
                    human_boxes = [d["bbox_xyxy"] for d in triage_res["detections"] if d["class_id"] == 0]
                    blurred_path = os.path.join(self.blurred_dir, f"{rec['filename']}")
                    final_img_path, blurred = self.privacy_blurrer.apply_privacy_blur(img_path, human_boxes, blurred_path)
                    human_records.append(rec)
                    print(f"  [HUMAN PRIVACY BLUR] {rec['filename']:35} -> Face/Body Blurred")
                    
                animal_boxes = [d for d in triage_res["detections"] if d["class_id"] != 0]
                primary_bbox = animal_boxes[0]["bbox_xyxy"] if animal_boxes else None
                
                subject_sightings.append({
                    "raw_rec": rec,
                    "image_path": final_img_path,
                    "species": "tiger" if cat in ("tiger", "animal") else ("human" if cat == "person" else "wildlife"),
                    "bbox": primary_bbox,
                    "triage_conf": triage_res["max_confidence"]
                })
                print(f"  [SUBJECT RETAINED]  {rec['filename']:35} ({cat.upper()} Conf: {triage_res['max_confidence']:.2f})")

        # Log Triage Savings
        savings = self.quarantine_mgr.calculate_savings(quarantined_records)
        cur.execute("""
        INSERT INTO triage_logs (batch_id, total_frames, blank_frames, subject_frames, human_frames, bytes_saved, time_saved_minutes, quarantine_dir, execution_time_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            batch_id, total_frames, len(quarantined_records), len(subject_sightings), len(human_records),
            savings["bytes_saved"], savings["time_saved_minutes"], os.path.join(self.quarantine_mgr.base_dir, batch_id),
            round(time.time() - start_time, 2)
        ))
        self.conn.commit()

        # 3. Phase 2: Flank Stripe Re-ID & Catalogue Matching
        print("\n--- [Phase 2] Flank Stripe Re-ID & Catalogue Matching ---")
        reid_results = []

        for item in subject_sightings:
            raw_rec = item["raw_rec"]
            img_path = item["image_path"]
            station_id = raw_rec["station_id"]
            timestamp = raw_rec["timestamp"]
            bbox = item["bbox"]

            if item["species"] in ("human", "vehicle"):
                continue

            crop_img, crop_path = self.flank_extractor.extract_flank_crop(
                img_path, bbox_xyxy=bbox, output_dir=self.flank_crops_dir
            )

            cur.execute("""
            INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, bbox_json, flank_crop_path)
            VALUES (?, ?, ?, ?, 'tiger', ?, ?);
            """, (raw_rec["filename"], img_path, station_id, timestamp, json.dumps(bbox) if bbox else None, crop_path))
            
            sighting_id = cur.lastrowid
            self.conn.commit()

            enroll_res = self.enrollment_engine.identify_and_enroll(
                crop_path, sighting_id=sighting_id, image_name=raw_rec["filename"]
            )

            decision = enroll_res["decision"]
            assigned_id = enroll_res.get("assigned_tiger_id") or enroll_res.get("suggested_tiger_id")
            conf = enroll_res.get("confidence", 0.0)

            print(f"  [RE-ID {decision.upper():20}] {raw_rec['filename']:30} -> Assigned: {assigned_id:15} (Score: {conf:.2f})")
            
            reid_results.append({
                "sighting_id": sighting_id,
                "image": raw_rec["filename"],
                "station_id": station_id,
                "timestamp": timestamp,
                "decision": decision,
                "tiger_id": assigned_id,
                "confidence": conf
            })

        # 4. Phase 3: Spatial Occupancy & Behavioral Movement Prediction
        map_path = None
        tiger_home_ranges = {}
        territorial_overlaps = []
        behavior_predictions = {}

        if generate_maps or enable_behavior_prediction:
            print("\n--- [Phase 3] Spatial Occupancy & Predictive Behavioral Intelligence ---")
            # Query all sightings with station coordinates from database
            cur.execute("""
            SELECT s.tiger_id, s.station_id, s.timestamp, st.latitude, st.longitude, st.zone, st.range_name
            FROM sightings s
            JOIN stations st ON s.station_id = st.station_id
            WHERE s.tiger_id IS NOT NULL AND s.tiger_id != 'UNMATCHED';
            """)
            all_sightings = cur.fetchall()

            sightings_by_tiger = {}
            for row in all_sightings:
                tid = row["tiger_id"]
                if tid not in sightings_by_tiger:
                    sightings_by_tiger[tid] = []
                sightings_by_tiger[tid].append(dict(row))

            # Generate behavioral movement predictions
            if enable_behavior_prediction:
                for tid, t_sightings in sightings_by_tiger.items():
                    pred = self.movement_predictor.predict_tiger_movement(tid, t_sightings)
                    behavior_predictions[tid] = pred
                    next_stns = pred.get("predicted_next_stations", [])
                    stn_str = ", ".join([f"{s[0]} ({s[1]*100:.0f}%)" for s in next_stns]) if next_stns else "Insufficient transitions"
                    print(f"  [🔮 PREDICT] {tid:20} -> Next Likely: {stn_str}")

            if generate_maps:
                map_filename = f"pench_occupancy_map_{batch_id}.html"
                map_path, tiger_home_ranges, territorial_overlaps = self.map_generator.generate_interactive_reserve_map(
                    sightings_by_tiger,
                    output_filename=map_filename,
                    behavior_predictions=behavior_predictions if enable_behavior_prediction else None,
                    recent_batch_sightings=reid_results
                )

                # Also save as latest map reference for UI
                latest_map_path = os.path.join(self.map_generator.output_dir, "pench_occupancy_map_latest.html")
                try:
                    import shutil
                    shutil.copy2(map_path, latest_map_path)
                except Exception:
                    pass

                print(f"  [✓] Generated Home Ranges for {len(tiger_home_ranges)} resident tigers.")
                for tid, hr in tiger_home_ranges.items():
                    print(f"      - {tid:20}: Area = {hr['area_sq_km']:>5.1f} km² | Centroid = {hr['centroid']}")
                print(f"  [✓] Detected {len(territorial_overlaps)} territorial overlap / collapsing zones.")

        # 5. Phase 4: Movement Deviation & Threat Alerting Engine
        alerts = []
        alert_report_path = None

        if generate_alerts:
            print("\n--- [Phase 4] Behavioral Deviation & Threat Alerting Engine ---")
            alerts = self.alert_engine.evaluate_batch_alerts(reid_results)
            print(f"  [✓] Triggered {len(alerts)} management deviation alerts:")
            for a in alerts:
                sev_icon = "🔴" if a["severity"] == "CRITICAL" else ("🟡" if a["severity"] == "WARNING" else "ℹ️")
                print(f"      {sev_icon} [{a['severity']:8}] {a['alert_type']:20} - Tiger: {a['tiger_id']:15} | {a['detected_change']}")

            alert_report_path = self.alert_engine.export_alert_report_markdown(
                alerts, output_path=os.path.join(self.alerts_dir, f"Alert_Briefing_{batch_id}.md")
            )

        execution_duration = round(time.time() - start_time, 2)

        summary_report = {
            "batch_id": batch_id,
            "total_frames": total_frames,
            "blank_quarantined": len(quarantined_records),
            "retained_subjects": len(subject_sightings),
            "human_blurred": len(human_records),
            "triage_savings": savings,
            "reid_results": reid_results,
            "home_ranges": tiger_home_ranges,
            "territorial_overlaps": territorial_overlaps,
            "behavior_predictions": behavior_predictions,
            "interactive_map_path": map_path,
            "alerts": alerts,
            "alert_report_path": alert_report_path,
            "execution_duration_sec": execution_duration
        }

        print(f"\n========================================================")
        print(f"      BATCH COMPLETED IN {execution_duration} SECONDS   ")
        print(f"========================================================\n")
        return summary_report
