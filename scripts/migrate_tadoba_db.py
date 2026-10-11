import json
import os
import sqlite3

def migrate_to_tadoba():
    db_path = os.path.join("TigerTrace_AI", "data", "database", "tigertrace.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Update Stations Table to 24 Tadoba Camera Stations
    cur.execute("DELETE FROM stations;")
    
    cameras_json_path = os.path.join("web_ui", "public", "data", "demo_cameras.json")
    with open(cameras_json_path, "r", encoding="utf-8") as f:
        cameras = json.load(f)

    for cam in cameras:
        cam_id = cam["id"]
        cam_name = cam["name"]
        lat = cam["pos"][0]
        lon = cam["pos"][1]
        cur.execute("""
            INSERT INTO stations (station_id, grid_id, range_name, zone, latitude, longitude, elevation_m, camera_model, is_active)
            VALUES (?, ?, ?, 'core', ?, ?, 280.0, 'Cuddeback_TATR', 1);
        """, (cam_id, cam_id, cam_name, lat, lon))
    print(f"Seeded {len(cameras)} Tadoba camera stations into stations table.")

    # 2. Update Villages Table to Tadoba buffer villages
    cur.execute("DELETE FROM villages;")
    tadoba_villages = [
        ("VIL_TATR_01", "Moharli Settlement", 20.1800, 79.3100, "buffer", "LOW", "Tadoba south tourism gate buffer community"),
        ("VIL_TATR_02", "Kolara Village", 20.4500, 79.3500, "buffer", "MEDIUM", "Tadoba north gate fringe corridor"),
        ("VIL_TATR_03", "Navegaon Settlement", 20.4800, 79.2800, "buffer", "LOW", "Northwest forest border habitat"),
        ("VIL_TATR_04", "Khutwanda Village", 20.2800, 79.2500, "buffer", "LOW", "West boundary fringe settlement"),
        ("VIL_TATR_05", "Pangdi Settlement", 20.0800, 79.4000, "buffer", "LOW", "South buffer dispersal border"),
        ("VIL_TATR_06", "Zari Village", 20.0300, 79.3600, "buffer", "LOW", "Southern boundary eco-sensitive buffer")
    ]
    for v in tadoba_villages:
        cur.execute("""
            INSERT INTO villages (village_id, name, latitude, longitude, zone, risk_level, description)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, v)
    print(f"Seeded {len(tadoba_villages)} Tadoba villages into villages table.")

    # 3. Update Tigers Table to Tadoba Tigers
    cur.execute("DELETE FROM tigers;")
    tadoba_tigers = [
        ("T-1", "Maya (T-1)", "F", "both", "2015-04-12", "2026-10-10", "resident", "web_ui/public/data/maya_crop.jpg", "{}", "Legendary dominant tigress of Tadoba Lake and core territory."),
        ("T-3", "Chhota Matka (T-3)", "M", "both", "2018-02-14", "2026-10-10", "resident", "web_ui/public/data/chhota_matka.jpg", "{}", "Dominant territorial male spanning core to north buffer."),
        ("T-2", "Matkasur (T-2)", "M", "both", "2014-06-20", "2026-10-09", "resident", "web_ui/public/data/matkasur.jpg", "{}", "Veteran male tiger of Tadoba."),
        ("T-4", "T-54", "M", "left", "2021-08-10", "2026-10-10", "resident", "web_ui/public/data/t54.jpg", "{}", "Sub-adult male dispersing along Kolsa corridor."),
        ("T-84", "Chota Dadhiyal (T-84)", "M", "both", "2019-11-05", "2026-10-11", "resident", "TigerTrace_AI/data/reference_catalogue/Chota_Dadhiyal_T84/Chota_Dadhiyal_001_flank_crop.jpg", "{}", "Prominent territorial male with distinctive flank stripe geometry.")
    ]
    for t in tadoba_tigers:
        cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, last_seen_date, status, reference_crop_path, stripe_features_json, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, t)
    print(f"Seeded {len(tadoba_tigers)} Tadoba tigers into tigers table.")

    # 4. Clean up any existing sightings & review queue referencing PTR or old names
    cur.execute("UPDATE sightings SET station_id = 'CT-C1' WHERE station_id LIKE 'PTR_%';")
    cur.execute("UPDATE sightings SET tiger_id = 'T-84' WHERE tiger_id IN ('BAJIRAO', 'SWASTIK', 'PTR_T_007', 'PTR_T_008');")
    cur.execute("UPDATE review_queue SET suggested_tiger_id = 'T-84' WHERE suggested_tiger_id IN ('BAJIRAO', 'SWASTIK', 'PTR_T_007', 'PTR_T_008');")
    cur.execute("UPDATE alerts SET station_id = 'CT-C1' WHERE station_id LIKE 'PTR_%';")
    cur.execute("UPDATE alerts SET tiger_id = 'T-84' WHERE tiger_id IN ('BAJIRAO', 'SWASTIK', 'PTR_T_007', 'PTR_T_008');")

    conn.commit()
    conn.close()
    print("Database successfully migrated to Tadoba-Andhari Tiger Reserve.")

if __name__ == "__main__":
    migrate_to_tadoba()
