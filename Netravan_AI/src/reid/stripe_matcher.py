import os
import cv2
import numpy as np
import torch
import torchvision.models as models
from torchvision.models import ResNet50_Weights
import torchvision.transforms as transforms
from PIL import Image

from typing import Optional, Tuple, Dict, Any, List


def normalize_flank_orientation(flank: Optional[str]) -> str:
    """
    Normalizes flank orientation strings to canonical values:
    'left', 'right', 'both', or 'unknown'.
    """
    if flank is None:
        return "unknown"
    val = str(flank).strip().lower()
    if val in ("left", "left_flank", "l"):
        return "left"
    if val in ("right", "right_flank", "r"):
        return "right"
    if val in ("both", "both_flanks", "bilateral"):
        return "both"
    return "unknown"


def is_flank_compatible(query_flank: Optional[str], ref_flank: Optional[str]) -> Tuple[bool, str]:
    """
    Evaluates biological compatibility between query flank and reference flank.
    
    Rules:
    - Both orientations must be known. An unknown orientation cannot be safely compared.
    - 'left' and 'right' are opposite flanks and strictly incompatible.
    - 'both' matches either 'left' or 'right' (or 'both').
    - 'left' matches 'left'.
    - 'right' matches 'right'.
    
    Returns:
        (is_compatible: bool, reason: str)
    """
    q = normalize_flank_orientation(query_flank)
    r = normalize_flank_orientation(ref_flank)

    if q == "unknown" and r == "unknown":
        return False, "unknown_query_and_reference_orientation"
    if q == "unknown":
        return False, "unknown_query_orientation"
    if r == "unknown":
        return False, "unknown_reference_orientation"

    if (q == "left" and r == "right") or (q == "right" and r == "left"):
        return False, "opposite_flanks_incompatible"

    if q == r or q == "both" or r == "both":
        return True, "compatible"

    return False, "flank_incompatible"


class StripeReIDMatcher:
    def __init__(self, use_deep_embedding=True):
        """
        Stripe Re-ID matcher combining:
        1. HotSpotter SIFT Keypoint Stripe Matcher (Geometric pattern minutiae).
        2. Pretrained Deep Feature Embedding (Cosine Similarity).
        """
        # SIFT Keypoint detector for stripe bifurcation minutiae
        self.sift = cv2.SIFT_create(nfeatures=1000, contrastThreshold=0.03, edgeThreshold=10)
        # FLANN Matcher for SIFT descriptors
        index_params = dict(algorithm=1, trees=5)  # FLANN_INDEX_KDTREE
        search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

        self.use_deep = use_deep_embedding
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.use_deep:
            weights = ResNet50_Weights.DEFAULT
            self.embedder = models.resnet50(weights=weights).to(self.device)
            # Remove final classification head to get 2048-dim feature embedding
            self.embedder.fc = torch.nn.Identity()
            self.embedder.eval()

            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])

    def extract_sift_features(self, img):
        """Extract SIFT keypoints and descriptors from flank image."""
        if isinstance(img, str):
            if not os.path.exists(img) or os.path.getsize(img) == 0:
                return [], None
            try:
                img = cv2.imread(img)
            except Exception:
                return [], None
        if img is None or not hasattr(img, "shape") or len(img.shape) < 2:
            return [], None
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Guard against OpenCV OutOfMemoryError on high-resolution camera trap photos (> 1600px)
        max_dim = max(gray.shape[:2])
        if max_dim > 1600:
            scale = 1600.0 / max_dim
            gray = cv2.resize(gray, (int(gray.shape[1] * scale), int(gray.shape[0] * scale)), interpolation=cv2.INTER_AREA)

        try:
            kp, des = self.sift.detectAndCompute(gray, None)
        except cv2.error:
            # Fallback for memory spikes on constrained systems
            try:
                scale = 800.0 / max(gray.shape[:2])
                gray_small = cv2.resize(gray, (int(gray.shape[1] * scale), int(gray.shape[0] * scale)), interpolation=cv2.INTER_AREA)
                kp, des = self.sift.detectAndCompute(gray_small, None)
            except Exception:
                return [], None
        return kp, des

    def extract_deep_embedding(self, img_path):
        """Extract 2048-dimensional normalized feature vector."""
        if not self.use_deep or not img_path or not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            return None
        try:
            with Image.open(img_path) as img:
                t = self.transform(img.convert('RGB')).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    emb = self.embedder(t).squeeze(0).cpu().numpy()
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                return emb
        except Exception:
            return None

    def match_sift_stripes(self, query_img, ref_img, lowe_ratio=0.75, min_ransac_points=4, ransac_reproj_thresh=5.0):
        """
        Performs robust HotSpotter SIFT stripe matching with:
        1. Lowe's distance ratio test (0.75).
        2. Mutual nearest-neighbour (reciprocal) one-to-one correspondence filtering
           (prevents duplicate query keypoints from inflating matches against a single reference keypoint).
        3. Spatial geometric verification using RANSAC homography.
        4. Rejection of insufficient evidence (< 4 verified inliers yields score 0.0).

        Returns: (match_score, inlier_matches, query_kp, ref_kp)
        """
        kp1, des1 = self.extract_sift_features(query_img)
        kp2, des2 = self.extract_sift_features(ref_img)

        if des1 is None or des2 is None or len(des1) < 4 or len(des2) < 4:
            return 0.0, [], kp1, kp2

        try:
            # 1. Forward k-NN matching (Query -> Ref)
            matches_12 = self.flann.knnMatch(des1, des2, k=2)
            # 2. Reverse k-NN matching (Ref -> Query)
            matches_21 = self.flann.knnMatch(des2, des1, k=2)

            # Filter with Lowe's ratio test
            good_12 = [m for m, n in matches_12 if m.distance < lowe_ratio * n.distance]
            good_21 = {m.queryIdx: m.trainIdx for m, n in matches_21 if m.distance < lowe_ratio * n.distance}

            # 3. Enforce mutual nearest-neighbour (reciprocal consistency) & 1-to-1 uniqueness
            mutual_matches = []
            seen_train = set()
            seen_query = set()
            for m in sorted(good_12, key=lambda x: x.distance):
                if good_21.get(m.trainIdx) == m.queryIdx:
                    if m.trainIdx not in seen_train and m.queryIdx not in seen_query:
                        mutual_matches.append(m)
                        seen_train.add(m.trainIdx)
                        seen_query.add(m.queryIdx)

            # 4. Spatial geometric verification using RANSAC homography
            inlier_matches = []
            if len(mutual_matches) >= min_ransac_points:
                src_pts = np.float32([kp1[m.queryIdx].pt for m in mutual_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in mutual_matches]).reshape(-1, 1, 2)
                H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_reproj_thresh)
                if mask is not None:
                    mask_flat = mask.ravel().tolist()
                    inlier_matches = [m for idx, m in enumerate(mutual_matches) if mask_flat[idx]]

            # 5. Insufficient evidence rejection: fewer than 4 verified inliers cannot confirm match
            inlier_count = len(inlier_matches)
            if inlier_count < min_ransac_points:
                score = 0.0
            else:
                score = min(1.0, inlier_count / 30.0)

            return round(score, 4), inlier_matches, kp1, kp2
        except Exception:
            return 0.0, [], kp1, kp2

    def compare_flanks(
        self,
        query_path,
        ref_path,
        query_emb=None,
        ref_emb=None,
        query_flank=None,
        ref_flank=None,
    ):
        """
        Combined comparison: SIFT stripe geometry score (55%) + Deep Embedding Cosine Similarity (45%).
        Enforces biological flank compatibility: opposite or unknown flanks are rejected
        before computing SIFT keypoints or deep embeddings.
        Reports raw cosine similarity alongside uncalibrated score without claiming probability calibration.
        """
        # Flank Compatibility Guard
        compatible, reason = is_flank_compatible(query_flank, ref_flank)
        if not compatible:
            return {
                "combined_score": 0.0,
                "sift_score": 0.0,
                "cosine_score": 0.0,
                "raw_cosine_similarity": 0.0,
                "cosine_is_uncalibrated": True,
                "good_matches_count": 0,
                "inlier_count": 0,
                "geometric_verification": "incompatible_flanks",
                "kp_query": [],
                "kp_ref": [],
                "matches": [],
                "flank_compatible": False,
                "flank_reason": reason,
                "reason": reason,
            }

        # 1. Robust SIFT stripe matching with MNN and RANSAC
        sift_score, good_matches, kp1, kp2 = self.match_sift_stripes(query_path, ref_path)

        # 2. Deep Feature Cosine Similarity
        raw_cosine = 0.0
        cosine_sim = 0.0
        if self.use_deep:
            if query_emb is None:
                query_emb = self.extract_deep_embedding(query_path)
            if ref_emb is None:
                ref_emb = self.extract_deep_embedding(ref_path)
            if query_emb is not None and ref_emb is not None:
                raw_cosine = float(np.dot(query_emb, ref_emb))
                # Note: (raw_cosine + 1) / 2 is an affine scaling heuristic, NOT a calibrated identity probability.
                cosine_sim = max(0.0, min(1.0, (raw_cosine + 1.0) / 2.0))

        # Combined Ensembled Re-ID Score (heuristic)
        combined_score = round(0.55 * sift_score + 0.45 * cosine_sim, 4)

        return {
            "combined_score": combined_score,
            "sift_score": sift_score,
            "cosine_score": round(cosine_sim, 4),
            "raw_cosine_similarity": round(raw_cosine, 4),
            "cosine_is_uncalibrated": True,
            "good_matches_count": len(good_matches),
            "inlier_count": len(good_matches),
            "geometric_verification": "verified" if len(good_matches) >= 4 else "insufficient_evidence",
            "kp_query": kp1,
            "kp_ref": kp2,
            "matches": good_matches,
            "flank_compatible": True,
            "flank_reason": "compatible",
            "reason": "compatible",
        }

    def generate_sift_match_visualization(
        self,
        query_path,
        ref_path,
        output_path,
        max_draw=25,
        query_flank=None,
        ref_flank=None,
    ):
        """
        Generates a visual verification image connecting matching stripe minutiae between two tigers.
        Essential for human-in-the-loop explainability and auditability.
        If flanks are provided and incompatible, visualization generation is skipped.
        """
        if query_flank is not None or ref_flank is not None:
            compatible, _ = is_flank_compatible(query_flank, ref_flank)
            if not compatible:
                return None

        img1 = cv2.imread(query_path)
        img2 = cv2.imread(ref_path)
        if img1 is None or img2 is None:
            return None

        _, good_matches, kp1, kp2 = self.match_sift_stripes(img1, img2)
        
        # Sort matches by distance
        good_matches = sorted(good_matches, key=lambda x: x.distance)[:max_draw]

        viz = cv2.drawMatches(
            img1, kp1, img2, kp2, good_matches, None,
            matchColor=(0, 255, 0),
            singlePointColor=(0, 0, 255),
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, viz)
        return output_path
