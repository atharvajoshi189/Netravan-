import os
import cv2
import numpy as np
from PIL import Image

class FlankExtractor:
    def __init__(self, target_size=(384, 384)):
        self.target_size = target_size
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

    def extract_flank_crop(self, image_path, bbox_xyxy=None, output_dir=None, save_enhanced=True):
        """
        Extracts the animal body/flank crop, applies CLAHE contrast enhancement for stripe visibility,
        and saves the normalized crop.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        h, w = img.shape[:2]

        if bbox_xyxy:
            x1, y1, x2, y2 = [int(v) for v in bbox_xyxy]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            # If box is sufficiently large, crop it; otherwise use full image
            if (x2 - x1) > 40 and (y2 - y1) > 40:
                crop = img[y1:y2, x1:x2]
            else:
                crop = img
        else:
            crop = img

        # Enhance stripe contrast using CLAHE on Luminance channel
        if save_enhanced:
            lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l_enhanced = self.clahe.apply(l)
            lab_enhanced = cv2.merge((l_enhanced, a, b))
            enhanced_crop = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        else:
            enhanced_crop = crop

        # Resize for consistent feature matching
        resized_crop = cv2.resize(enhanced_crop, self.target_size, interpolation=cv2.INTER_AREA)

        crop_path = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            fname = os.path.splitext(os.path.basename(image_path))[0]
            crop_path = os.path.join(output_dir, f"{fname}_flank.jpg")
            cv2.imwrite(crop_path, resized_crop)

        return resized_crop, crop_path
