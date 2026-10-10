import os
import json
import sqlite3
import numpy as np
from .stripe_matcher import StripeReIDMatcher

class TigerEnrollmentEngine:
    def __init__(self, db_connection, high_confidence_threshold=0.5, low_confidence_threshold=0.35, viz_dir=None):
        self.conn = db_connection
        self.high_thresh = high_confidence_threshold
        self.low_thresh = low_confidence_threshold
        self.matcher = StripeReIDMatcher(use_deep_embedding=True)
        
        if viz_dir is None:
            self.viz_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "review_visualizations")
        else:
            self.viz_dir = viz_dir
        os.makedirs(self.viz_dir, exist_ok=True)

    def load_catalogue(self):
        """Loads all enrolled reference tigers and their reference flank crops from the database."""
        cur = self.conn.cursor()
        cur.execute("SELECT tiger_id, name, gender, reference_crop_path, stripe_features_json FROM tigers;")
        rows = cur.fetchall()
        catalogue = []
        for r in rows:
            catalogue.append({
                "tiger_id": r["tiger_id"],
                "name": r["name"],
                "gender": r["gender"],
                "crop_path": r["reference_crop_path"],
                "features": json.loads(r["stripe_features_json"]) if r["stripe_features_json"] else None
            })
        return catalogue

    def seed_initial_catalogue_from_folder(self, catalogue_folder):
        """
        Seeds known resident tigers into SQLite from reference catalogue images
        (e.g., Bajirao, Collarwali, Patdev, L-Mark, Swastik, Karmajhiri).
        """
        if not os.path.exists(catalogue_folder):
            return 0

        cur = self.conn.cursor()
        enrolled_count = 0

        for tiger_name in os.listdir(catalogue_folder):
            tiger_dir = os.path.join(catalogue_folder, tiger_name)
            if os.path.isdir(tiger_dir):
                crops = [f for f in sorted(os.listdir(tiger_dir)) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if crops:
                    ref_crop = os.path.join(tiger_dir, crops[0])
                    tiger_id = tiger_name.upper().replace("-", "_").replace(" ", "_")
                    
                    # Extract reference deep embedding
                    emb = self.matcher.extract_deep_embedding(ref_crop)
                    emb_json = json.dumps(emb.tolist()) if emb is not None else None

                    gender = "F" if "collarwali" in tiger_name.lower() or "patdev" in tiger_name.lower() else "M"
                    
                    cur.execute("""
                    INSERT OR REPLACE INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, reference_crop_path, stripe_features_json, status)
                    VALUES (?, ?, ?, 'both', '2021-01-01', ?, ?, 'resident');
                    """, (tiger_id, tiger_name, gender, ref_crop, emb_json))
                    enrolled_count += 1

        self.conn.commit()
        print(f"[CATALOGUE SEED] Registered {enrolled_count} reference individual tigers into SQLite.")
        return enrolled_count

    def identify_and_enroll(self, query_crop_path, sighting_id, image_name):
        """
        Matches a query crop against the catalogue and applies decision rules:
        - Auto-Match (High Confidence)
        - Human Review Queue (Ambiguous)
        - Auto-Enroll New Individual (Low Confidence)
        """
        catalogue = self.load_catalogue()
        cur = self.conn.cursor()

        if not catalogue:
            # First tiger ever: auto-enroll as PTR_T_01
            new_id = "PTR_T_001"
            emb = self.matcher.extract_deep_embedding(query_crop_path)
            emb_json = json.dumps(emb.tolist()) if emb is not None else None
            
            cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, reference_crop_path, stripe_features_json, status)
            VALUES (?, ?, 'U', 'both', date('now'), ?, ?, 'resident');
            """, (new_id, f"Unidentified Resident {new_id}", query_crop_path, emb_json))
            
            cur.execute("""
            UPDATE sightings SET tiger_id = ?, reid_score = 1.0, match_method = 'hotspotter_sift', review_status = 'confirmed'
            WHERE sighting_id = ?;
            """, (new_id, sighting_id))
            
            self.conn.commit()
            return {
                "decision": "auto_enrolled_new",
                "assigned_tiger_id": new_id,
                "confidence": 1.0,
                "top_candidates": []
            }

        # Extract query embedding
        query_emb = self.matcher.extract_deep_embedding(query_crop_path)
        
        candidates = []
        for ind in catalogue:
            ref_crop = ind["crop_path"]
            if not ref_crop or not os.path.exists(ref_crop):
                continue
                
            ref_emb = np.array(ind["features"]) if ind["features"] else None
            match_res = self.matcher.compare_flanks(query_crop_path, ref_crop, query_emb, ref_emb)
            
            candidates.append({
                "tiger_id": ind["tiger_id"],
                "name": ind["name"],
                "ref_crop_path": ref_crop,
                "score": match_res["combined_score"],
                "sift_score": match_res["sift_score"],
                "cosine_score": match_res["cosine_score"],
                "good_matches_count": match_res["good_matches_count"]
            })

        # Sort candidates descending by score
        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        best_match = candidates[0] if candidates else {"tiger_id": None, "score": 0.0}

        best_id = best_match.get("tiger_id")
        best_score = best_match.get("score", 0.0)

        # Decision 1: High-Confidence Auto-Match
        if best_score >= self.high_thresh:
            cur.execute("""
            UPDATE sightings SET tiger_id = ?, reid_score = ?, match_method = 'hotspotter_sift', review_status = 'confirmed'
            WHERE sighting_id = ?;
            """, (best_id, best_score, sighting_id))
            
            cur.execute("UPDATE tigers SET last_seen_date = date('now') WHERE tiger_id = ?;", (best_id,))
            self.conn.commit()
            
            return {
                "decision": "auto_matched",
                "assigned_tiger_id": best_id,
                "confidence": best_score,
                "top_candidates": candidates[:3]
            }

        # Decision 2: Ambiguous Match -> Queue for Human Review
        elif best_score >= self.low_thresh:
            # Generate visual verification image for human auditor
            viz_name = f"sighting_{sighting_id}_match_vs_{best_id}.jpg"
            viz_path = os.path.join(self.viz_dir, viz_name)
            self.matcher.generate_sift_match_visualization(query_crop_path, best_match["ref_crop_path"], viz_path)

            cur.execute("""
            UPDATE sightings SET tiger_id = ?, reid_score = ?, match_method = 'hotspotter_sift', review_status = 'pending_review'
            WHERE sighting_id = ?;
            """, (best_id, best_score, sighting_id))

            cur.execute("""
            INSERT INTO review_queue (sighting_id, suggested_tiger_id, suggested_score, top_candidates_json, flank_crop_path, sift_match_viz_path, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending');
            """, (sighting_id, best_id, best_score, json.dumps(candidates[:5]), query_crop_path, viz_path))

            self.conn.commit()
            return {
                "decision": "queued_for_review",
                "suggested_tiger_id": best_id,
                "confidence": best_score,
                "viz_path": viz_path,
                "top_candidates": candidates[:3]
            }

        # Decision 3: Low Match Score -> Auto-Enroll as New Individual
        else:
            cur.execute("SELECT COUNT(*) FROM tigers;")
            total_tigers = cur.fetchone()[0]
            new_id = f"PTR_T_{total_tigers + 1:03d}"

            emb_json = json.dumps(query_emb.tolist()) if query_emb is not None else None
            cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, reference_crop_path, stripe_features_json, status)
            VALUES (?, ?, 'U', 'both', date('now'), ?, ?, 'resident');
            """, (new_id, f"New Individual {new_id}", query_crop_path, emb_json))

            cur.execute("""
            UPDATE sightings SET tiger_id = ?, reid_score = ?, match_method = 'hotspotter_sift', review_status = 'confirmed'
            WHERE sighting_id = ?;
            """, (new_id, best_score, sighting_id))

            self.conn.commit()
            return {
                "decision": "auto_enrolled_new",
                "assigned_tiger_id": new_id,
                "confidence": best_score,
                "top_candidates": candidates[:3]
            }
