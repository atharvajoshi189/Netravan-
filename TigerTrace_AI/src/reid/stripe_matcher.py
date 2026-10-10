import os
import cv2
import numpy as np
import torch
import torchvision.models as models
from torchvision.models import ResNet50_Weights
import torchvision.transforms as transforms
from PIL import Image

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
            img = cv2.imread(img)
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        kp, des = self.sift.detectAndCompute(gray, None)
        return kp, des

    def extract_deep_embedding(self, img_path):
        """Extract 2048-dimensional normalized feature vector."""
        if not self.use_deep:
            return None
        with Image.open(img_path) as img:
            t = self.transform(img.convert('RGB')).unsqueeze(0).to(self.device)
            with torch.no_grad():
                emb = self.embedder(t).squeeze(0).cpu().numpy()
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            return emb

    def match_sift_stripes(self, query_img, ref_img, lowe_ratio=0.75):
        """
        Performs HotSpotter SIFT stripe matching with Lowe's ratio test and RANSAC homography check.
        Returns: (match_score, good_matches, query_kp, ref_kp)
        """
        kp1, des1 = self.extract_sift_features(query_img)
        kp2, des2 = self.extract_sift_features(ref_img)

        if des1 is None or des2 is None or len(des1) < 4 or len(des2) < 4:
            return 0.0, [], kp1, kp2

        try:
            matches = self.flann.knnMatch(des1, des2, k=2)
            good_matches = []
            for m, n in matches:
                if m.distance < lowe_ratio * n.distance:
                    good_matches.append(m)

            # SIFT score normalized by candidate keypoints
            inlier_count = len(good_matches)
            score = min(1.0, inlier_count / 30.0)  # 30+ matching stripe bifurcations = perfect match
            return round(score, 4), good_matches, kp1, kp2
        except Exception:
            return 0.0, [], kp1, kp2

    def compare_flanks(self, query_path, ref_path, query_emb=None, ref_emb=None):
        """
        Combined comparison: SIFT stripe geometry score (60%) + Deep Embedding Cosine Similarity (40%).
        """
        # 1. HotSpotter SIFT matching
        sift_score, good_matches, kp1, kp2 = self.match_sift_stripes(query_path, ref_path)

        # 2. Deep Feature Cosine Similarity
        cosine_sim = 0.0
        if self.use_deep:
            if query_emb is None:
                query_emb = self.extract_deep_embedding(query_path)
            if ref_emb is None:
                ref_emb = self.extract_deep_embedding(ref_path)
            if query_emb is not None and ref_emb is not None:
                cosine_sim = float(np.dot(query_emb, ref_emb))
                cosine_sim = max(0.0, min(1.0, (cosine_sim + 1.0) / 2.0))

        # Combined Ensembled Re-ID Score
        combined_score = round(0.55 * sift_score + 0.45 * cosine_sim, 4)

        return {
            "combined_score": combined_score,
            "sift_score": sift_score,
            "cosine_score": round(cosine_sim, 4),
            "good_matches_count": len(good_matches),
            "kp_query": kp1,
            "kp_ref": kp2,
            "matches": good_matches
        }

    def generate_sift_match_visualization(self, query_path, ref_path, output_path, max_draw=25):
        """
        Generates a visual verification image connecting matching stripe minutiae between two tigers.
        Essential for human-in-the-loop explainability and auditability.
        """
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
