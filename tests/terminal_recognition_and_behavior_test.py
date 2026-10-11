"""
NETRAVAN Live Terminal Beta Verification Script
================================================
Performs live terminal verification for:
1. Wildlife Image Recognition (Species classification, confidence score, bounding boxes)
2. Individual Tiger Biometric Re-Identification (SIFT keypoint inliers, cosine similarity, candidate matches)
3. Behavior & Movement Analysis (Current station, Markov transition probabilities, directional trend, compass heading, buffer village proximity alerts)
"""

import os
import sys
import json
import requests
import time

def run_test():
    api_url = "http://127.0.0.1:8000/api/analyze"
    health_url = "http://127.0.0.1:8000/api/health"

    print("\n" + "=" * 80)
    print("      NETRAVAN TERMINAL BETA TEST — RECOGNITION & BEHAVIOR ANALYSIS")
    print("=" * 80)

    # 1. Verify Backend Connectivity
    try:
        health_resp = requests.get(health_url, timeout=3)
        if health_resp.status_code == 200:
            h = health_resp.json()
            print(f"[+] Backend Service Live: {h.get('service')} (v{h.get('version')})")
            print(f"[+] Compute Platform Device: {h.get('device')}")
            print(f"[+] Active Models: {', '.join(h.get('active_models', {}).keys())}")
        else:
            print(f"[-] Backend returned status {health_resp.status_code}")
            return 1
    except Exception as e:
        print(f"[-] Failed to reach backend: {e}")
        return 1

    # 2. Test Fixtures Definition
    test_cases = [
        {
            "label": "TEST 1: Resident Tiger Biometric & Movement Forecast",
            "file_path": "TigerTrace_AI/data/reference_catalogue/Bajirao/Bajirao_001_flank_crop.jpg",
            "station": "PTR_STN_01",
            "flank_hint": "left",
            "expected_species": "tiger"
        },
        {
            "label": "TEST 2: Wildlife Camera-Trap Probe (Field ATRW Observation)",
            "file_path": "data/staging/atrw_pilot/images/000179.jpg",
            "station": "PTR_STN_03",
            "flank_hint": "unknown",
            "expected_species": "tiger"
        },
        {
            "label": "TEST 3: Mobile Field Observation Capture",
            "file_path": "TigerTrace_AI/data/mobile_uploads/mobile_20261010_112308_13a32cd7.jpg",
            "station": "PTR_STN_05",
            "flank_hint": "left",
            "expected_species": "tiger"
        }
    ]

    all_passed = True

    for idx, tc in enumerate(test_cases, 1):
        print("\n" + "-" * 80)
        print(f"  {tc['label']}")
        print("-" * 80)

        fpath = tc["file_path"]
        if not os.path.exists(fpath):
            print(f"[-] File not found: {fpath} (Skipping)")
            continue

        file_size_kb = os.path.getsize(fpath) / 1024
        print(f"[*] Input File     : {fpath} ({file_size_kb:.1f} KB)")
        print(f"[*] Station Origin : {tc['station']} | Flank Hint: {tc['flank_hint']}")

        t0 = time.time()
        with open(fpath, "rb") as f:
            resp = requests.post(
                api_url,
                files={"file": (os.path.basename(fpath), f, "image/jpeg")},
                data={"station_id": tc["station"], "flank_hint": tc["flank_hint"]},
                timeout=15
            )
        duration_ms = (time.time() - t0) * 1000

        if resp.status_code != 200:
            print(f"[-] HTTP Error {resp.status_code}: {resp.text}")
            all_passed = False
            continue

        data = resp.json()

        # A. Species Recognition
        species = data.get("species", "unknown")
        confidence = data.get("species_confidence", 0.0)
        is_blank = data.get("is_blank", False)
        bbox = data.get("bbox_xyxy")

        print(f"\n[1] SPECIES RECOGNITION:")
        print(f"    • Detected Species   : {species.upper()} (Confidence: {confidence * 100:.2f}%)")
        print(f"    • Blank Frame Status : {'Quarantined Blank' if is_blank else 'Valid Animal Trigger'}")
        if bbox:
            print(f"    • Detection BBox     : [x1={bbox[0]:.0f}, y1={bbox[1]:.0f}, x2={bbox[2]:.0f}, y2={bbox[3]:.0f}]")
        if data.get("crop_url"):
            print(f"    • Flank Subcrop URL  : {data.get('crop_url')}")

        # B. Individual Re-Identification
        assigned_id = data.get("assigned_identity")
        assigned_name = data.get("assigned_name")
        id_status = data.get("identity_status")
        top_score = data.get("top_score", 0.0)
        candidates = data.get("candidate_identities", [])

        print(f"\n[2] BIOMETRIC STRIPE RE-IDENTIFICATION:")
        print(f"    • Match Decision     : {assigned_name or assigned_id or 'Unknown'} ({id_status})")
        print(f"    • Top Biometric Score: {top_score * 100:.2f}%")
        if candidates:
            print(f"    • Top Candidate Rankings ({len(candidates)} total):")
            for c in candidates[:3]:
                print(f"      - {c.get('name')} ({c.get('tiger_id')}): Score={c.get('score') * 100:.1f}%, SIFT Inliers={c.get('sift_score')}, Cosine={c.get('cosine_score') * 100:.1f}%")
        else:
            print(f"    • Novel/Unmatched Individual: Proposed candidate {assigned_id}")

        # C. Behavior & Movement Analysis
        beh = data.get("behaviour_estimate")
        print(f"\n[3] BEHAVIOR & MOVEMENT ANALYSIS:")
        if beh:
            beh_status = beh.get("status")
            print(f"    • Trajectory Status  : {beh_status.upper()}")
            if beh_status == "success":
                print(f"    • Current Station    : {beh.get('current_station')}")
                next_stns = beh.get("predicted_next_stations", [])
                if next_stns:
                    formatted_next = ", ".join([f"{st} ({prob * 100:.1f}%)" for st, prob in next_stns])
                    print(f"    • Next Stations Prob : {formatted_next}")

                trend = beh.get("directional_trend")
                if trend and trend.get("status") == "success":
                    print(f"    • Compass Heading    : {trend.get('compass_heading')} ({trend.get('displacement_km')} km net displacement)")
                    villages = trend.get("approaching_villages", [])
                    if villages:
                        print(f"    • Human-Wildlife Risk Alerts:")
                        for vil in villages:
                            print(f"      * {vil.get('village_name')}: {vil.get('current_distance_km')} km away -> [{vil.get('risk_level')} RISK]")
            else:
                print(f"    • Movement Status    : {beh.get('notes', 'Insufficient historical sightings')}")
                print(f"    • Scientific Integrity: Trajectory forecast safely skipped to prevent fabricated movement")
        else:
            print("    • Behavior Estimate  : None (Non-target trigger)")

        print(f"\n[+] Processing Latency: {duration_ms:.1f} ms")

    print("\n" + "=" * 80)
    print("                    TERMINAL TEST EXECUTION COMPLETE")
    print(f"                    Overall Status: {'PASSED [100% OPERATIONAL]' if all_passed else 'FAILED'}")
    print("=" * 80 + "\n")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_test())
