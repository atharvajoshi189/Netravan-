import os
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple, List, Union


def resolve_and_validate_bbox(
    bbox_xyxy: Optional[Union[List, Tuple]],
    img_width: int,
    img_height: int,
    min_dimension: int = 40,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Validates and resolves bounding box coordinates into absolute pixel coordinates (x1, y1, x2, y2).
    
    Distinguishes:
    1. Genuinely absent boxes (None, empty container, or all-empty fields): returns None (full-image fallback).
    2. Normalized coordinates (all values in [0.0, 1.0]): scales x by img_width and y by img_height.
    3. Pixel coordinates (any value > 1.0): validates bounds and clips to image boundaries.
    
    Rejects (raises ValueError):
    - Malformed coordinate counts (not 4 elements).
    - Non-numeric or non-finite values (NaN, Inf).
    - Negative coordinates (< 0).
    - Reversed or zero-area boxes (x2 <= x1 or y2 <= y1).
    - Out-of-bounds origins (x1 >= img_width or y1 >= img_height).
    - Degenerate crops yielding dimensions below min_dimension (40x40 pixels).
    """
    # 1. Genuinely absent bounding box (e.g., pre-cropped ATRW images)
    if bbox_xyxy is None:
        return None
    if isinstance(bbox_xyxy, (list, tuple, str)) and len(bbox_xyxy) == 0:
        return None
    if isinstance(bbox_xyxy, (list, tuple)) and all(v is None or v == "" for v in bbox_xyxy):
        return None

    # 2. Length check
    if not isinstance(bbox_xyxy, (list, tuple)) or len(bbox_xyxy) != 4:
        raise ValueError(f"Bounding box must contain exactly 4 coordinates, got: {bbox_xyxy}")

    # 3. Numeric and finiteness check
    try:
        coords = [float(v) for v in bbox_xyxy]
    except (TypeError, ValueError) as e:
        raise ValueError(f"Bounding box coordinates must be numeric, got: {bbox_xyxy}") from e

    for idx, v in enumerate(coords):
        if np.isnan(v) or np.isinf(v):
            raise ValueError(f"Bounding box coordinate at index {idx} is non-finite ({v}): {bbox_xyxy}")

    x1_raw, y1_raw, x2_raw, y2_raw = coords

    # 4. Non-negativity check
    if any(v < 0 for v in coords):
        raise ValueError(f"Bounding box coordinates must be non-negative, got: {bbox_xyxy}")

    # 5. Ordering and non-zero area check
    if x2_raw <= x1_raw:
        raise ValueError(f"Invalid horizontal ordering (x2 <= x1): x1={x1_raw}, x2={x2_raw}")
    if y2_raw <= y1_raw:
        raise ValueError(f"Invalid vertical ordering (y2 <= y1): y1={y1_raw}, y2={y2_raw}")

    # 6. Coordinate space determination
    max_val = max(coords)
    if max_val <= 1.0:
        # Normalized coordinates [0.0, 1.0]
        x1 = int(round(x1_raw * img_width))
        y1 = int(round(y1_raw * img_height))
        x2 = int(round(x2_raw * img_width))
        y2 = int(round(y2_raw * img_height))
    else:
        # Absolute pixel coordinates
        if x1_raw >= img_width or y1_raw >= img_height:
            raise ValueError(
                f"Bounding box origin ({x1_raw}, {y1_raw}) is outside image dimensions ({img_width}x{img_height})"
            )
        x1 = int(round(x1_raw))
        y1 = int(round(y1_raw))
        x2 = int(round(x2_raw))
        y2 = int(round(y2_raw))

    # 7. Boundary clipping
    x1 = max(0, min(img_width, x1))
    y1 = max(0, min(img_height, y1))
    x2 = max(0, min(img_width, x2))
    y2 = max(0, min(img_height, y2))

    # 8. Minimum dimension check
    box_w = x2 - x1
    box_h = y2 - y1
    if box_w < min_dimension or box_h < min_dimension:
        raise ValueError(
            f"Resolved crop dimensions ({box_w}x{box_h}) are below minimum viable dimension ({min_dimension}x{min_dimension})"
        )

    return x1, y1, x2, y2


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

        resolved_box = resolve_and_validate_bbox(bbox_xyxy, img_width=w, img_height=h)
        if resolved_box is not None:
            x1, y1, x2, y2 = resolved_box
            crop = img[y1:y2, x1:x2]
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
