import os
import json
import sqlite3
import logging
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import cv2

from .stripe_matcher import StripeReIDMatcher

try:
    from ..config import (
        REID_HIGH_CONFIDENCE_THRESHOLD,
        REID_LOW_CONFIDENCE_THRESHOLD,
        REID_DUPLICATE_CHECK_THRESHOLD,
        REID_MODEL_VERSION,
    )
except ImportError:
    REID_HIGH_CONFIDENCE_THRESHOLD = 0.50
    REID_LOW_CONFIDENCE_THRESHOLD = 0.35
    REID_DUPLICATE_CHECK_THRESHOLD = 0.30
    REID_MODEL_VERSION = "hotspotter_sift_v1+resnet50_v1"

logger = logging.getLogger("TigerTrace.ReID.Enrollment")


class TigerEnrollmentEngine:
    """
    Animal Identity Enrollment and Stripe Re-ID Decision Engine.
    
    Provides safe, explainable, human-auditable individual identification:
    - Rejects false certainty on empty catalogues.
    - Prevents unsafe automatic enrollment of low-confidence observations.
    - Emits explicit identity decision states:
        * 'matched': High-confidence match to an existing enrolled individual.
        * 'review_required': Ambiguous match queued for human verification.
        * 'unknown': Observation cannot be matched or image features are unreadable.
        * 'new_identity_candidate': Potential new individual requiring explicit approval.
    - Enforces duplicate detection before approving new individual enrollment.
    - Configurable similarity thresholds.
    - Species-aware candidate filtering (supports multi-species expansion).
    """

    def __init__(
        self,
        db_connection: Optional[sqlite3.Connection] = None,
        high_confidence_threshold: Optional[float] = None,
        low_confidence_threshold: Optional[float] = None,
        duplicate_threshold: Optional[float] = None,
        viz_dir: Optional[str] = None,
        matcher: Optional[StripeReIDMatcher] = None,
        model_version: Optional[str] = None,
    ):
        self.conn = db_connection
        self.high_thresh = float(
            high_confidence_threshold
            if high_confidence_threshold is not None
            else REID_HIGH_CONFIDENCE_THRESHOLD
        )
        self.low_thresh = float(
            low_confidence_threshold
            if low_confidence_threshold is not None
            else REID_LOW_CONFIDENCE_THRESHOLD
        )
        self.duplicate_thresh = float(
            duplicate_threshold
            if duplicate_threshold is not None
            else REID_DUPLICATE_CHECK_THRESHOLD
        )
        self.model_version = str(model_version or REID_MODEL_VERSION)
        self.matcher = matcher if matcher is not None else StripeReIDMatcher(use_deep_embedding=True)

        if viz_dir is None:
            self.viz_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "data",
                "review_visualizations",
            )
        else:
            self.viz_dir = viz_dir
        os.makedirs(self.viz_dir, exist_ok=True)

    def _get_tigers_columns(self) -> List[str]:
        """Inspects columns of the tigers table for schema resilience."""
        if self.conn is None:
            return []
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(tigers);")
        return [row[1] for row in cur.fetchall()]

    def load_catalogue(self, species: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Loads all enrolled reference animals and their reference flank features from the database.
        Filters by species if species metadata is present in the catalogue.
        """
        if self.conn is None:
            return []

        cur = self.conn.cursor()
        cols = self._get_tigers_columns()
        has_species_col = "species" in cols

        if has_species_col:
            cur.execute(
                "SELECT tiger_id, name, gender, reference_crop_path, stripe_features_json, species FROM tigers;"
            )
        else:
            cur.execute(
                "SELECT tiger_id, name, gender, reference_crop_path, stripe_features_json FROM tigers;"
            )

        rows = cur.fetchall()
        catalogue = []
        for r in rows:
            entry_species = r["species"] if has_species_col else None
            # If species metadata is provided on both query and catalogue entry, ensure compatibility
            if species is not None and entry_species is not None:
                if entry_species.strip().lower() != species.strip().lower():
                    continue

            catalogue.append({
                "tiger_id": r["tiger_id"],
                "name": r["name"],
                "gender": r["gender"],
                "crop_path": r["reference_crop_path"],
                "species": entry_species,
                "features": json.loads(r["stripe_features_json"]) if r["stripe_features_json"] else None,
            })
        return catalogue

    def seed_initial_catalogue_from_folder(self, catalogue_folder: str, species: str = "tiger") -> int:
        """
        Seeds known resident animals into SQLite from reference catalogue images
        (e.g., Bajirao, Collarwali, Patdev, L-Mark, Swastik, Karmajhiri).
        """
        if not os.path.exists(catalogue_folder) or self.conn is None:
            return 0

        cur = self.conn.cursor()
        cols = self._get_tigers_columns()
        has_species_col = "species" in cols
        enrolled_count = 0

        for tiger_name in os.listdir(catalogue_folder):
            tiger_dir = os.path.join(catalogue_folder, tiger_name)
            if os.path.isdir(tiger_dir):
                crops = [f for f in sorted(os.listdir(tiger_dir)) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
                if crops:
                    ref_crop = os.path.join(tiger_dir, crops[0])
                    tiger_id = tiger_name.upper().replace("-", "_").replace(" ", "_")

                    # Extract reference deep embedding
                    emb = self.matcher.extract_deep_embedding(ref_crop)
                    emb_json = json.dumps(emb.tolist()) if emb is not None else None

                    gender = "F" if "collarwali" in tiger_name.lower() or "patdev" in tiger_name.lower() else "M"

                    if has_species_col:
                        cur.execute("""
                        INSERT OR REPLACE INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, reference_crop_path, stripe_features_json, status, species)
                        VALUES (?, ?, ?, 'both', '2021-01-01', ?, ?, 'resident', ?);
                        """, (tiger_id, tiger_name, gender, ref_crop, emb_json, species))
                    else:
                        cur.execute("""
                        INSERT OR REPLACE INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, reference_crop_path, stripe_features_json, status)
                        VALUES (?, ?, ?, 'both', '2021-01-01', ?, ?, 'resident');
                        """, (tiger_id, tiger_name, gender, ref_crop, emb_json))
                    enrolled_count += 1

        self.conn.commit()
        logger.info("Catalogue seed registered %d reference individuals into SQLite.", enrolled_count)
        print(f"[CATALOGUE SEED] Registered {enrolled_count} reference individual tigers into SQLite.")
        return enrolled_count

    def _generate_next_candidate_id(self, prefix: str = "PTR_T_") -> str:
        """Generates a non-colliding candidate identifier for new individual proposals."""
        if self.conn is None:
            return f"{prefix}001"

        cur = self.conn.cursor()
        # Find maximum numeric index across both enrolled tigers and review queue suggestions
        cur.execute("SELECT tiger_id FROM tigers WHERE tiger_id LIKE ?;", (f"{prefix}%",))
        existing_enrolled = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT suggested_tiger_id FROM review_queue WHERE suggested_tiger_id LIKE ?;", (f"{prefix}%",))
        existing_suggested = [row[0] for row in cur.fetchall() if row[0]]

        all_ids = set(existing_enrolled + existing_suggested)
        max_idx = 0
        for tid in all_ids:
            try:
                num_part = tid.replace(prefix, "")
                if num_part.isdigit():
                    max_idx = max(max_idx, int(num_part))
            except Exception:
                pass

        return f"{prefix}{max_idx + 1:03d}"

    def check_potential_duplicate(
        self,
        query_crop_path: str,
        query_emb: Optional[np.ndarray] = None,
        species: Optional[str] = None,
        exclude_tiger_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Compares an image against all currently enrolled individuals to detect potential duplicates.
        Returns: (is_duplicate_flagged, top_match_record)
        """
        catalogue = self.load_catalogue(species=species)
        if not catalogue:
            return False, None

        if query_emb is None and os.path.exists(query_crop_path):
            query_emb = self.matcher.extract_deep_embedding(query_crop_path)

        candidates = []
        for ind in catalogue:
            if exclude_tiger_id and ind["tiger_id"] == exclude_tiger_id:
                continue
            ref_crop = ind["crop_path"]
            if not ref_crop or not os.path.exists(ref_crop):
                continue
            ref_emb = np.array(ind["features"]) if ind["features"] else None
            match_res = self.matcher.compare_flanks(query_crop_path, ref_crop, query_emb, ref_emb)
            score = match_res.get("combined_score", 0.0)
            candidates.append({
                "tiger_id": ind["tiger_id"],
                "name": ind["name"],
                "ref_crop_path": ref_crop,
                "score": score,
            })

        if not candidates:
            return False, None

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        top_match = candidates[0]
        if top_match["score"] >= self.duplicate_thresh:
            return True, top_match

        return False, top_match

    def approve_new_identity(
        self,
        sighting_id: int,
        candidate_id: Optional[str] = None,
        name: Optional[str] = None,
        gender: str = "U",
        species: Optional[str] = None,
        force: bool = False,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Explicit approval flow for permanently enrolling a new individual into the catalogue.
        
        Guards:
        1. Checks for possible duplicate identities against all enrolled individuals.
        2. Halts approval if duplicate detected unless force=True.
        3. Inserts into tigers only upon explicit approval.
        4. Updates sighting review_status to 'confirmed'.
        5. Updates review_queue status to 'enrolled_new'.
        """
        if self.conn is None:
            raise RuntimeError("Database connection required to approve enrollment.")

        cur = self.conn.cursor()
        cur.execute("SELECT sighting_id, flank_crop_path, species FROM sightings WHERE sighting_id = ?;", (sighting_id,))
        sighting_row = cur.fetchone()
        if not sighting_row:
            raise ValueError(f"Sighting ID {sighting_id} not found in database.")

        crop_path = sighting_row["flank_crop_path"]
        effective_species = species or sighting_row["species"] or "tiger"

        if not crop_path or not os.path.exists(crop_path):
            raise FileNotFoundError(f"Crop image not found at: {crop_path}")

        # Check for possible duplicates before approval
        is_dup, top_dup = self.check_potential_duplicate(crop_path, species=effective_species)
        if is_dup and not force:
            logger.warning(
                "Enrollment approval halted: potential duplicate of %s (score=%.4f >= duplicate_threshold=%.4f).",
                top_dup["tiger_id"],
                top_dup["score"],
                self.duplicate_thresh,
            )
            return {
                "status": "possible_duplicate_flagged",
                "duplicate_flagged": True,
                "top_match_id": top_dup["tiger_id"],
                "top_match_score": top_dup["score"],
                "message": (
                    f"Candidate matches existing identity '{top_dup['tiger_id']}' with score {top_dup['score']:.4f} "
                    f">= threshold {self.duplicate_thresh:.4f}. Human verification required or set force=True to override."
                ),
            }

        # Resolve unique ID
        resolved_id = candidate_id.strip().upper() if candidate_id else self._generate_next_candidate_id()
        resolved_name = name or f"Resident {resolved_id}"

        # Extract and persist embedding
        emb = self.matcher.extract_deep_embedding(crop_path)
        emb_json = json.dumps(emb.tolist()) if emb is not None else None

        cols = self._get_tigers_columns()
        has_species_col = "species" in cols

        if has_species_col:
            cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, last_seen_date, reference_crop_path, stripe_features_json, status, notes, species)
            VALUES (?, ?, ?, 'both', date('now'), date('now'), ?, ?, 'resident', ?, ?);
            """, (resolved_id, resolved_name, gender, crop_path, emb_json, notes, effective_species))
        else:
            cur.execute("""
            INSERT INTO tigers (tiger_id, name, gender, flank_side_registered, first_seen_date, last_seen_date, reference_crop_path, stripe_features_json, status, notes)
            VALUES (?, ?, ?, 'both', date('now'), date('now'), ?, ?, 'resident', ?);
            """, (resolved_id, resolved_name, gender, crop_path, emb_json, notes))

        # Update sighting
        cur.execute("""
        UPDATE sightings
        SET tiger_id = ?, review_status = 'confirmed', match_method = 'manual'
        WHERE sighting_id = ?;
        """, (resolved_id, sighting_id))

        # Update review queue
        cur.execute("""
        UPDATE review_queue
        SET status = 'enrolled_new', reviewer_notes = ?, reviewed_at = CURRENT_TIMESTAMP
        WHERE sighting_id = ?;
        """, (f"Approved enrollment as {resolved_id}", sighting_id))

        self.conn.commit()
        logger.info(
            "Approved new identity: tiger_id=%s, sighting_id=%d, species=%s, force=%s",
            resolved_id,
            sighting_id,
            effective_species,
            force,
        )

        return {
            "status": "enrolled",
            "duplicate_flagged": False,
            "tiger_id": resolved_id,
            "name": resolved_name,
            "sighting_id": sighting_id,
            "species": effective_species,
        }

    def identify_and_enroll(
        self,
        query_crop_path: str,
        sighting_id: int,
        image_name: str,
        species: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Audited identity matching and triage logic:
        1. Validates query image features.
        2. Safely handles empty catalogues (no false certainty, returns pending candidate).
        3. Filters reference animals by species if metadata is available.
        4. Applies explicit, configurable decision states:
            - 'matched': score >= high_thresh
            - 'review_required': low_thresh <= score < high_thresh
            - 'new_identity_candidate': score < low_thresh (never auto-enrolled without approval)
        5. Emits structured decision logging.
        """
        cur = self.conn.cursor() if self.conn else None

        # Look up species from sighting record if not explicitly provided
        effective_species = species
        if effective_species is None and cur is not None and sighting_id is not None:
            try:
                cur.execute("SELECT species FROM sightings WHERE sighting_id = ?;", (sighting_id,))
                row = cur.fetchone()
                if row and row["species"]:
                    effective_species = row["species"]
            except Exception:
                pass

        # Validate query crop path and extract features
        if not query_crop_path or not os.path.exists(query_crop_path):
            reason = "invalid_or_missing_image_features"
            logger.warning("Re-ID Failed: %s for sighting %s (path: %s)", reason, sighting_id, query_crop_path)

            if cur:
                cur.execute("""
                UPDATE sightings SET reid_score = 0.0, match_method = 'unmatched', review_status = 'pending_review'
                WHERE sighting_id = ?;
                """, (sighting_id,))
                self.conn.commit()

            return {
                "decision_state": "unknown",
                "decision": "unknown",
                "assigned_tiger_id": None,
                "suggested_tiger_id": "UNMATCHED",
                "confidence": 0.0,
                "best_score": 0.0,
                "second_best_score": None,
                "top_candidates": [],
                "reason": reason,
                "species": effective_species,
                "model_version": self.model_version,
            }

        # Check if image is decodable
        test_img = cv2.imread(query_crop_path)
        if test_img is None or test_img.size == 0:
            reason = "corrupt_or_unreadable_image"
            logger.warning("Re-ID Failed: %s for sighting %s", reason, sighting_id)

            if cur:
                cur.execute("""
                UPDATE sightings SET reid_score = 0.0, match_method = 'unmatched', review_status = 'pending_review'
                WHERE sighting_id = ?;
                """, (sighting_id,))
                self.conn.commit()

            return {
                "decision_state": "unknown",
                "decision": "unknown",
                "assigned_tiger_id": None,
                "suggested_tiger_id": "UNMATCHED",
                "confidence": 0.0,
                "best_score": 0.0,
                "second_best_score": None,
                "top_candidates": [],
                "reason": reason,
                "species": effective_species,
                "model_version": self.model_version,
            }

        # Load catalogue filtered by species
        catalogue = self.load_catalogue(species=effective_species)

        # ---------------------------------------------------------------------
        # Condition A: Empty Catalogue Handling
        # ---------------------------------------------------------------------
        if not catalogue:
            candidate_id = self._generate_next_candidate_id()
            reason = "empty_catalogue_pending_enrollment_approval"

            logger.info(
                "Re-ID Decision: state=new_identity_candidate, predicted_id=%s, best_score=0.0, second_best_score=None, reason=%s, model_version=%s, sighting_id=%s",
                candidate_id,
                reason,
                self.model_version,
                sighting_id,
            )

            if cur:
                # Do NOT auto-enroll into tigers. Stage observation in review queue with pending status.
                cur.execute("""
                UPDATE sightings
                SET tiger_id = NULL, reid_score = 0.0, match_method = 'unmatched', review_status = 'pending_review'
                WHERE sighting_id = ?;
                """, (sighting_id,))

                cur.execute("""
                INSERT INTO review_queue (sighting_id, suggested_tiger_id, suggested_score, top_candidates_json, flank_crop_path, sift_match_viz_path, status)
                VALUES (?, ?, 0.0, '[]', ?, NULL, 'pending');
                """, (sighting_id, candidate_id, query_crop_path))

                self.conn.commit()

            return {
                "decision_state": "new_identity_candidate",
                "decision": "new_identity_candidate",
                "assigned_tiger_id": None,
                "suggested_tiger_id": candidate_id,
                "candidate_id": candidate_id,
                "confidence": 0.0,
                "best_score": 0.0,
                "second_best_score": None,
                "top_candidates": [],
                "reason": reason,
                "requires_approval": True,
                "species": effective_species,
                "model_version": self.model_version,
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
                "score": match_res.get("combined_score", 0.0),
                "sift_score": match_res.get("sift_score", 0.0),
                "cosine_score": match_res.get("cosine_score", 0.0),
                "good_matches_count": match_res.get("good_matches_count", 0),
            })

        # Sort candidates descending by score
        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        best_match = candidates[0] if candidates else {"tiger_id": None, "score": 0.0}

        best_id = best_match.get("tiger_id")
        best_score = float(best_match.get("score", 0.0))
        second_best_score = float(candidates[1]["score"]) if len(candidates) > 1 else None

        # ---------------------------------------------------------------------
        # Condition B1: High-Confidence Valid Match
        # ---------------------------------------------------------------------
        if best_score >= self.high_thresh:
            decision_state = "matched"
            reason = "strong_biometric_match_above_high_threshold"

            logger.info(
                "Re-ID Decision: state=%s, predicted_id=%s, best_score=%.4f, second_best_score=%s, reason=%s, model_version=%s, sighting_id=%s",
                decision_state,
                best_id,
                best_score,
                f"{second_best_score:.4f}" if second_best_score is not None else "None",
                reason,
                self.model_version,
                sighting_id,
            )

            if cur:
                cur.execute("""
                UPDATE sightings SET tiger_id = ?, reid_score = ?, match_method = 'hotspotter_sift', review_status = 'confirmed'
                WHERE sighting_id = ?;
                """, (best_id, best_score, sighting_id))

                cur.execute("UPDATE tigers SET last_seen_date = date('now') WHERE tiger_id = ?;", (best_id,))
                self.conn.commit()

            return {
                "decision_state": decision_state,
                "decision": decision_state,
                "assigned_tiger_id": best_id,
                "suggested_tiger_id": best_id,
                "confidence": best_score,
                "best_score": best_score,
                "second_best_score": second_best_score,
                "top_candidates": candidates[:3],
                "reason": reason,
                "requires_approval": False,
                "species": effective_species,
                "model_version": self.model_version,
            }

        # ---------------------------------------------------------------------
        # Condition B2: Ambiguous Match -> Queue for Human Review
        # ---------------------------------------------------------------------
        elif best_score >= self.low_thresh:
            decision_state = "review_required"
            reason = "ambiguous_match_below_auto_confirm_threshold"

            viz_name = f"sighting_{sighting_id}_match_vs_{best_id}.jpg"
            viz_path = os.path.join(self.viz_dir, viz_name)
            if best_match.get("ref_crop_path"):
                self.matcher.generate_sift_match_visualization(
                    query_crop_path, best_match["ref_crop_path"], viz_path
                )
            else:
                viz_path = None

            logger.info(
                "Re-ID Decision: state=%s, predicted_id=%s, best_score=%.4f, second_best_score=%s, reason=%s, model_version=%s, sighting_id=%s",
                decision_state,
                best_id,
                best_score,
                f"{second_best_score:.4f}" if second_best_score is not None else "None",
                reason,
                self.model_version,
                sighting_id,
            )

            if cur:
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
                "decision_state": decision_state,
                "decision": decision_state,
                "assigned_tiger_id": None,
                "suggested_tiger_id": best_id,
                "confidence": best_score,
                "best_score": best_score,
                "second_best_score": second_best_score,
                "viz_path": viz_path,
                "top_candidates": candidates[:3],
                "reason": reason,
                "requires_approval": True,
                "species": effective_species,
                "model_version": self.model_version,
            }

        # ---------------------------------------------------------------------
        # Condition B3: Low Similarity Observation -> Candidate Only (No Auto-Enroll)
        # ---------------------------------------------------------------------
        else:
            decision_state = "new_identity_candidate"
            candidate_id = self._generate_next_candidate_id()
            reason = "low_similarity_below_reid_threshold_requires_approval"

            viz_name = f"sighting_{sighting_id}_candidate_vs_{best_id or 'none'}.jpg"
            viz_path = os.path.join(self.viz_dir, viz_name)
            if best_match.get("ref_crop_path"):
                self.matcher.generate_sift_match_visualization(
                    query_crop_path, best_match["ref_crop_path"], viz_path
                )
            else:
                viz_path = None

            logger.info(
                "Re-ID Decision: state=%s, predicted_id=%s, best_score=%.4f, second_best_score=%s, reason=%s, model_version=%s, sighting_id=%s",
                decision_state,
                candidate_id,
                best_score,
                f"{second_best_score:.4f}" if second_best_score is not None else "None",
                reason,
                self.model_version,
                sighting_id,
            )

            if cur:
                # Preserve candidate metadata and image reference in review queue without permanent DB enrollment
                cur.execute("""
                UPDATE sightings SET tiger_id = NULL, reid_score = ?, match_method = 'unmatched', review_status = 'pending_review'
                WHERE sighting_id = ?;
                """, (best_score, sighting_id))

                cur.execute("""
                INSERT INTO review_queue (sighting_id, suggested_tiger_id, suggested_score, top_candidates_json, flank_crop_path, sift_match_viz_path, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending');
                """, (sighting_id, candidate_id, best_score, json.dumps(candidates[:5]), query_crop_path, viz_path))

                self.conn.commit()

            return {
                "decision_state": decision_state,
                "decision": decision_state,
                "assigned_tiger_id": None,
                "suggested_tiger_id": candidate_id,
                "candidate_id": candidate_id,
                "confidence": best_score,
                "best_score": best_score,
                "second_best_score": second_best_score,
                "viz_path": viz_path,
                "top_candidates": candidates[:3],
                "reason": reason,
                "requires_approval": True,
                "species": effective_species,
                "model_version": self.model_version,
            }
