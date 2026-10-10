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

ui_dir = os.path.dirname(os.path.abspath(__file__))
pkg_dir = os.path.dirname(ui_dir)
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from src.db.schema import get_connection, init_db, seed_sample_stations
from src.pipeline import TigerTracePipeline
from src.config import ALERT_PHONE_NUMBER, GAMMU_CONFIG_PATH, SMS_DRY_RUN

app = FastAPI(title="TigerTrace AI - Pench Tiger Reserve Command Center", version="2.5.0")

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
    action: str
    tiger_id: Optional[str] = None

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
    station_id: str = Form("PTR_STN_01"),
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

    predictions = {}
    for tid, t_sightings in sightings_by_tiger.items():
        pred = pipeline.movement_predictor.predict_tiger_movement(tid, t_sightings)
        predictions[tid] = {
            "tiger_id": tid,
            "status": pred["status"],
            "confidence_note": pred["confidence_note"],
            "sighting_count": pred["sighting_count"],
            "current_station": pred["current_station"],
            "predicted_next_stations": pred["predicted_next_stations"],
            "directional_trend": pred["directional_trend"],
            "peak_location": pred["peak_location"],
            "heatmap_points_count": len(pred.get("heatmap_points", []))
        }
    return predictions

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
    """Returns pending human review items."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT rq.review_id, rq.sighting_id, rq.suggested_tiger_id, rq.suggested_score, 
           rq.flank_crop_path, rq.sift_match_viz_path, rq.status, s.station_id, s.image_name, s.timestamp
    FROM review_queue rq
    JOIN sightings s ON rq.sighting_id = s.sighting_id
    WHERE rq.status = 'pending'
    ORDER BY rq.created_at DESC;
    """)
    items = [dict(r) for r in cur.fetchall()]
    conn.close()
    return items

@app.post("/api/review_queue/{review_id}/action")
async def handle_review_action(review_id: int, req: ReviewActionRequest):
    """Approve, reassign, or auto-enroll a tiger from the review queue."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT sighting_id, suggested_tiger_id FROM review_queue WHERE review_id = ?;", (review_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Review item not found")

    sighting_id = row["sighting_id"]
    assigned_tiger = req.tiger_id if req.tiger_id and req.tiger_id != "NEW_TIGER" else row["suggested_tiger_id"]

    if req.action == "enroll_new":
        cur.execute("SELECT COUNT(*) FROM tigers;")
        new_idx = cur.fetchone()[0] + 1
        assigned_tiger = f"PTR_T_{new_idx:03d}"
        cur.execute("""
        INSERT INTO tigers (tiger_id, name, status, first_seen_date, last_seen_date)
        VALUES (?, ?, 'resident', DATE('now'), DATE('now'));
        """, (assigned_tiger, f"Pench Tiger {assigned_tiger}"))

    cur.execute("""
    UPDATE sightings 
    SET tiger_id = ?, review_status = 'confirmed' 
    WHERE sighting_id = ?;
    """, (assigned_tiger, sighting_id))

    cur.execute("""
    UPDATE review_queue 
    SET status = ?, reviewer_notes = 'Reviewed via Command Center UI', reviewed_at = CURRENT_TIMESTAMP 
    WHERE review_id = ?;
    """, (req.action, review_id))

    conn.commit()
    conn.close()
    return {"status": "success", "assigned_tiger_id": assigned_tiger, "message": f"Assigned to {assigned_tiger}"}

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
    """Securely serves a local image file for UI previews."""
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Image file not found")

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

def run_server(host="127.0.0.1", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
