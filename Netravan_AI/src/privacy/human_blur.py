import os
import cv2
import numpy as np

class HumanPrivacyBlurrer:
    def __init__(self, blur_kernel_size=(51, 51)):
        self.kernel_size = blur_kernel_size

    def apply_privacy_blur(self, image_path, human_bboxes_xyxy, output_path=None):
        """
        Applies strong Gaussian blur to any human bounding box detected in the frame.
        :param image_path: Path to raw camera trap image.
        :param human_bboxes_xyxy: List of [x1, y1, x2, y2] bounding boxes for humans.
        :param output_path: Where to save blurred image (if None, overwrites or creates privacy_blurred copy).
        """
        img = cv2.imread(image_path)
        if img is None:
            return image_path, False

        h, w = img.shape[:2]
        blurred = False

        for bbox in human_bboxes_xyxy:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 > x1 and y2 > y1:
                # Extract ROI
                roi = img[y1:y2, x1:x2]
                # Apply Gaussian Blur
                blurred_roi = cv2.GaussianBlur(roi, self.kernel_size, 30)
                img[y1:y2, x1:x2] = blurred_roi
                blurred = True

        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_blurred{ext}"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, img)
        return output_path, blurred
