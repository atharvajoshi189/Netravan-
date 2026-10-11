import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REF_CAT_DIR = os.path.join(DATA_DIR, "reference_catalogue")
RAW_SD_DIR = os.path.join(DATA_DIR, "raw_sd_cards", "SD_CARD_PTR_STN_02")

# Source directories in workspace
SRC_CROPS = os.path.join(os.path.dirname(BASE_DIR), "dataset", "flank_stripe_crops")
SRC_VERIFIED = os.path.join(os.path.dirname(BASE_DIR), "dataset", "verified_tiger_dataset")
SRC_BLANKS = os.path.join(os.path.dirname(BASE_DIR), "dataset", "camera_trap_blanks", "vegetation_and_habitat")

def setup_reference_and_sample_sd_cards():
    os.makedirs(REF_CAT_DIR, exist_ok=True)
    os.makedirs(RAW_SD_DIR, exist_ok=True)

    # 1. Copy reference flank crops for the 6 identified tiger categories
    categories = ["Bajirao", "T15_Collarwali", "T40_Patdev", "T-74_L-Mark", "Swastik", "Karmajhiri_Core_Tigers"]
    
    for cat in categories:
        src_cat_dir = os.path.join(SRC_CROPS, cat)
        dest_cat_dir = os.path.join(REF_CAT_DIR, cat)
        os.makedirs(dest_cat_dir, exist_ok=True)

        if os.path.exists(src_cat_dir):
            for f in os.listdir(src_cat_dir):
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    shutil.copy2(os.path.join(src_cat_dir, f), os.path.join(dest_cat_dir, f))
            print(f"[REFERENCE SEED] Copied {len(os.listdir(dest_cat_dir))} crops for: {cat}")

    # 2. Prepare a test SD Card drop mixing:
    #   - 3 Tiger images (Bajirao, Collarwali, Patdev)
    #   - 3 Blank vegetation/habitat frames (to test Phase 1 triage quarantine)
    #   - 1 General unknown tiger image (to test Phase 2 auto-enrollment)
    
    sample_targets = [
        (os.path.join(SRC_VERIFIED, "Bajirao", "Bajirao_001.png"), "IMG_0001_PTR_STN_02.png"),
        (os.path.join(SRC_VERIFIED, "T15_Collarwali", "T15_Collarwali_001.png"), "IMG_0002_PTR_STN_02.png"),
        (os.path.join(SRC_VERIFIED, "T40_Patdev", "T40_Patdev_001.png"), "IMG_0003_PTR_STN_02.png"),
        (os.path.join(SRC_VERIFIED, "Pench_General_Tigers", "Pench_General_Tiger_001.jpg"), "IMG_0004_PTR_STN_02.jpg"),
    ]

    for src_path, dest_name in sample_targets:
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(RAW_SD_DIR, dest_name))

    # Copy blanks
    if os.path.exists(SRC_BLANKS):
        blank_files = [f for f in os.listdir(SRC_BLANKS) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        for idx, bf in enumerate(blank_files[:3]):
            src_b = os.path.join(SRC_BLANKS, bf)
            shutil.copy2(src_b, os.path.join(RAW_SD_DIR, f"BLANK_TRAIL_{idx+1:03d}_PTR_STN_02.jpg"))

    print(f"[TEST SD SEED] Created sample SD Card drop at: {RAW_SD_DIR} with {len(os.listdir(RAW_SD_DIR))} mixed field images.")

if __name__ == "__main__":
    setup_reference_and_sample_sd_cards()
