import sqlite3
import os
import json
import time

DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "database")
DB_PATH = os.path.join(DATABASE_DIR, "tigertrace.db")

def get_connection(db_path=DB_PATH):
    """Get a connection to the SQLite database, creating parent dirs if necessary."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    """Initialize the complete SQLite schema for Pench Tiger Reserve."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Camera Trap Stations Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stations (
        station_id TEXT PRIMARY KEY,
        grid_id TEXT NOT NULL,
        range_name TEXT,
        zone TEXT NOT NULL CHECK(zone IN ('core', 'buffer', 'village_fringe')),
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        elevation_m REAL,
        camera_model TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Surrounding Villages Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS villages (
        village_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        zone TEXT DEFAULT 'village_fringe',
        risk_level TEXT CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Known Individual Tigers Catalogue
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tigers (
        tiger_id TEXT PRIMARY KEY,
        name TEXT,
        gender TEXT CHECK(gender IN ('M', 'F', 'U')),
        flank_side_registered TEXT CHECK(flank_side_registered IN ('left', 'right', 'both')),
        first_seen_date TEXT,
        last_seen_date TEXT,
        status TEXT DEFAULT 'resident' CHECK(status IN ('resident', 'dispersing', 'absent', 'deceased')),
        reference_crop_path TEXT,
        stripe_features_json TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Individual Sightings / Camera Trap Detections
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sightings (
        sighting_id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_name TEXT NOT NULL,
        image_path TEXT NOT NULL,
        station_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        species TEXT DEFAULT 'tiger',
        tiger_id TEXT,
        flank_side TEXT CHECK(flank_side IN ('left', 'right', 'unknown')),
        reid_score REAL,
        match_method TEXT CHECK(match_method IN ('hotspotter_sift', 'deep_embedding', 'manual', 'unmatched')),
        review_status TEXT DEFAULT 'confirmed' CHECK(review_status IN ('confirmed', 'pending_review', 'rejected', 'inconclusive')),
        bbox_json TEXT,
        flank_crop_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations(station_id),
        FOREIGN KEY (tiger_id) REFERENCES tigers(tiger_id)
    );
    """)

    # 5. Human-in-the-Loop Review Queue
    cur.execute("""
    CREATE TABLE IF NOT EXISTS review_queue (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sighting_id INTEGER NOT NULL,
        suggested_tiger_id TEXT,
        suggested_score REAL,
        top_candidates_json TEXT,
        flank_crop_path TEXT,
        sift_match_viz_path TEXT,
        query_flank TEXT,
        ref_flank TEXT,
        sift_inliers INTEGER DEFAULT 0,
        geometric_status TEXT DEFAULT 'none',
        raw_cosine_sim REAL DEFAULT 0.0,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'accepted', 'rejected', 'inconclusive', 'reassigned', 'enrolled_new')),
        decision TEXT,
        decision_reason TEXT,
        reviewer_id TEXT,
        reviewer_notes TEXT,
        reviewed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sighting_id) REFERENCES sightings(sighting_id)
    );
    """)

    # Ensure new columns exist on review_queue if table was previously created
    cur.execute("PRAGMA table_info(review_queue);")
    existing_cols = {col[1] for col in cur.fetchall()}
    for col_name, col_type in [
        ("query_flank", "TEXT"),
        ("ref_flank", "TEXT"),
        ("sift_inliers", "INTEGER DEFAULT 0"),
        ("geometric_status", "TEXT DEFAULT 'none'"),
        ("raw_cosine_sim", "REAL DEFAULT 0.0"),
        ("decision", "TEXT"),
        ("decision_reason", "TEXT"),
        ("reviewer_id", "TEXT"),
    ]:
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE review_queue ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass

    # 5b. Human-in-the-Loop Review Audit Log
    cur.execute("""
    CREATE TABLE IF NOT EXISTS review_audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER NOT NULL,
        sighting_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        assigned_tiger_id TEXT,
        reviewer_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        machine_suggested_id TEXT,
        machine_suggested_score REAL,
        machine_raw_cosine REAL,
        machine_sift_inliers INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (review_id) REFERENCES review_queue(review_id),
        FOREIGN KEY (sighting_id) REFERENCES sightings(sighting_id)
    );
    """)

    # 6. Behavioral & Movement Deviation Alerts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT NOT NULL CHECK(alert_type IN ('CENTROID_SHIFT', 'VILLAGE_DISPERSAL', 'NOVEL_STATION', 'PROLONGED_ABSENCE', 'TERRITORIAL_CONFLICT')),
        severity TEXT NOT NULL CHECK(severity IN ('INFO', 'WARNING', 'CRITICAL')),
        tiger_id TEXT NOT NULL,
        station_id TEXT,
        detected_change TEXT NOT NULL,
        supporting_evidence TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        is_acknowledged INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tiger_id) REFERENCES tigers(tiger_id),
        FOREIGN KEY (station_id) REFERENCES stations(station_id)
    );
    """)

    # 7. Triage & Blank Quarantine Execution Logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS triage_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT NOT NULL,
        total_frames INTEGER NOT NULL,
        blank_frames INTEGER NOT NULL,
        subject_frames INTEGER NOT NULL,
        human_frames INTEGER NOT NULL,
        bytes_saved INTEGER NOT NULL,
        time_saved_minutes REAL NOT NULL,
        quarantine_dir TEXT,
        execution_time_seconds REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sightings_station ON sightings(station_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sightings_tiger ON sightings(tiger_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sightings_timestamp ON sightings(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_tiger ON alerts(tiger_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);")

    conn.commit()
    conn.close()
    print(f"[DB INIT] SQLite database initialized successfully at: {db_path}")

def seed_sample_stations(db_path=DB_PATH):
    """Seed real-world Tadoba-Andhari Tiger Reserve (TATR) grid stations & villages."""
    import json
    import os

    conn = get_connection(db_path)
    cur = conn.cursor()

    cams_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "web_ui", "public", "data", "demo_cameras.json"))
    if os.path.exists(cams_path):
        with open(cams_path, "r", encoding="utf-8") as f:
            cameras = json.load(f)
        for cam in cameras:
            cur.execute("""
            INSERT OR REPLACE INTO stations (station_id, grid_id, range_name, zone, latitude, longitude, elevation_m, camera_model, is_active)
            VALUES (?, ?, ?, 'core', ?, ?, 280.0, 'Cuddeback_TATR', 1);
            """, (cam["id"], cam["id"], cam["name"], cam["pos"][0], cam["pos"][1]))
        total_cams = len(cameras)
    else:
        tadoba_defaults = [
            ("CT-NW1", "North-West Nimdela Corner Camera", 20.4285, 79.2365),
            ("CT-N1", "Far North Navegaon Boundary Camera", 20.4720, 79.2780),
            ("CT-C1", "Tadoba Lake Watchtower", 20.2520, 79.3320),
            ("CT-C4", "Pandharpauni Meadow", 20.2310, 79.3450),
            ("CT-W1", "Khutwanda Buffer Waterhole", 20.2840, 79.2560),
            ("CT-E1", "Kolsa Range Dense Canopy", 20.1580, 79.4210)
        ]
        for stn_id, name, lat, lon in tadoba_defaults:
            cur.execute("""
            INSERT OR REPLACE INTO stations (station_id, grid_id, range_name, zone, latitude, longitude, elevation_m, camera_model, is_active)
            VALUES (?, ?, ?, 'core', ?, ?, 280.0, 'Cuddeback_TATR', 1);
            """, (stn_id, stn_id, name, lat, lon))
        total_cams = len(tadoba_defaults)

    tadoba_villages = [
        ("VIL_TATR_01", "Moharli Settlement", 20.1800, 79.3100, "buffer", "LOW", "Tadoba south tourism gate buffer community"),
        ("VIL_TATR_02", "Kolara Village", 20.4500, 79.3500, "buffer", "MEDIUM", "Tadoba north gate fringe corridor"),
        ("VIL_TATR_03", "Navegaon Settlement", 20.4800, 79.2800, "buffer", "LOW", "Northwest forest border habitat"),
        ("VIL_TATR_04", "Khutwanda Village", 20.2800, 79.2500, "buffer", "LOW", "West boundary fringe settlement"),
        ("VIL_TATR_05", "Pangdi Settlement", 20.0800, 79.4000, "buffer", "LOW", "South buffer dispersal border"),
        ("VIL_TATR_06", "Zari Village", 20.0300, 79.3600, "buffer", "LOW", "Southern boundary eco-sensitive buffer")
    ]
    for vil in tadoba_villages:
        cur.execute("""
        INSERT OR REPLACE INTO villages (village_id, name, latitude, longitude, zone, risk_level, description)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, vil)

    conn.commit()
    conn.close()
    print(f"[DB SEED] Seeded {total_cams} Tadoba camera stations and {len(tadoba_villages)} buffer settlements into SQLite.")

if __name__ == "__main__":
    init_db()
    seed_sample_stations()
