import os
import cv2
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOLO_DIR = os.path.join(BASE_DIR, "dataset", "yolo_detection_dataset")
IMAGES_DIR = os.path.join(YOLO_DIR, "images", "train")
LABELS_DIR = os.path.join(YOLO_DIR, "labels", "train")
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset", "annotated_visualizations")

CLASSES = [
    "T15_Collarwali",
    "T40_Patdev",
    "T-74_L-Mark",
    "Bajirao",
    "Swastik",
    "Karmajhiri_Core_Tigers",
    "Pench_General_Tigers"
]

# Distinct colors for each tiger class (BGR format)
COLORS = [
    (0, 165, 255),   # 0: Collarwali (Orange)
    (255, 0, 255),   # 1: Patdev (Magenta)
    (0, 255, 255),   # 2: L-Mark (Yellow)
    (0, 255, 0),     # 3: Bajirao (Green)
    (255, 200, 0),   # 4: Swastik (Cyan/Sky blue)
    (0, 128, 255),   # 5: Karmajhiri (Deep Orange)
    (200, 200, 200)  # 6: General Pench Tiger (Silver/White)
]

def render_visual_bounding_boxes():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for cat in CLASSES:
        os.makedirs(os.path.join(OUTPUT_DIR, cat), exist_ok=True)
        
    image_files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    print(f"Rendering bounding boxes on {len(image_files)} images...")
    
    for img_name in sorted(image_files):
        img_path = os.path.join(IMAGES_DIR, img_name)
        base_name = os.path.splitext(img_name)[0]
        txt_path = os.path.join(LABELS_DIR, f"{base_name}.txt")
        
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        h, w = img.shape[:2]
        
        target_cat = "Pench_General_Tigers"
        
        if os.path.exists(txt_path):
            with open(txt_path, "r") as f:
                lines = f.readlines()
                
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls_id = int(parts[0])
                    xc, yc, bw, bh = map(float, parts[1:5])
                    
                    # Convert normalized YOLO (xc, yc, w, h) to pixel (x1, y1, x2, y2)
                    x1 = int((xc - bw / 2) * w)
                    y1 = int((yc - bh / 2) * h)
                    x2 = int((xc + bw / 2) * w)
                    y2 = int((yc + bh / 2) * h)
                    
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w - 1, x2), min(h - 1, y2)
                    
                    cls_name = CLASSES[cls_id] if cls_id < len(CLASSES) else f"Class_{cls_id}"
                    color = COLORS[cls_id % len(COLORS)]
                    target_cat = cls_name
                    
                    # Draw Bounding Box rectangle
                    thickness = max(2, int(min(w, h) / 300))
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
                    
                    # Draw Label text with background box
                    label_text = f"{cls_name} [ID:{cls_id}]"
                    font_scale = max(0.6, min(w, h) / 1000)
                    (tw, th), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
                    
                    # Ensure label is inside image
                    label_y1 = max(0, y1 - th - 10)
                    label_y2 = y1 if y1 - th - 10 >= 0 else y1 + th + 10
                    
                    cv2.rectangle(img, (x1, label_y1), (x1 + tw + 10, label_y2), color, -1)
                    cv2.putText(img, label_text, (x1 + 5, label_y2 - 5 if y1 - th - 10 >= 0 else label_y2 - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 2, cv2.LINE_AA)
                                
        dest_path = os.path.join(OUTPUT_DIR, target_cat, f"{base_name}_annotated.jpg")
        cv2.imwrite(dest_path, img)
        
    print(f"\nAll visual annotated images successfully saved to:\n  {OUTPUT_DIR}")

if __name__ == "__main__":
    render_visual_bounding_boxes()
