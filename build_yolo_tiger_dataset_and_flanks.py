import os
import re
import json
import shutil
from PIL import Image
import torch
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERIFIED_DIR = os.path.join(BASE_DIR, "dataset", "verified_tiger_dataset")
YOLO_DIR = os.path.join(BASE_DIR, "dataset", "yolo_detection_dataset")
FLANKS_DIR = os.path.join(BASE_DIR, "dataset", "flank_stripe_crops")

# 7 Target Classes: 6 Identified Individuals/Groups + 1 General Group
CLASSES = [
    "T15_Collarwali",
    "T40_Patdev",
    "T-74_L-Mark",
    "Bajirao",
    "Swastik",
    "Karmajhiri_Core_Tigers",
    "Pench_General_Tigers"
]

CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASSES)}

# Clean prefix mapping for filenames
CLASS_PREFIX = {
    "T15_Collarwali": "T15_Collarwali",
    "T40_Patdev": "T40_Patdev",
    "T-74_L-Mark": "T74_LMark",
    "Bajirao": "Bajirao",
    "Swastik": "Swastik",
    "Karmajhiri_Core_Tigers": "Karmajhiri_Core",
    "Pench_General_Tigers": "Pench_General_Tiger"
}

def rename_and_standardize_images():
    """Rename all images across the 7 folders systematically."""
    print("\n========================================================")
    print(" 1. STANDARDIZING & RENAMING TIGER IMAGES ACROSS 7 TYPES")
    print("========================================================")
    
    renamed_files = {}
    
    for cat_name in CLASSES:
        cat_dir = os.path.join(VERIFIED_DIR, cat_name)
        if not os.path.exists(cat_dir):
            continue
            
        prefix = CLASS_PREFIX[cat_name]
        files = [f for f in sorted(os.listdir(cat_dir)) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        
        # Two-pass rename to avoid collision
        temp_renames = []
        for idx, fname in enumerate(files):
            old_path = os.path.join(cat_dir, fname)
            ext = fname.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                ext = 'jpg'
            temp_name = f"_temp_{prefix}_{idx+1:03d}.{ext}"
            temp_path = os.path.join(cat_dir, temp_name)
            os.rename(old_path, temp_path)
            temp_renames.append((temp_path, f"{prefix}_{idx+1:03d}.{ext}"))
            
        renamed_files[cat_name] = []
        for temp_path, final_name in temp_renames:
            final_path = os.path.join(cat_dir, final_name)
            os.rename(temp_path, final_path)
            renamed_files[cat_name].append(final_path)
            
        print(f"  [Renamed] {cat_name:25} : {len(renamed_files[cat_name])} images -> {prefix}_001 to {prefix}_{len(files):03d}")
        
    return renamed_files

def get_tiger_bounding_box(model, img_path):
    """
    Run YOLO detector to get animal/tiger bounding box.
    Returns (x_center, y_center, width, height) in normalized coordinates (0..1)
    and pixel coordinates (x1, y1, x2, y2).
    """
    with Image.open(img_path) as img:
        img_w, img_h = img.size

    results = model(img_path, verbose=False)
    boxes = results[0].boxes
    
    best_box = None
    best_conf = 0.0
    
    # Priority COCO animal classes: cat (15), dog (16), horse (17), sheep (18), cow (19), elephant (20), bear (21), zebra (22), giraffe (23)
    animal_classes = [15, 16, 17, 18, 19, 20, 21, 22, 23]
    
    if len(boxes) > 0:
        for b in boxes:
            cls_id = int(b.cls.item())
            conf = b.conf.item()
            xywhn = b.xywhn[0].tolist()
            xyxy = b.xyxy[0].tolist()
            
            # Prefer zebra, cat, bear, dog, or any dominant large bounding box
            is_animal = cls_id in animal_classes
            if is_animal and conf > best_conf:
                best_conf = conf
                best_box = (xywhn, xyxy)
            elif not best_box and conf > 0.25:
                best_box = (xywhn, xyxy)

    # Fallback if detector found no box (tight central flank crop)
    if not best_box:
        # Default full-frame / centered animal bounding box
        best_box = ([0.5, 0.5, 0.90, 0.85], [int(img_w * 0.05), int(img_h * 0.075), int(img_w * 0.95), int(img_h * 0.925)])
        
    return best_box, img_w, img_h

def generate_yolo_annotations_and_flank_crops(renamed_files):
    """Generate YOLO format .txt annotations and flank stripe crops."""
    print("\n========================================================")
    print(" 2. GENERATING YOLO BOUNDING BOXES & STRIPE CROPS        ")
    print("========================================================")
    
    model = YOLO('yolov8n.pt')
    
    # Prepare YOLO dataset directories
    yolo_images_train = os.path.join(YOLO_DIR, "images", "train")
    yolo_labels_train = os.path.join(YOLO_DIR, "labels", "train")
    os.makedirs(yolo_images_train, exist_ok=True)
    os.makedirs(yolo_labels_train, exist_ok=True)
    
    manifest_records = []
    total_crops = 0
    
    for cat_name, file_paths in renamed_files.items():
        class_id = CLASS_TO_ID[cat_name]
        flank_cat_dir = os.path.join(FLANKS_DIR, cat_name)
        os.makedirs(flank_cat_dir, exist_ok=True)
        
        print(f"\nProcessing Category [{class_id}]: {cat_name} ({len(file_paths)} images)...")
        
        for img_path in file_paths:
            fname = os.path.basename(img_path)
            base_name = os.path.splitext(fname)[0]
            
            # Compute Tiger Bounding Box
            (xywhn, xyxy), img_w, img_h = get_tiger_bounding_box(model, img_path)
            xc, yc, w, h = xywhn
            x1, y1, x2, y2 = [int(v) for v in xyxy]
            
            # Ensure coordinates within image boundaries
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img_w, x2), min(img_h, y2)
            
            # 1. Save YOLO .txt annotation in the verified folder next to the image
            txt_path_local = os.path.join(os.path.dirname(img_path), f"{base_name}.txt")
            with open(txt_path_local, "w") as f:
                f.write(f"{class_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                
            # 2. Copy to centralized YOLO detection training directory
            dest_img = os.path.join(yolo_images_train, fname)
            dest_lbl = os.path.join(yolo_labels_train, f"{base_name}.txt")
            shutil.copy2(img_path, dest_img)
            with open(dest_lbl, "w") as f:
                f.write(f"{class_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                
            # 3. Extract and save Flank / Stripe crop for Stripe Re-ID matching
            crop_path = os.path.join(flank_cat_dir, f"{base_name}_flank_crop.jpg")
            try:
                with Image.open(img_path) as img:
                    # If box is valid, crop the tiger/flank body
                    if (x2 - x1) > 20 and (y2 - y1) > 20:
                        crop_img = img.crop((x1, y1, x2, y2))
                    else:
                        crop_img = img
                    crop_img.convert("RGB").save(crop_path, "JPEG", quality=95)
                    total_crops += 1
            except Exception as e:
                print(f"Error cropping {fname}: {e}")
                
            manifest_records.append({
                "filename": fname,
                "class_id": class_id,
                "class_name": cat_name,
                "resolution": f"{img_w}x{img_h}",
                "yolo_bbox": [round(xc, 4), round(yc, 4), round(w, 4), round(h, 4)],
                "pixel_bbox": [x1, y1, x2, y2],
                "image_path": os.path.relpath(img_path, BASE_DIR).replace("\\", "/"),
                "flank_crop_path": os.path.relpath(crop_path, BASE_DIR).replace("\\", "/"),
                "yolo_label_path": os.path.relpath(txt_path_local, BASE_DIR).replace("\\", "/")
            })
            
            print(f"  [✓] {fname:25} | Box: [{xc:.3f}, {yc:.3f}, {w:.3f}, {h:.3f}] -> Crop saved")

    # Generate data.yaml for YOLO training
    yaml_content = f"""# Pench Tiger Reserve Individual Detection & Flank Localization Dataset
path: {YOLO_DIR.replace("\\", "/")}
train: images/train
val: images/train

names:
"""
    for idx, name in enumerate(CLASSES):
        yaml_content += f"  {idx}: {name}\n"
        
    yaml_path = os.path.join(YOLO_DIR, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
        
    # Generate final comprehensive JSON manifest
    manifest_data = {
        "dataset_name": "Pench_Tiger_YOLO_and_Flank_Dataset",
        "description": "Standardized YOLO-format object detection and flank stripe Re-ID dataset for 6 identified Pench tiger groups + 1 general group",
        "classes": {idx: name for idx, name in enumerate(CLASSES)},
        "total_images": len(manifest_records),
        "total_flank_crops": total_crops,
        "class_distribution": {name: len([r for r in manifest_records if r['class_name'] == name]) for name in CLASSES},
        "records": manifest_records
    }
    
    manifest_json_path = os.path.join(VERIFIED_DIR, "verified_tiger_manifest.json")
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
        
    return manifest_data

def main():
    renamed = rename_and_standardize_images()
    manifest = generate_yolo_annotations_and_flank_crops(renamed)
    
    print("\n========================================================")
    print("      FINAL DATASET ANNOTATION & FLANK CROP SUMMARY     ")
    print("========================================================")
    print(f" Total Annotated Images:     {manifest['total_images']}")
    print(f" Total Flank Stripe Crops:   {manifest['total_flank_crops']}")
    print("--------------------------------------------------------")
    print(" Class Distribution (YOLO Labels):")
    for idx, name in enumerate(CLASSES):
        count = manifest["class_distribution"][name]
        prefix = CLASS_PREFIX[name]
        print(f"  [ID {idx}] {name:25} ({prefix}_001..): {count:>2} images / labels / crops")
    print("========================================================")
    print(f" YOLO Training Config : {os.path.join(YOLO_DIR, 'data.yaml')}")
    print(f" Flank Crops Directory: {FLANKS_DIR}")
    print(f" Manifest Saved To    : {os.path.join(VERIFIED_DIR, 'verified_tiger_manifest.json')}")

if __name__ == "__main__":
    main()
