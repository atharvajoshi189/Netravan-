import sqlite3
import os
import json
import time

DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "database")
DB_PATH = os.path.join(DATABASE_DIR, "tigertrace.db")

def get_connection(db_path=DB_PATH):
    """Get a connection to the SQLite database, creating parent dirs if necessary."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
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
        review_status TEXT DEFAULT 'confirmed' CHECK(review_status IN ('confirmed', 'pending_review', 'rejected')),
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
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'reassigned', 'enrolled_new')),
        reviewer_notes TEXT,
        reviewed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    """Seed real-world Pench Tiger Reserve grid stations & villages."""
    from ..occupancy.pench_gis_data import PENCH_CAMERA_STATIONS, PENCH_VILLAGES
    
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    # Seed Stations
    for stn in PENCH_CAMERA_STATIONS:
        cur.execute("""
        INSERT OR REPLACE INTO stations (station_id, grid_id, range_name, zone, latitude, longitude, elevation_m, camera_model)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (stn["station_id"], stn["grid_id"], stn["range"], stn["zone"], stn["lat"], stn["lon"], stn["elevation_m"], stn["camera_model"]))

    # Seed Villages
    for vil in PENCH_VILLAGES:
        cur.execute("""
        INSERT OR REPLACE INTO villages (village_id, name, latitude, longitude, zone, risk_level, description)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (vil["village_id"], vil["name"], vil["lat"], vil["lon"], vil["zone"], vil["risk_level"], vil["description"]))

    conn.commit()
    conn.close()
    print(f"[DB SEED] Seeded {len(PENCH_CAMERA_STATIONS)} Pench camera stations and {len(PENCH_VILLAGES)} buffer villages into SQLite.")

if __name__ == "__main__":
    init_db()
    seed_sample_stations()
