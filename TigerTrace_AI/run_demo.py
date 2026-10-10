import os
import sys
import argparse
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.config import ALERT_PHONE_NUMBER, GAMMU_CONFIG_PATH, SMS_DRY_RUN
from src.pipeline import TigerTracePipeline

def main():
    parser = argparse.ArgumentParser(description="TigerTrace_AI: Automated Camera Trap Triage & Tiger Movement Intelligence System")
    parser.add_argument("--sd_card", type=str, default=os.path.join(current_dir, "data", "raw_sd_cards", "SD_CARD_PTR_STN_02"),
                        help="Path to raw camera trap SD card folder")
    parser.add_argument("--catalogue", type=str, default=os.path.join(current_dir, "data", "reference_catalogue"),
                        help="Path to reference tiger catalogue folder")
    parser.add_argument("--batch_id", type=str, default=None,
                        help="Optional custom batch ID")
    parser.add_argument("--enable_sms_alerts", action="store_true",
                        help="Enable offline SMS alerts for village-proximity events")
    parser.add_argument("--sms_dry_run", action="store_true", default=SMS_DRY_RUN,
                        help="Log SMS messages instead of sending them")
    parser.add_argument("--alert_phone_number", type=str, default=ALERT_PHONE_NUMBER,
                        help="Phone number to receive SMS alerts")
    parser.add_argument("--gammu_config_path", type=str, default=GAMMU_CONFIG_PATH,
                        help="Path to Gammu config file")
    args = parser.parse_args()

    print("=" * 75)
    print("   🐅 TIGERTRACE_AI: CAMERA TRAP TRIAGE & MOVEMENT INTELLIGENCE 🐅   ")
    print("=" * 75)
    print(f" Target SD Card Folder : {args.sd_card}")
    print(f" Reference Catalogue   : {args.catalogue}")
    print(f" SMS Alerts Enabled    : {args.enable_sms_alerts}")
    if args.enable_sms_alerts:
        print(f" SMS Dry Run           : {args.sms_dry_run}")
        print(f" SMS Phone Number      : {args.alert_phone_number}")
        print(f" Gammu Config Path     : {args.gammu_config_path}")
    print("=" * 75)

    # 1. Initialize Pipeline
    print("\n[1/3] Initializing SQLite Database, GIS Stations & Vision Models...")
    pipeline = TigerTracePipeline(
        enable_sms_alerts=args.enable_sms_alerts,
        alert_phone_number=args.alert_phone_number,
        gammu_config_path=args.gammu_config_path,
        sms_dry_run=args.sms_dry_run,
    )

    # 2. Seed Reference Tigers
    print("\n[2/3] Loading Known Tiger Catalogue (Bajirao, Collarwali, Patdev, Swastik, L-Mark)...")
    pipeline.seed_reference_catalogue(args.catalogue)

    # 3. Process the SD card batch
    print(f"\n[3/3] Executing Pipeline Across Raw Frames from: {args.sd_card}...")
    report = pipeline.process_sd_card_folder(args.sd_card, batch_id=args.batch_id, generate_maps=True, generate_alerts=True)

    print("\n" + "=" * 75)
    print("                    BATCH EXECUTION SUMMARY                     ")
    print("=" * 75)
    print(f" Batch ID             : {report.get('batch_id')}")
    print(f" Total Frames Scanned : {report.get('total_frames')}")
    print(f" Blank Quarantined    : {report.get('blank_quarantined')}")
    print(f" Retained Subjects    : {report.get('retained_subjects')}")
    print(f" Human Privacy Blurred: {report.get('human_blurred')}")
    print(f" Execution Time       : {report.get('execution_duration_sec')} seconds")
    print("-" * 75)
    
    savings = report.get("triage_savings", {})
    print(f" Storage Space Saved  : {savings.get('mb_saved', 0.0)} MB ({savings.get('bytes_saved', 0)} bytes)")
    print(f" Staff Hours Saved    : {savings.get('time_saved_hours', 0.0)} hours ({savings.get('time_saved_minutes', 0.0)} mins)")
    print("-" * 75)
    
    print("\n--- [Phase 2] INDIVIDUAL TIGER IDENTIFICATION (RE-ID) ---")
    reid_list = report.get("reid_results", [])
    if reid_list:
        print(f" {'Image File':<26} | {'Station':<12} | {'Assigned Tiger':<16} | {'Score':<6} | {'Decision'}")
        print("-" * 75)
        for r in reid_list:
            print(f" {r['image']:<26} | {r['station_id']:<12} | {r['tiger_id']:<16} | {r['confidence']:<6.2f} | {r['decision']}")
            
    print("\n--- [Phase 3] SPATIAL OCCUPANCY & HOME RANGES (MCP) ---")
    hrs = report.get("home_ranges", {})
    for tid, hr in hrs.items():
        print(f" 🐾 Tiger: {tid:<18} | Area: {hr['area_sq_km']:>5.1f} km² | Centroid: {hr['centroid']} | Sightings: {hr['sighting_count']}")
        
    overlaps = report.get("territorial_overlaps", [])
    if overlaps:
        print(f"\n ⚠️ Territorial Overlap / Collapsing Zones Detected ({len(overlaps)}):")
        for ov in overlaps:
            print(f"    - {ov['tiger_1']} ↔ {ov['tiger_2']}: Overlap Area = {ov['overlap_area_sq_km']} km² (Risk: {ov['conflict_risk']})")

    print("\n--- [Phase 4] BEHAVIORAL DEVIATION ALERTS ---")
    alerts = report.get("alerts", [])
    if alerts:
        for idx, a in enumerate(alerts, 1):
            sev_icon = "🔴" if a["severity"] == "CRITICAL" else ("🟡" if a["severity"] == "WARNING" else "ℹ️")
            print(f" {sev_icon} [{a['severity']}] {a['alert_type']}: {a['detected_change']}")
    else:
        print(" No new critical deviations detected.")

    print("\n" + "=" * 75)
    print(f" 🗺️ Interactive Reserve Map : {report.get('interactive_map_path')}")
    print(f" 🚨 Alert Briefing Report   : {report.get('alert_report_path')}")
    print(f" 🗄️ SQLite Database         : {os.path.join(current_dir, 'data', 'database', 'tigertrace.db')}")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
