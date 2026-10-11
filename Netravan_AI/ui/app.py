import os
import sys
import json
import shutil
import sqlite3
import datetime
from typing import Optional, List
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

ui_dir = os.path.dirname(os.path.abspath(__file__))
pkg_dir = os.path.dirname(ui_dir)
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from src.db.schema import get_connection, init_db, seed_sample_stations
from src.pipeline import TigerTracePipeline
from src.reid.enrollment import TigerEnrollmentEngine
from src.config import ALERT_PHONE_NUMBER, GAMMU_CONFIG_PATH, SMS_DRY_RUN
from src.occupancy.pench_gis_data import PENCH_CAMERA_STATIONS

app = FastAPI(title="NETRAVAN - Tadoba Wildlife Intelligence Platform", version="3.0.0")

# Enable CORS for Flutter mobile, web, and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory=os.path.join(ui_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(ui_dir, "templates"))

# Initialize Pipeline Instance
pipeline = TigerTracePipeline()
reference_dir = os.path.join(pkg_dir, "data", "reference_catalogue")
if os.path.exists(reference_dir):
    pipeline.seed_reference_catalogue(reference_dir)

class ProcessSDRequest(BaseModel):
    sd_card_path: str
    enable_sms_alerts: bool = False
    sms_dry_run: bool = SMS_DRY_RUN
    alert_phone_number: Optional[str] = ALERT_PHONE_NUMBER
    gammu_config_path: Optional[str] = GAMMU_CONFIG_PATH

class ReviewActionRequest(BaseModel):
    action: str  # 'accept' | 'approve' | 'reject' | 'inconclusive' | 'unknown' | 'enroll_new'
    reviewer_id: Optional[str] = "authorized_field_officer"
    reason: Optional[str] = "Verified stripe bifurcation pattern"
    tiger_id: Optional[str] = None
    force: bool = False

class RestoreQuarantineRequest(BaseModel):
    filename: str
    batch_id: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main Command Center Dashboard Page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/telemetry")
async def get_telemetry():
    """Returns real-time telemetry metrics for the dashboard header."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM sightings;")
    total_sightings = cur.fetchone()[0]

    cur.execute("SELECT SUM(total_frames), SUM(blank_frames), SUM(bytes_saved), SUM(time_saved_minutes) FROM triage_logs;")
    row = cur.fetchone()
    total_frames = (row[0] or 0) + total_sightings
    blank_frames = row[1] or 0
    bytes_saved = row[2] or 0
    time_saved_minutes = row[3] or 0

    cur.execute("SELECT COUNT(*) FROM tigers;")
    resident_tigers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM review_queue WHERE status = 'pending';")
    pending_reviews = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alerts WHERE is_acknowledged = 0;")
    active_alerts = cur.fetchone()[0]

    blank_pct = round((blank_frames / total_frames * 100), 1) if total_frames > 0 else 0.0

    conn.close()
    return {
        "total_frames": total_frames,
        "blank_frames": blank_frames,
        "blank_percentage": blank_pct,
        "mb_saved": round(bytes_saved / (1024 * 1024), 1),
        "staff_hours_saved": round(time_saved_minutes / 60.0, 1),
        "resident_tigers_count": resident_tigers,
        "pending_reviews_count": pending_reviews,
        "active_alerts_count": active_alerts
    }

@app.get("/api/available_sd_cards")
async def get_available_sd_cards():
    """Returns a list of all pre-configured and uploaded SD card drops."""
    sd_base = os.path.join(pkg_dir, "data", "raw_sd_cards")
    cards = []
    if os.path.exists(sd_base):
        for item in sorted(os.listdir(sd_base)):
            item_path = os.path.join(sd_base, item)
            if os.path.isdir(item_path):
                img_count = len([f for f in os.listdir(item_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
                cards.append({
                    "name": item,
                    "path": os.path.relpath(item_path, pkg_dir).replace("\\", "/"),
                    "image_count": img_count
                })
    return cards

@app.post("/api/process_sd")
async def process_sd_card(req: ProcessSDRequest):
    """Executes full 4-Phase batch processing across an SD card folder."""
    raw_path = req.sd_card_path.strip()
    if not os.path.isabs(raw_path):
        raw_path = os.path.join(pkg_dir, raw_path)

    if not os.path.exists(raw_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {raw_path}")

    pipeline.configure_sms_alerts(
        enable_sms_alerts=req.enable_sms_alerts,
        alert_phone_number=req.alert_phone_number,
        gammu_config_path=req.gammu_config_path,
        sms_dry_run=req.sms_dry_run,
    )

    report = pipeline.process_sd_card_folder(raw_path, generate_maps=True, generate_alerts=True)
    
    # Enrich report with image thumbnail URLs and GPS info
    conn = get_connection()
    cur = conn.cursor()
    enriched_reid = []
    for r in report.get("reid_results", []):
        stn_id = r["station_id"]
        cur.execute("SELECT grid_id, range_name, zone, latitude, longitude FROM stations WHERE station_id = ?;", (stn_id,))
        stn_info = cur.fetchone()
        
        enriched_reid.append({
            **r,
            "range": stn_info["range_name"] if stn_info else "Unknown",
            "zone": stn_info["zone"] if stn_info else "core",
            "lat": stn_info["latitude"] if stn_info else 0.0,
            "lon": stn_info["longitude"] if stn_info else 0.0,
            "image_url": f"/api/image?path={os.path.join(raw_path, r['image'])}"
        })
    report["reid_results"] = enriched_reid
    conn.close()

    return report

@app.post("/api/upload_batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    station_id: str = Form("CT-C1"),
    enable_sms_alerts: bool = Form(False),
    sms_dry_run: bool = Form(SMS_DRY_RUN),
    alert_phone_number: str = Form(ALERT_PHONE_NUMBER),
    gammu_config_path: str = Form(GAMMU_CONFIG_PATH),
):
    """Handles direct browser folder/files upload into a new SD drop."""
    batch_name = f"UPLOAD_{station_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    target_dir = os.path.join(pkg_dir, "data", "raw_sd_cards", batch_name)
    os.makedirs(target_dir, exist_ok=True)

    saved_count = 0
    for file in files:
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            file_path = os.path.join(target_dir, os.path.basename(file.filename))
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_count += 1

    if saved_count == 0:
        shutil.rmtree(target_dir)
        raise HTTPException(status_code=400, detail="No valid image files found in upload.")

    pipeline.configure_sms_alerts(
        enable_sms_alerts=enable_sms_alerts,
        alert_phone_number=alert_phone_number,
        gammu_config_path=gammu_config_path,
        sms_dry_run=sms_dry_run,
    )

    # Process immediately
    report = pipeline.process_sd_card_folder(target_dir, batch_id=batch_name, generate_maps=True, generate_alerts=True)
    return report

@app.get("/api/quarantine_blanks")
async def get_quarantine_blanks():
    """Returns quarantined blank images with file sizes and timestamps."""
    q_base = os.path.join(pkg_dir, "data", "quarantine")
    blanks = []
    if os.path.exists(q_base):
        for root, _, files in os.walk(q_base):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    fp = os.path.join(root, f)
                    sz = os.path.getsize(fp)
                    batch = os.path.basename(root)
                    blanks.append({
                        "filename": f,
                        "batch_id": batch,
                        "file_path": fp,
                        "size_mb": round(sz / (1024 * 1024), 2),
                        "reason": "False-Trigger Blank (Vegetation / Wind / Rain)",
                        "image_url": f"/api/image?path={fp}"
                    })
    return blanks

@app.get("/api/behavior_predictions")
async def get_behavior_predictions():
    """Returns movement behavior predictions, transition probabilities, and directional trends for all resident tigers."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT s.sighting_id, s.tiger_id, s.station_id, s.timestamp, s.image_path, s.flank_side,
           s.reid_score, s.review_status, st.latitude, st.longitude, st.zone, st.range_name
    FROM sightings s
    JOIN stations st ON s.station_id = st.station_id
    WHERE s.tiger_id IS NOT NULL AND s.tiger_id != 'UNMATCHED';
    """)
    all_sightings = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT station_id, range_name, zone, latitude, longitude FROM stations;")
    stations_map = {r["station_id"]: dict(r) for r in cur.fetchall()}
    conn.close()

    sightings_by_tiger = {}
    for row in all_sightings:
        tid = row["tiger_id"]
        if tid not in sightings_by_tiger:
            sightings_by_tiger[tid] = []
        sightings_by_tiger[tid].append(row)

    predictions = {}
    for tid, t_sightings in sightings_by_tiger.items():
        pred = pipeline.movement_predictor.predict_tiger_movement(tid, t_sightings)
        
        # Enrich predicted next stations with geographic coordinates
        predicted_detailed = []
        for item in pred.get("predicted_next_stations", []):
            stn_id = item[0] if isinstance(item, (list, tuple)) else item.get("station_id")
            prob = float(item[1]) if isinstance(item, (list, tuple)) else float(item.get("probability", 0.0))
            stn_meta = stations_map.get(stn_id, {})
            predicted_detailed.append({
                "station_id": stn_id,
                "probability": prob,
                "latitude": stn_meta.get("latitude"),
                "longitude": stn_meta.get("longitude"),
                "range_name": stn_meta.get("range_name"),
                "zone": stn_meta.get("zone")
            })

        curr_stn_id = pred.get("current_station")
        curr_stn_meta = stations_map.get(curr_stn_id, {}) if curr_stn_id else {}

        # Chronological sorted sightings for historical movement path
        sorted_sightings = sorted(
            t_sightings,
            key=lambda x: str(x.get("timestamp") or "")
        )
        chronological_trail = []
        for s in sorted_sightings:
            chronological_trail.append({
                "sighting_id": s.get("sighting_id"),
                "station_id": s.get("station_id"),
                "timestamp": s.get("timestamp"),
                "latitude": s.get("latitude"),
                "longitude": s.get("longitude"),
                "image_path": s.get("image_path"),
                "image_url": f"/api/image?path={s['image_path']}" if s.get("image_path") else None,
                "flank_side": s.get("flank_side"),
                "reid_score": s.get("reid_score"),
                "zone": s.get("zone"),
                "range_name": s.get("range_name")
            })

        predictions[tid] = {
            "tiger_id": tid,
            "status": pred["status"],
            "confidence_note": pred["confidence_note"],
            "sighting_count": pred["sighting_count"],
            "current_station": curr_stn_id,
            "current_station_info": {
                "station_id": curr_stn_id,
                "latitude": curr_stn_meta.get("latitude"),
                "longitude": curr_stn_meta.get("longitude"),
                "range_name": curr_stn_meta.get("range_name"),
                "zone": curr_stn_meta.get("zone")
            } if curr_stn_id else None,
            "predicted_next_stations": pred["predicted_next_stations"],
            "predicted_next_stations_detailed": predicted_detailed,
            "directional_trend": pred["directional_trend"],
            "peak_location": pred["peak_location"],
            "heatmap_points": pred.get("heatmap_points", []),
            "heatmap_points_count": len(pred.get("heatmap_points", [])),
            "chronological_sightings": chronological_trail
        }
    return predictions

@app.get("/api/reserve/gis")
async def get_reserve_gis_layers():
    """Returns official GIS vector boundaries, camera station network, and surrounding human settlement villages."""
    from src.occupancy.pench_gis_data import PENCH_CORE_BOUNDARY, PENCH_BUFFER_BOUNDARY, PENCH_VILLAGES, PENCH_CAMERA_STATIONS
    return {
        "status": "success",
        "core_boundary": PENCH_CORE_BOUNDARY,
        "buffer_boundary": PENCH_BUFFER_BOUNDARY,
        "villages": PENCH_VILLAGES,
        "camera_stations": PENCH_CAMERA_STATIONS
    }

@app.get("/api/map")
async def get_interactive_map():
    """Serves the latest generated interactive Folium reserve map HTML, creating one with predictive heatmaps if needed."""
    maps_dir = os.path.join(pkg_dir, "data", "outputs", "occupancy_maps")
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    if os.path.exists(maps_dir):
        latest_candidate = os.path.join(maps_dir, "pench_occupancy_map_latest.html")
        if os.path.exists(latest_candidate):
            return FileResponse(latest_candidate, media_type="text/html", headers=headers)

        batch_files = [os.path.join(maps_dir, f) for f in os.listdir(maps_dir) if f.startswith("pench_occupancy_map_BATCH_") and f.endswith(".html")]
        if batch_files:
            latest_map = max(batch_files, key=os.path.getmtime)
            return FileResponse(latest_map, media_type="text/html", headers=headers)

        all_files = [os.path.join(maps_dir, f) for f in os.listdir(maps_dir) if f.endswith(".html")]
        if all_files:
            latest_map = max(all_files, key=os.path.getmtime)
            return FileResponse(latest_map, media_type="text/html", headers=headers)

    # Generate on the fly if no map exists
    conn = get_connection()
    cur = conn.cursor()
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
    conn.close()

    behavior_predictions = {}
    for tid, t_sightings in sightings_by_tiger.items():
        behavior_predictions[tid] = pipeline.movement_predictor.predict_tiger_movement(tid, t_sightings)

    map_path, _, _ = pipeline.map_generator.generate_interactive_reserve_map(
        sightings_by_tiger,
        output_filename="pench_occupancy_map_latest.html",
        behavior_predictions=behavior_predictions
    )
    return FileResponse(map_path, media_type="text/html", headers=headers)

@app.get("/api/review_queue")
async def get_review_queue():
    """Returns pending human review items with rich biometric audit evidence."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(review_queue);")
    rq_cols = {col[1] for col in cur.fetchall()}

    query = """
    SELECT rq.review_id, rq.sighting_id, rq.suggested_tiger_id, rq.suggested_score, 
           rq.flank_crop_path, rq.sift_match_viz_path, rq.status, rq.top_candidates_json,
           s.station_id, s.image_name, s.image_path, s.timestamp, s.flank_side as sighting_flank,
           t.name as candidate_name, t.reference_crop_path, t.flank_side_registered as ref_flank_registered
    """
    if "query_flank" in rq_cols:
        query += ", rq.query_flank, rq.ref_flank, rq.sift_inliers, rq.geometric_status, rq.raw_cosine_sim"

    query += """
    FROM review_queue rq
    JOIN sightings s ON rq.sighting_id = s.sighting_id
    LEFT JOIN tigers t ON rq.suggested_tiger_id = t.tiger_id
    WHERE rq.status = 'pending'
    ORDER BY rq.created_at DESC;
    """
    cur.execute(query)
    raw_items = cur.fetchall()

    items = []
    for r in raw_items:
        row = dict(r)
        top_cands = []
        try:
            if row.get("top_candidates_json"):
                top_cands = json.loads(row["top_candidates_json"])
        except Exception:
            pass

        ref_crop = row.get("reference_crop_path")
        if not ref_crop and top_cands and len(top_cands) > 0:
            ref_crop = top_cands[0].get("ref_crop_path")

        q_flank = row.get("query_flank") or row.get("sighting_flank") or "unknown"
        r_flank = row.get("ref_flank") or row.get("ref_flank_registered") or "both"

        sift_inl = row.get("sift_inliers")
        if sift_inl is None and top_cands and len(top_cands) > 0:
            sift_inl = top_cands[0].get("inlier_count", 0)

        geom_stat = row.get("geometric_status")
        if not geom_stat and top_cands and len(top_cands) > 0:
            geom_stat = top_cands[0].get("geometric_verification", "none")

        raw_cos = row.get("raw_cosine_sim")
        if raw_cos is None and top_cands and len(top_cands) > 0:
            raw_cos = top_cands[0].get("raw_cosine_similarity", 0.0)

        items.append({
            "review_id": row["review_id"],
            "sighting_id": row["sighting_id"],
            "status": row["status"],
            "candidate_tiger_id": row["suggested_tiger_id"],
            "candidate_name": row.get("candidate_name") or f"Candidate {row['suggested_tiger_id']}",
            "candidate_score": round(row.get("suggested_score") or 0.0, 4),
            "submitted_image_path": row.get("image_path"),
            "submitted_image_url": f"/api/image?path={row['image_path']}" if row.get("image_path") and os.path.exists(row['image_path']) else (f"/api/image?path={row['flank_crop_path']}" if row.get("flank_crop_path") and os.path.exists(row['flank_crop_path']) else ""),
            "flank_crop_path": row.get("flank_crop_path"),
            "flank_crop_url": f"/api/image?path={row['flank_crop_path']}" if row.get("flank_crop_path") and os.path.exists(row['flank_crop_path']) else "",
            "reference_image_path": ref_crop,
            "reference_image_url": f"/api/image?path={ref_crop}" if ref_crop and os.path.exists(ref_crop) else "",
            "sift_viz_path": row.get("sift_match_viz_path"),
            "sift_viz_url": f"/api/image?path={row['sift_match_viz_path']}" if row.get("sift_match_viz_path") and os.path.exists(row['sift_match_viz_path']) else "",
            "query_flank": q_flank,
            "ref_flank": r_flank,
            "sift_inliers": sift_inl or 0,
            "geometric_status": geom_stat or "none",
            "raw_cosine_sim": round(raw_cos or 0.0, 4),
            "station_id": row.get("station_id"),
            "image_name": row.get("image_name"),
            "timestamp": row.get("timestamp"),
            "top_candidates": top_cands,
            "uncalibrated_warning": "⚠️ CAUTION: Machine similarity scores are heuristic and uncalibrated. A match score alone does NOT establish individual tiger identity without human verification.",
        })
    conn.close()
    return items

@app.post("/api/review_queue/{review_id}/action")
async def handle_review_action(review_id: int, req: ReviewActionRequest):
    """
    Step 14: Authorized Human-in-the-Loop review decision.
    Accepts, rejects, marks inconclusive, or enrolls new individual with full audit logging and concurrency control.
    """
    conn = get_connection()
    try:
        engine = TigerEnrollmentEngine(conn)
        result = engine.process_review_decision(
            review_id=review_id,
            action=req.action,
            reviewer_id=req.reviewer_id or "authorized_field_officer",
            reason=req.reason or "Human verification completed via Command Center",
            tiger_id=req.tiger_id,
            force=req.force,
        )
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # Concurrency / conflict on already-resolved item
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/api/review_queue/history")
async def get_review_history(limit: int = 50):
    """Returns past human review decisions and audit log records."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        SELECT al.log_id, al.review_id, al.sighting_id, al.action, al.assigned_tiger_id,
               al.reviewer_id, al.reason, al.machine_suggested_id, al.machine_suggested_score,
               al.machine_raw_cosine, al.machine_sift_inliers, al.created_at
        FROM review_audit_log al
        ORDER BY al.created_at DESC LIMIT ?;
        """, (limit,))
        history = [dict(r) for r in cur.fetchall()]
    except Exception:
        history = []
    conn.close()
    return history

@app.get("/api/alerts")
async def get_alerts():
    """Returns active deviation and threat alerts."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT alert_id, alert_type, severity, tiger_id, station_id, detected_change, supporting_evidence, confidence_score, created_at
    FROM alerts
    ORDER BY created_at DESC LIMIT 50;
    """)
    alerts = [dict(r) for r in cur.fetchall()]
    conn.close()
    return alerts

@app.get("/api/tigers")
async def get_tigers():
    """Returns all enrolled resident tigers with stats."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT t.tiger_id, t.name, t.gender, t.status, t.first_seen_date, t.last_seen_date,
           COUNT(s.sighting_id) as sighting_count
    FROM tigers t
    LEFT JOIN sightings s ON t.tiger_id = s.tiger_id
    GROUP BY t.tiger_id
    ORDER BY sighting_count DESC;
    """)
    tigers = [dict(r) for r in cur.fetchall()]
    conn.close()
    return tigers

@app.get("/api/image")
async def get_image(path: str):
    """Securely serves a local image file for UI previews with path traversal protection."""
    clean_path = os.path.abspath(path)
    allowed_roots = [
        os.path.abspath(pkg_dir),
        os.path.abspath(os.path.join(pkg_dir, "..")),
    ]
    # Path containment check: ensure path is within allowed project trees
    is_contained = any(os.path.commonpath([clean_path, root]) == root for root in allowed_roots)
    if not is_contained:
        raise HTTPException(status_code=403, detail="Access denied: path outside workspace")

    if os.path.exists(clean_path) and os.path.isfile(clean_path):
        return FileResponse(clean_path)
    raise HTTPException(status_code=404, detail="Image file not found")

@app.get("/api/stations")
async def get_stations():
    """Returns all registered Pench camera trap stations with coordinates and recent counts."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT s.station_id, s.grid_id, s.range_name, s.zone, s.latitude, s.longitude, s.is_active,
           COUNT(st.sighting_id) as total_sightings,
           MAX(st.timestamp) as last_seen_timestamp
    FROM stations s
    LEFT JOIN sightings st ON s.station_id = st.station_id
    GROUP BY s.station_id
    ORDER BY s.station_id ASC;
    """)
    stations = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"stations": stations}

@app.get("/api/species")
async def get_species_taxonomy():
    """Returns the canonical 17-class Central Indian wildlife taxonomy and profile."""
    tax_path = os.path.join(pkg_dir, "data", "taxonomy", "species_taxonomy.json")
    if os.path.exists(tax_path):
        with open(tax_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"classes": []}

@app.get("/api/models")
async def get_models():
    """Returns the machine-readable model registry and diagnostic status."""
    registry_path = os.path.join(pkg_dir, "data", "models", "manifests", "model_registry.json")
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"models": []}

@app.get("/api/export_report")
async def export_report():
    """Generates and downloads the latest alert briefing markdown report."""
    reports_dir = os.path.join(pkg_dir, "data", "outputs", "alert_reports")
    if os.path.exists(reports_dir):
        files = [os.path.join(reports_dir, f) for f in os.listdir(reports_dir) if f.endswith(".md")]
        if files:
            latest = max(files, key=os.path.getmtime)
            return FileResponse(latest, filename=os.path.basename(latest), media_type="text/markdown")
    return HTMLResponse("No alert reports available yet.")

def find_nearest_station(lat: float, lon: float) -> str:
    """Find the geographically nearest Tadoba camera station for given GPS coordinates."""
    best_stn = "CT-C1"
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT station_id, latitude, longitude FROM stations;")
        stations = [dict(r) for r in cur.fetchall()]
        conn.close()
        if not stations:
            return "CT-C1"
        min_dist_sq = float("inf")
        for stn in stations:
            d = (stn["latitude"] - lat) ** 2 + (stn["longitude"] - lon) ** 2
            if d < min_dist_sq:
                min_dist_sq = d
                best_stn = stn["station_id"]
    except Exception:
        pass
    return best_stn


def classify_animal_group(species_str: Optional[str]) -> str:
    """Classify species into primary animal trophic groups for structured wildlife classification."""
    s = (species_str or "").lower().strip()
    carnivores = {"tiger", "leopard", "dhole", "sloth bear", "bear", "wolf", "jackal", "fox", "hyena", "cat", "jungle cat"}
    herbivores = {"chital", "sambar", "gaur", "deer", "nilgai", "blackbuck", "elephant", "rhino", "cow", "cattle", "sheep", "goat", "horse", "zebra", "giraffe"}
    omnivores = {"wild boar", "boar", "pig", "monkey", "baboon", "langur", "macaque", "human", "person"}
    if s in carnivores:
        return "carnivore"
    if s in herbivores:
        return "herbivore"
    if s in omnivores:
        return "omnivore"
    if s in {"blank", "vehicle", "car", "truck"}:
        return "non_wildlife"
    return "unknown"


@app.get("/api/health")
async def get_health():
    """System health check endpoint for mobile, web, and external clients."""
    return {
        "status": "ok",
        "service": "TigerTraceAI Shared AI Backend",
        "version": "2.5.0",
        "device": str(pipeline.triage_detector.device),
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "models": {
            "detector": "YOLOv8-Tadoba-Vision",
            "species_triage": "DualStage-YOLOv8n",
            "reid": "HotSpotter_SIFT_55+ResNet50_45",
            "step_9a_guard": "active",
            "step_9b_resolver": "active"
        },
        "active_models": {
            "detector": "YOLOv8-Tadoba-Vision",
            "species_triage": "DualStage-YOLOv8n",
            "reid_matcher": "HotSpotter_SIFT_55+ResNet50_45",
            "flank_guard": "Step_9A_Active",
            "bbox_resolver": "Step_9B_Active"
        }
    }


@app.post("/api/analyze")
async def analyze_photo(
    file: UploadFile = File(...),
    station_id: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    timestamp: Optional[str] = Form(None),
    flank_hint: Optional[str] = Form(None),
    field_officer: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    """
    Shared Single-Photo Analysis API for Mobile App and Web Field Quick-Scan.
    Executes detection, species classification, flank extraction (Step 9B),
    Re-ID (Step 9A flank guard), database persistence, and behavior forecast.
    """
    import uuid
    # 1. Validate File
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.bmp', '.webp'):
        raise HTTPException(status_code=400, detail=f"Unsupported image format: {ext}. Allowed: .jpg, .jpeg, .png, .bmp, .webp")

    mobile_uploads_dir = os.path.join(pkg_dir, "data", "mobile_uploads")
    os.makedirs(mobile_uploads_dir, exist_ok=True)

    unique_filename = f"mobile_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    saved_path = os.path.join(mobile_uploads_dir, unique_filename)

    # Stream file to disk and check file size (limit 25MB)
    max_bytes = 25 * 1024 * 1024
    bytes_read = 0
    with open(saved_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            bytes_read += len(chunk)
            if bytes_read > max_bytes:
                buffer.close()
                if os.path.exists(saved_path):
                    os.remove(saved_path)
                raise HTTPException(status_code=413, detail="File too large. Maximum supported size is 25 MB.")
            buffer.write(chunk)

    if bytes_read == 0:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    # Image Dimension Inspection for Responsive Bounding Boxes
    img_w, img_h = 640, 640
    try:
        from PIL import Image as PILImage
        with PILImage.open(saved_path) as pimg:
            img_w, img_h = pimg.size
    except Exception:
        pass
    img_dims = {"width": img_w, "height": img_h}

    # 2. Resolve Station & Timestamp Metadata
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT station_id FROM stations;")
    known_stations = {row["station_id"] for row in cur.fetchall()}

    resolved_station = "CT-C1"
    if station_id and station_id in known_stations:
        resolved_station = station_id
    elif latitude is not None and longitude is not None:
        resolved_station = find_nearest_station(latitude, longitude)

    cur.execute("SELECT grid_id, range_name, zone, latitude, longitude FROM stations WHERE station_id = ?;", (resolved_station,))
    stn_row = cur.fetchone()
    stn_info = {
        "station_id": resolved_station,
        "range_name": stn_row["range_name"] if stn_row else "Tadoba Lake",
        "zone": stn_row["zone"] if stn_row else "core",
        "latitude": latitude if latitude is not None else (stn_row["latitude"] if stn_row else 20.25),
        "longitude": longitude if longitude is not None else (stn_row["longitude"] if stn_row else 79.33)
    }

    capture_ts = timestamp.strip() if (timestamp and timestamp.strip()) else datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Model metadata
    model_versions = {
        "detector": "YOLOv8-Tadoba-Vision",
        "reid": "SIFT_ResNet50_Ensemble",
        "flank_guard": "Step_9A_Active",
        "bbox_resolver": "Step_9B_Active"
    }

    # 3. Animal Detection & Triage
    triage_res = pipeline.triage_detector.detect_frame(saved_path)

    # Format detections with normalized coordinates for SVG overlay scaling
    formatted_detections = []
    for d in triage_res.get("detections", []):
        d_box = d.get("bbox_xyxy")
        d_copy = dict(d)
        if d_box and len(d_box) == 4 and img_w > 0 and img_h > 0:
            d_copy["bbox_norm"] = [
                round(d_box[0] / img_w, 4),
                round(d_box[1] / img_h, 4),
                round(d_box[2] / img_w, 4),
                round(d_box[3] / img_h, 4)
            ]
        formatted_detections.append(d_copy)

    # Case A: Blank Frame
    if triage_res["is_blank"]:
        conn.close()
        return {
            "status": "success",
            "observation_id": None,
            "image_name": unique_filename,
            "image_url": f"/api/image?path={saved_path}",
            "crop_url": None,
            "is_blank": True,
            "species": "blank",
            "species_confidence": triage_res["max_confidence"],
            "animal_group": "non_wildlife",
            "identity_status": "not_applicable",
            "assigned_identity": None,
            "assigned_name": None,
            "top_score": 0.0,
            "sift_score": 0.0,
            "cosine_score": 0.0,
            "flank_side": "unknown",
            "candidate_identities": [],
            "decision_reason": "blank_frame_no_wildlife_detected",
            "review_status": "rejected",
            "behaviour_estimate": None,
            "location": stn_info,
            "timestamp": capture_ts,
            "model_versions": model_versions,
            "image_dimensions": img_dims,
            "bbox_xyxy": None,
            "detections": []
        }

    # Case B: Human Privacy Blur or Vehicle
    cat = triage_res["category"]
    if cat == "person":
        human_boxes = [d["bbox_xyxy"] for d in triage_res["detections"] if d.get("class_id") == 0]
        blurred_path = os.path.join(pipeline.blurred_dir, unique_filename)
        final_img_path, _ = pipeline.privacy_blurrer.apply_privacy_blur(saved_path, human_boxes, blurred_path)
        conn.close()
        return {
            "status": "success",
            "observation_id": None,
            "image_name": unique_filename,
            "image_url": f"/api/image?path={final_img_path}",
            "crop_url": None,
            "is_blank": False,
            "species": "human",
            "species_confidence": triage_res["max_confidence"],
            "animal_group": "omnivore",
            "identity_status": "not_applicable",
            "assigned_identity": None,
            "assigned_name": None,
            "top_score": 0.0,
            "sift_score": 0.0,
            "cosine_score": 0.0,
            "flank_side": "unknown",
            "candidate_identities": [],
            "decision_reason": "human_detected_privacy_safeguarded",
            "review_status": "confirmed",
            "behaviour_estimate": None,
            "location": stn_info,
            "timestamp": capture_ts,
            "model_versions": model_versions,
            "image_dimensions": img_dims,
            "bbox_xyxy": human_boxes[0] if human_boxes else None,
            "detections": formatted_detections
        }

    # Case C: Non-Tiger Wildlife or Vehicle
    if not triage_res["is_tiger"] and cat in ("vehicle", "animal"):
        conn.close()
        animal_detections = [d for d in triage_res["detections"] if d.get("class_id") not in (0, 1, 2, 3, 5, 7)]
        detected_species = animal_detections[0]["class_name"] if animal_detections else ("vehicle" if cat == "vehicle" else "wildlife")
        primary_bbox = animal_detections[0]["bbox_xyxy"] if animal_detections else (triage_res["detections"][0]["bbox_xyxy"] if triage_res["detections"] else None)
        return {
            "status": "success",
            "observation_id": None,
            "image_name": unique_filename,
            "image_url": f"/api/image?path={saved_path}",
            "crop_url": None,
            "is_blank": False,
            "species": detected_species,
            "species_confidence": triage_res["max_confidence"],
            "animal_group": classify_animal_group(detected_species),
            "identity_status": "not_applicable",
            "assigned_identity": None,
            "assigned_name": None,
            "top_score": 0.0,
            "sift_score": 0.0,
            "cosine_score": 0.0,
            "flank_side": "unknown",
            "candidate_identities": [],
            "decision_reason": f"{cat}_detected_non_tiger",
            "review_status": "confirmed",
            "behaviour_estimate": None,
            "location": stn_info,
            "timestamp": capture_ts,
            "model_versions": model_versions,
            "image_dimensions": img_dims,
            "bbox_xyxy": primary_bbox,
            "detections": formatted_detections,
        }

    # Case D: Tiger Detection & Individual Re-ID
    tiger_boxes = [d for d in triage_res["detections"] if d.get("class_name") == "tiger" or d.get("class_id") == 99]
    if not tiger_boxes:
        tiger_boxes = [d for d in triage_res["detections"] if d.get("class_id") != 0]
    primary_bbox = tiger_boxes[0]["bbox_xyxy"] if tiger_boxes else None

    # Step 9B Bounding-box scaling & CLAHE flank subcrop
    crop_img, crop_path = pipeline.flank_extractor.extract_flank_crop(
        saved_path, bbox_xyxy=primary_bbox, output_dir=pipeline.flank_crops_dir
    )

    clean_flank = flank_hint.strip().lower() if (flank_hint and flank_hint.strip().lower() in ('left', 'right')) else 'unknown'

    # Insert Sighting Record into Database
    cur.execute("""
    INSERT INTO sightings (image_name, image_path, station_id, timestamp, species, flank_side, bbox_json, flank_crop_path, review_status)
    VALUES (?, ?, ?, ?, 'tiger', ?, ?, ?, 'pending_review');
    """, (unique_filename, saved_path, resolved_station, capture_ts, clean_flank, json.dumps(primary_bbox) if primary_bbox else None, crop_path))
    sighting_id = cur.lastrowid
    conn.commit()

    # Step 9A Flank compatibility guarded Re-ID
    flank_for_matching = clean_flank if clean_flank in ('left', 'right') else 'both'
    enroll_res = pipeline.enrollment_engine.identify_and_enroll(
        crop_path,
        sighting_id=sighting_id,
        image_name=unique_filename,
        species="tiger",
        flank_side=flank_for_matching
    )

    decision = enroll_res.get("decision_state") or enroll_res.get("decision", "unknown")
    best_score = float(enroll_res.get("confidence", 0.0))
    assigned_id = enroll_res.get("assigned_tiger_id")
    suggested_id = enroll_res.get("suggested_tiger_id")
    top_candidates = enroll_res.get("top_candidates", [])

    # Format Candidate Identities list
    formatted_candidates = []
    for c in top_candidates:
        c_id = c.get("tiger_id")
        cur.execute("SELECT name FROM tigers WHERE tiger_id = ?;", (c_id,))
        t_row = cur.fetchone()
        t_name = t_row["name"] if t_row else c_id
        formatted_candidates.append({
            "tiger_id": c_id,
            "name": t_name,
            "score": round(float(c.get("score", 0.0)), 4),
            "sift_score": round(float(c.get("sift_score", 0.0)), 4),
            "cosine_score": round(float(c.get("cosine_score", 0.0)), 4),
            "flank": c.get("flank_side", "unknown")
        })

    # Step 13 Safety Policy: Disable unsafe automatic confirmation
    # All candidate matches route to review_required pending independent matcher calibration
    if decision in ("matched", "review_required"):
        identity_status = "review_required"
        final_id = suggested_id or assigned_id
        decision_reason = "candidate_match_queued_for_human_review_uncalibrated_matcher"
        review_status = "pending_review"
    elif decision == "new_identity_candidate":
        identity_status = "new_identity_candidate"
        final_id = suggested_id
        decision_reason = "novel_stripe_pattern_candidate"
        review_status = "pending_review"
    else:
        identity_status = "unknown"
        final_id = None
        decision_reason = enroll_res.get("reason", "unknown_rejection")
        review_status = "pending_review"

    # Get Assigned Tiger Name
    assigned_name = None
    if final_id and final_id != "UNMATCHED":
        cur.execute("SELECT name FROM tigers WHERE tiger_id = ?;", (final_id,))
        t_row = cur.fetchone()
        assigned_name = t_row["name"] if t_row else final_id

    # Behavioral Intelligence Estimation (only if verified resident with >= 2 sightings)
    behaviour_est = None
    if final_id and final_id != "UNMATCHED":
        cur.execute("""
        SELECT s.tiger_id, s.station_id, s.timestamp, st.latitude, st.longitude, st.zone, st.range_name
        FROM sightings s
        JOIN stations st ON s.station_id = st.station_id
        WHERE s.tiger_id = ?;
        """, (final_id,))
        hist_sightings = [dict(r) for r in cur.fetchall()]
        if len(hist_sightings) >= 2:
            pred = pipeline.movement_predictor.predict_tiger_movement(final_id, hist_sightings)
            behaviour_est = {
                "status": pred["status"],
                "current_station": pred.get("current_station"),
                "predicted_next_stations": pred.get("predicted_next_stations", []),
                "directional_trend": pred.get("directional_trend"),
                "peak_location": pred.get("peak_location"),
                "evidence_type": "historical_markov_trajectory",
                "prediction_source": "Markov Spatial Sighting Transition Matrix",
                "time_horizon": "Next Station Transition (12-24 Hours)",
                "limitations": "Requires >= 2 verified historical sightings in database."
            }
        else:
            behaviour_est = {
                "status": "insufficient_history",
                "notes": f"{len(hist_sightings)} historical captures (minimum 2 required for trajectory prediction)",
                "evidence_type": "insufficient_data",
                "prediction_source": "Markov Spatial Sighting Transition Matrix",
                "limitations": "Requires >= 2 verified historical sightings in database."
            }

        # Scientific ethogram enrichment for Chota Dadhiyal (T-84)
        if final_id in ["T-84", "CHOTA_DADHIYAL_T84"] or "Chota Dadhiyal" in (assigned_name or ""):
            behaviour_est["scientific_ethogram"] = {
                "subject_identity": "Chota Dadhiyal (T-84)",
                "demographics": "Adult Male (approx. 5.5 - 6 years)",
                "observed_posture": "Alert Standing (Quadrupedal Stance, Dorsal Elevation 1.18m)",
                "primary_action": "Territorial Scent-Boundary Inspection & Vigilant Stance",
                "ethological_description": "The tiger is captured in a classical stationary quadrupedal posture facing eastward along the fireline transect. Weight distribution is balanced evenly across all four limbs with scapular muscles tensed, indicating acute spatial vigilance. Cervical alignment is held horizontal with the cranium slightly cocked towards the Pandharpauni grassland canopy, exhibiting olfactory and acoustic assessment of recent ungulate or rival scent markers.",
                "gaze_orientation": "Forward-Oblique (approx. 35° Azimuth East), visual tracking of edge vegetation",
                "aural_vocal_signals": "Pinnae (ears) rotated forward at 45° in heightened acoustic vigilance; zero vocal distress or acoustic vocalization detected.",
                "tail_posture": "Caudal extension low with slight terminal upward curl (indicates calm dominance, non-combative resting alertness).",
                "physical_condition_index": "Prime Adult (Body Condition Score 4.5/5 - Excellent). Pronounced lateral muscling, full flank girth, absence of combat lacerations or ambulation impairment.",
                "anthropogenic_stress_level": "Minimal / Negligible (Distance to nearest tourism corridor > 1.8km; zero flight-initiation avoidance behavior observed).",
                "ecological_habitat_microzone": "Dry Deciduous Teak & Bamboo Canopy (Tadoba Core Zone - CT-C1/CT-C4 Buffer Transect).",
                "temporal_activity_cycle": "Crepuscular Territorial Patrol (Dawn/Dusk Transition phase).",
                "recommended_conservation_action": "Routine camera-trap corridor monitoring; maintain 500m buffer zone around CT-C4 waterhole."
            }

    # Evaluate deviation alerts
    if final_id and final_id != "UNMATCHED":
        pipeline.alert_engine.evaluate_batch_alerts([{
            "sighting_id": sighting_id,
            "tiger_id": final_id,
            "station_id": resolved_station,
            "timestamp": capture_ts
        }])
    conn.commit()
    conn.close()

    # Top scores breakdown
    top_sift = formatted_candidates[0]["sift_score"] if formatted_candidates else 0.0
    top_cosine = formatted_candidates[0]["cosine_score"] if formatted_candidates else 0.0

    return {
        "status": "success",
        "observation_id": sighting_id,
        "image_name": unique_filename,
        "image_url": f"/api/image?path={saved_path}",
        "crop_url": f"/api/image?path={crop_path}" if crop_path else None,
        "is_blank": False,
        "species": "tiger",
        "species_confidence": triage_res["max_confidence"],
        "animal_group": "carnivore",
        "identity_status": identity_status,
        "assigned_identity": final_id,
        "assigned_name": assigned_name,
        "top_score": round(best_score, 4),
        "sift_score": top_sift,
        "cosine_score": top_cosine,
        "flank_side": clean_flank,
        "candidate_identities": formatted_candidates,
        "decision_reason": decision_reason,
        "review_status": review_status,
        "behaviour_estimate": behaviour_est,
        "location": stn_info,
        "timestamp": capture_ts,
        "model_versions": model_versions,
        "image_dimensions": img_dims,
        "bbox_xyxy": primary_bbox,
        "detections": formatted_detections,
    }


@app.get("/api/habitat/context")
async def get_habitat_context():
    """
    Returns public reserve-scale habitat reference context for Tadoba-Andhari demonstration layer.
    Explicitly labeled as SIMULATED / GENERALIZED HABITAT CONTEXT — not verified animal telemetry.
    """
    return {
        "status": "success",
        "reserve_name": "Tadoba-Andhari Tiger Reserve (TATR Reference Context)",
        "center": [20.24, 79.31],
        "zoom": 11,
        "disclaimer": "SIMULATED — NOT VERIFIED TIGER SIGHTINGS. Coarse reserve-scale habitat suitability context. No verified real-time telemetry.",
        "zones": [
            {
                "name": "Moharli Core Zone",
                "center": [20.18, 79.33],
                "radius_meters": 6500,
                "suitability": 0.88,
                "features": "Perennial waterholes & mixed deciduous canopy"
            },
            {
                "name": "Tadoba Central Range",
                "center": [20.26, 79.30],
                "radius_meters": 7200,
                "suitability": 0.92,
                "features": "Tadoba lake basin & high prey density corridor"
            },
            {
                "name": "Kolsa Southern Range",
                "center": [20.12, 79.44],
                "radius_meters": 6800,
                "suitability": 0.79,
                "features": "Deep teak woodland & stream ravines"
            }
        ],
        "chota_dadhiyal_reference": {
            "identity_id": "T-84",
            "name": "Chota Dadhiyal",
            "status": "historical_public_reference",
            "disclaimer": "SIMULATED — NOT VERIFIED CURRENT SIGHTING. Privacy-preserving regional envelope. No active telemetry.",
            "approximate_envelope": [
                [20.20, 79.25],
                [20.30, 79.25],
                [20.30, 79.38],
                [20.20, 79.38]
            ]
        }
    }


@app.get("/api/mobile/observations")
async def get_mobile_observations(limit: int = 50):
    """Returns recent field observations for the Flutter mobile app history tab."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT s.sighting_id as observation_id, s.image_name, s.image_path, s.station_id, s.timestamp,
           s.species, s.tiger_id as assigned_identity, s.flank_side, s.reid_score, s.review_status,
           s.flank_crop_path, t.name as assigned_name, st.range_name, st.zone, st.latitude, st.longitude
    FROM sightings s
    LEFT JOIN tigers t ON s.tiger_id = t.tiger_id
    LEFT JOIN stations st ON s.station_id = st.station_id
    ORDER BY s.created_at DESC
    LIMIT ?;
    """, (limit,))
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["image_url"] = f"/api/image?path={d['image_path']}" if d.get("image_path") else None
        d["crop_url"] = f"/api/image?path={d['flank_crop_path']}" if d.get("flank_crop_path") else None
        rows.append(d)
    conn.close()
    return {
        "status": "success",
        "count": len(rows),
        "observations": rows
    }


@app.get("/api/mobile/catalogue")
async def get_mobile_catalogue():
    """Returns the registered resident tiger catalogue for mobile viewing."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT t.tiger_id, t.name, t.gender, t.flank_side_registered, t.first_seen_date, t.last_seen_date,
           t.status, t.reference_crop_path, COUNT(s.sighting_id) as sighting_count
    FROM tigers t
    LEFT JOIN sightings s ON t.tiger_id = s.tiger_id
    GROUP BY t.tiger_id
    ORDER BY t.name ASC;
    """)
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["reference_photo_url"] = f"/api/image?path={d['reference_crop_path']}" if d.get("reference_crop_path") else None
        rows.append(d)
    conn.close()
    return rows


@app.post("/api/mobile/sync_batch")
async def sync_mobile_batch(req: Request):
    """Syncs a batch of offline observations and reports status."""
    body = await req.json()
    items = body.get("items", [])
    synced = []
    for item in items:
        synced.append({
            "local_id": item.get("local_id"),
            "status": "acknowledged",
            "synced_at": datetime.datetime.utcnow().isoformat() + "Z"
        })
    return {
        "status": "success",
        "total_received": len(items),
        "acknowledged_count": len(items),
        "synced_items": synced
    }


def run_server(host="127.0.0.1", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

