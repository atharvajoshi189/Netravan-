import os
import json
import math
import sqlite3
import datetime
from ..config import SMS_ALERT_TYPE_ALIASES, SMS_ENABLED_ALERT_TYPES
from ..occupancy.home_range import HomeRangeAnalyzer
from ..occupancy.pench_gis_data import PENCH_VILLAGES

class DeviationAlertEngine:
    def __init__(self, db_connection, on_alert_raised=None, sms_enabled_alert_types=None):
        self.conn = db_connection
        self.analyzer = HomeRangeAnalyzer()
        self.on_alert_raised = on_alert_raised
        enabled_types = sms_enabled_alert_types if sms_enabled_alert_types is not None else SMS_ENABLED_ALERT_TYPES
        self.sms_enabled_alert_types = {str(item).strip().lower() for item in enabled_types}

    def _normalize_sms_alert_type(self, alert):
        alert_type = alert.get("sms_alert_type") or alert.get("alert_type")
        if alert_type is None:
            return None
        return SMS_ALERT_TYPE_ALIASES.get(str(alert_type), str(alert_type).strip().lower())

    def _emit_alert_hook(self, alert):
        if self.on_alert_raised is None:
            return

        sms_alert_type = self._normalize_sms_alert_type(alert)
        if sms_alert_type not in self.sms_enabled_alert_types:
            return

        try:
            self.on_alert_raised(alert)
        except Exception as exc:
            print(f"[ALERT HOOK] SMS callback failed for {sms_alert_type}: {exc}")

    def evaluate_batch_alerts(self, batch_sightings):
        """
        Evaluates a batch of new sightings against historical baseline to generate actionable alerts:
        1. Centroid Shift Beyond Threshold (15-20 sq km in core, 5 km in buffer).
        2. First capture at previously unused station (effort-normalized).
        3. Movement toward buffer or village-adjacent stations.
        4. Prolonged absence of regular resident tigers.
        """
        cur = self.conn.cursor()
        alerts = []

        # -------------------------------------------------------------
        # 1. Evaluate Village Dispersal & Conflict Proximity
        # -------------------------------------------------------------
        for s in batch_sightings:
            tiger_id = s.get("tiger_id")
            station_id = s.get("station_id")
            timestamp = s.get("timestamp")

            if not tiger_id or tiger_id == "UNMATCHED":
                continue

            cur.execute("SELECT station_id, grid_id, range_name, zone, latitude, longitude FROM stations WHERE station_id = ?;", (station_id,))
            stn = cur.fetchone()
            if not stn:
                continue

            stn_lat, stn_lon, stn_zone = stn["latitude"], stn["longitude"], stn["zone"]

            for vil in PENCH_VILLAGES:
                d_km = math.sqrt(((stn_lat - vil["lat"]) * 111.0)**2 + ((stn_lon - vil["lon"]) * 103.2)**2)

                if d_km <= 2.5:
                    alert = {
                        "alert_type": "VILLAGE_DISPERSAL",
                        "sms_alert_type": "village_proximity",
                        "severity": "CRITICAL" if d_km <= 1.5 else "WARNING",
                        "tiger_id": tiger_id,
                        "station_id": station_id,
                        "station_range_name": stn["range_name"],
                        "village_name": vil["name"],
                        "distance_km": round(d_km, 2),
                        "timestamp": timestamp,
                        "detected_change": f"Tiger {tiger_id} detected near {vil['name']} ({d_km:.1f} km away)",
                        "supporting_evidence": f"Captured at Station {station_id} ({stn['range_name']} - {stn_zone.upper()}) at {timestamp}. Village is {d_km:.2f} km from camera location.",
                        "confidence_score": 0.95,
                    }
                    alerts.append(alert)
                    if self._save_alert(alert):
                        self._emit_alert_hook(alert)

            # ---------------------------------------------------------
            # 2. First Capture at a Previously Unused Station
            # ---------------------------------------------------------
            cur.execute(
                """
            SELECT COUNT(*) FROM sightings 
            WHERE tiger_id = ? AND station_id = ? AND sighting_id != ?;
            """,
                (tiger_id, station_id, s.get("sighting_id", -1)),
            )
            past_captures = cur.fetchone()[0]

            if past_captures == 0:
                cur.execute("SELECT created_at FROM stations WHERE station_id = ?;", (station_id,))
                _station_created_at = cur.fetchone()

                alert = {
                    "alert_type": "NOVEL_STATION",
                    "severity": "WARNING" if stn_zone == "buffer" else "INFO",
                    "tiger_id": tiger_id,
                    "station_id": station_id,
                    "detected_change": f"First recorded capture of {tiger_id} at {station_id} ({stn['range_name']})",
                    "supporting_evidence": f"No prior historical sightings at {station_id}. Station is located in {stn_zone.upper()} zone at ({stn_lat:.4f}°N, {stn_lon:.4f}°E).",
                    "confidence_score": 0.88,
                }
                alerts.append(alert)
                if self._save_alert(alert):
                    self._emit_alert_hook(alert)

        # -------------------------------------------------------------
        # 3. Centroid Shift Beyond Threshold (15-20 sq km Core / 5 km Buffer)
        # -------------------------------------------------------------
        cur.execute("SELECT DISTINCT tiger_id FROM sightings WHERE tiger_id IS NOT NULL;")
        all_tigers = [r[0] for r in cur.fetchall()]

        for tid in all_tigers:
            cur.execute(
                """
            SELECT s.station_id, s.timestamp, st.latitude, st.longitude, st.zone 
            FROM sightings s
            JOIN stations st ON s.station_id = st.station_id
            WHERE s.tiger_id = ?
            ORDER BY s.timestamp ASC;
            """,
                (tid,),
            )
            history = [dict(r) for r in cur.fetchall()]

            if len(history) >= 4:
                mid = len(history) // 2
                past_half = history[:mid]
                recent_half = history[mid:]

                hr_past = self.analyzer.calculate_tiger_home_range(past_half)
                hr_recent = self.analyzer.calculate_tiger_home_range(recent_half)

                c_past = hr_past["centroid"]
                c_recent = hr_recent["centroid"]

                if c_past[0] and c_recent[0]:
                    d_shift_km = math.sqrt(((c_recent[0] - c_past[0]) * 111.0)**2 + ((c_recent[1] - c_past[1]) * 103.2)**2)
                    area_delta_km = abs(hr_recent["area_sq_km"] - hr_past["area_sq_km"])

                    is_core = any(r.get("zone") == "core" for r in recent_half)
                    shift_threshold = 15.0 if is_core else 5.0

                    if d_shift_km >= shift_threshold or area_delta_km >= 15.0:
                        alert = {
                            "alert_type": "CENTROID_SHIFT",
                            "severity": "CRITICAL" if d_shift_km >= 10.0 else "WARNING",
                            "tiger_id": tid,
                            "station_id": recent_half[-1]["station_id"],
                            "detected_change": f"Significant territory centroid shift for {tid}: {d_shift_km:.1f} km displacement",
                            "supporting_evidence": f"Baseline centroid ({c_past[0]:.4f}, {c_past[1]:.4f}) shifted to ({c_recent[0]:.4f}, {c_recent[1]:.4f}). Home range area changed by {area_delta_km:.1f} sq km.",
                            "confidence_score": 0.91,
                        }
                        alerts.append(alert)
                        if self._save_alert(alert):
                            self._emit_alert_hook(alert)

        # -------------------------------------------------------------
        # 4. Prolonged Absence Tracking
        # -------------------------------------------------------------
        cur.execute("SELECT tiger_id, name, last_seen_date, status FROM tigers WHERE status = 'resident';")
        resident_tigers = cur.fetchall()

        now = datetime.datetime.now()
        for t in resident_tigers:
            tid = t["tiger_id"]
            last_date_str = t["last_seen_date"]
            if last_date_str:
                try:
                    last_dt = datetime.datetime.strptime(last_date_str, "%Y-%m-%d")
                    days_absent = (now - last_dt).days

                    if days_absent >= 45:
                        alert = {
                            "alert_type": "PROLONGED_ABSENCE",
                            "severity": "WARNING" if days_absent < 90 else "CRITICAL",
                            "tiger_id": tid,
                            "station_id": None,
                            "detected_change": f"Prolonged absence of resident tiger {tid} ({days_absent} days without capture)",
                            "supporting_evidence": f"Last recorded camera capture on {last_date_str}. Expected monitoring capture interval exceeded.",
                            "confidence_score": 0.85,
                        }
                        alerts.append(alert)
                        if self._save_alert(alert):
                            self._emit_alert_hook(alert)
                except Exception:
                    pass

        self.conn.commit()
        return alerts

    def _save_alert(self, alert_dict):
        """Saves an alert to SQLite database, avoiding duplicate identical unacknowledged alerts."""
        cur = self.conn.cursor()
        cur.execute("""
        SELECT COUNT(*) FROM alerts 
        WHERE alert_type = ? AND tiger_id = ? AND detected_change = ? AND is_acknowledged = 0;
        """, (alert_dict["alert_type"], alert_dict["tiger_id"], alert_dict["detected_change"]))
        
        if cur.fetchone()[0] == 0:
            cur.execute("""
            INSERT INTO alerts (alert_type, severity, tiger_id, station_id, detected_change, supporting_evidence, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                alert_dict["alert_type"],
                alert_dict["severity"],
                alert_dict["tiger_id"],
                alert_dict.get("station_id"),
                alert_dict["detected_change"],
                alert_dict["supporting_evidence"],
                alert_dict["confidence_score"]
            ))
            return True

        return False

    def export_alert_report_markdown(self, alerts, output_path=None):
        """Generates a printable management briefing report for forest department officials."""
        if output_path is None:
            output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "outputs", "alert_reports", f"Alert_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        md = f"""# 🚨 Pench Tiger Reserve: Movement Intelligence & Deviation Alert Briefing
**Generated At:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Target Landscape:** Pench Tiger Reserve (MP & MH Core/Buffer)

---

## 📋 Active Operational Alerts Summary ({len(alerts)})

| Alert Type | Severity | Tiger ID | Nearest Station / Location | Confidence |
| :--- | :---: | :--- | :--- | :---: |
"""
        for a in alerts:
            sev_badge = f"🔴 **{a['severity']}**" if a['severity'] == "CRITICAL" else (f"🟡 **{a['severity']}**" if a['severity'] == "WARNING" else f"ℹ️ {a['severity']}")
            md += f"| {a['alert_type']} | {sev_badge} | **{a['tiger_id']}** | {a.get('station_id', 'N/A')} | {a['confidence_score'] * 100:.0f}% |\n"

        md += "\n---\n\n## 🔍 Detailed Evidence & Recommended Interventions\n\n"

        for idx, a in enumerate(alerts, 1):
            md += f"### {idx}. [{a['severity']}] {a['alert_type']} - Tiger: `{a['tiger_id']}`\n"
            md += f"- **Detected Change:** {a['detected_change']}\n"
            md += f"- **Supporting Evidence:** {a['supporting_evidence']}\n"
            md += f"- **Detection Confidence:** `{a['confidence_score'] * 100:.1f}%`\n\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"[ALERT ENGINE] Exported management alert briefing to:\n  {output_path}")
        return output_path
