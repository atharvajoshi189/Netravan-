import os
import shutil
import sqlite3
from src.db.schema import get_connection, init_db, seed_sample_stations
from src.reid.enrollment import TigerEnrollmentEngine
from src.occupancy.map_generator import PenchMapGenerator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "database", "tigertrace.db")
REF_CAT_DIR = os.path.join(DATA_DIR, "reference_catalogue")

def reset_system():
    print("=========================================================================")
    print("        TIGERTRACE AI - RESETTING SYSTEM TO FRESH INITIAL STATE           ")
    print("=========================================================================")

    # 1. Clear output/cache directories
    folders_to_clear = [
        os.path.join(DATA_DIR, "outputs", "occupancy_maps"),
        os.path.join(DATA_DIR, "outputs", "alert_reports"),
        os.path.join(DATA_DIR, "quarantine"),
        os.path.join(DATA_DIR, "tiger_crops"),
        os.path.join(DATA_DIR, "annotated_sightings"),
        os.path.join(DATA_DIR, "review_visualizations")
    ]

    for folder in folders_to_clear:
        if os.path.exists(folder):
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"  Warning: could not delete {item_path}: {e}")
        os.makedirs(folder, exist_ok=True)
        print(f"[CLEARED] {folder}")

    # 2. Reset SQLite Database
    init_db(DB_PATH)
    conn = get_connection(DB_PATH)
    cur = conn.cursor()

    # Clear tables
    cur.execute("DELETE FROM sightings;")
    cur.execute("DELETE FROM triage_logs;")
    cur.execute("DELETE FROM review_queue;")
    cur.execute("DELETE FROM alerts;")
    cur.execute("DELETE FROM tigers;")
    conn.commit()

    print("[DB RESET] Cleared all sightings, triage logs, review queue, and alerts.")

    # Re-seed stations & initial reference tigers
    seed_sample_stations(DB_PATH)
    enrollment = TigerEnrollmentEngine(db_connection=conn)
    enrollment.seed_initial_catalogue_from_folder(REF_CAT_DIR)

    conn.close()

    # 3. Generate Baseline Map
    map_gen = PenchMapGenerator()
    map_path = map_gen.generate_interactive_reserve_map({}, output_filename="pench_occupancy_map_baseline.html")
    print(f"[BASELINE MAP] Generated clean Pench reserve map at: {map_path[0]}")

    print("\n[OK] System reset complete! TigerTrace AI is now in a 100% fresh first-time state.")
    print("   Ready for live field SD card batch ingestion from the UI dashboard.")
    print("=========================================================================\n")

if __name__ == "__main__":
    reset_system()
