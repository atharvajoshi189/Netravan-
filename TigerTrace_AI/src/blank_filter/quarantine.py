import os
import shutil
import json
import time

class QuarantineManager:
    def __init__(self, quarantine_base_dir=None):
        if quarantine_base_dir is None:
            self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "quarantine")
        else:
            self.base_dir = quarantine_base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def stage_blank_frame(self, original_path, batch_id, reason="low_subject_confidence", confidence=0.0):
        """
        Safely moves a blank frame into staged quarantine without destroying field data.
        Returns quarantine file path and metadata record.
        """
        batch_dir = os.path.join(self.base_dir, batch_id)
        os.makedirs(batch_dir, exist_ok=True)

        filename = os.path.basename(original_path)
        quarantined_path = os.path.join(batch_dir, filename)

        # Copy to quarantine (staged delete approach)
        shutil.copy2(original_path, quarantined_path)
        file_size = os.path.getsize(original_path)

        record = {
            "filename": filename,
            "original_path": original_path,
            "quarantined_path": quarantined_path,
            "batch_id": batch_id,
            "reason": reason,
            "confidence": confidence,
            "file_size_bytes": file_size,
            "quarantined_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Update batch manifest
        manifest_path = os.path.join(batch_dir, "quarantine_manifest.json")
        manifest = []
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                manifest = []

        manifest.append(record)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return record

    def calculate_savings(self, quarantined_records, manual_sec_per_frame=3.5):
        """
        Calculates storage space saved and human inspection hours saved.
        :param manual_sec_per_frame: Average time in seconds field staff takes to review 1 camera trap frame.
        """
        total_bytes = sum(r.get("file_size_bytes", 0) for r in quarantined_records)
        total_frames = len(quarantined_records)
        time_saved_seconds = total_frames * manual_sec_per_frame
        time_saved_minutes = round(time_saved_seconds / 60.0, 2)
        time_saved_hours = round(time_saved_seconds / 3600, 2)

        return {
            "quarantined_frames": total_frames,
            "bytes_saved": total_bytes,
            "mb_saved": round(total_bytes / (1024 * 1024), 2),
            "gb_saved": round(total_bytes / (1024 * 1024 * 1024), 4),
            "time_saved_minutes": time_saved_minutes,
            "time_saved_hours": time_saved_hours
        }

    def restore_batch(self, batch_id):
        """
        Reverses quarantine for an entire batch, restoring all images to original locations.
        """
        batch_dir = os.path.join(self.base_dir, batch_id)
        manifest_path = os.path.join(batch_dir, "quarantine_manifest.json")

        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found for batch: {batch_id}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        restored_count = 0
        for r in records:
            q_path = r["quarantined_ path"]
            orig_path = r["original_path"]
            if os.path.exists(q_path):
                os.makedirs(os.path.dirname(orig_path), exist_ok=True)
                shutil.copy2(q_path, orig_path)
                restored_count += 1

        print(f"[QUARANTINE RESTORE] Restored {restored_count} images for batch: {batch_id}")
        return restored_count
