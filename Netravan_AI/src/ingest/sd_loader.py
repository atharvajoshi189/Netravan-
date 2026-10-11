import os
import re
import datetime
from PIL import Image
from PIL.ExifTags import TAGS

class SDCardLoader:
    def __init__(self, clock_drift_offset_seconds=0, default_station="PTR_STN_01"):
        """
        Loader for raw field camera trap SD cards.
        :param clock_drift_offset_seconds: Integer seconds to correct for camera clock drift.
        :param default_station: Fallback station ID if not found in folder/filename structure.
        """
        self.drift_offset = datetime.timedelta(seconds=clock_drift_offset_seconds)
        self.default_station = default_station

    def extract_exif_timestamp(self, img_path):
        """Extract camera timestamp from image EXIF metadata, applying drift correction."""
        try:
            with Image.open(img_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in ('DateTimeOriginal', 'DateTimeDigitized', 'DateTime'):
                            try:
                                dt = datetime.datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                                corrected_dt = dt + self.drift_offset
                                return corrected_dt.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                pass
        except Exception:
            pass

        # Fallback to filesystem modified time
        try:
            mtime = os.path.getmtime(img_path)
            dt = datetime.datetime.fromtimestamp(mtime) + self.drift_offset
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def infer_station_id(self, img_path):
        """
        Infer camera trap station ID from path hierarchy or filename.
        e.g., /SD_Card_PTR_STN_02/100EK113/IMG_001.JPG -> PTR_STN_02
        """
        path_upper = img_path.upper().replace("\\", "/")
        match = re.search(r'(PTR_STN_\d+|STN_\d+|GRID_[A-Z]\d+)', path_upper)
        if match:
            matched_str = match.group(1)
            if not matched_str.startswith("PTR_"):
                return f"PTR_{matched_str}"
            return matched_str
        return self.default_station

    def scan_sd_card_folder(self, raw_folder_path):
        """
        Recursively scans an SD card folder, returning a list of valid image records.
        """
        if not os.path.exists(raw_folder_path):
            raise FileNotFoundError(f"SD card folder not found: {raw_folder_path}")

        records = []
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')

        for root, _, files in os.walk(raw_folder_path):
            for file in sorted(files):
                if file.lower().endswith(valid_extensions):
                    full_path = os.path.join(root, file)
                    station_id = self.infer_station_id(full_path)
                    timestamp = self.extract_exif_timestamp(full_path)
                    file_size = os.path.getsize(full_path)

                    records.append({
                        "filename": file,
                        "file_path": full_path,
                        "station_id": station_id,
                        "timestamp": timestamp,
                        "file_size_bytes": file_size
                    })

        print(f"[SD INGEST] Scanned {len(records)} camera trap images from: {raw_folder_path}")
        return records
