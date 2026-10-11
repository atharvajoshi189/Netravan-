import os
import torch
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

class CameraTrapTriageDetector:
    def __init__(self, model_name="yolov8n.pt", custom_model_path=None, confidence_threshold=0.25):
        """
        Dual-Stage Triage & Custom Trained Tiger Vision Engine.
        Primary Stage: Loads user's custom trained 'best_yolov8.pt' model weights for high-accuracy Tiger detection.
        Secondary Stage: COCO / MegaDetector YOLO for Person (human privacy blur), Vehicle, & Blank triage.
        """
        self.conf_threshold = confidence_threshold
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[TRIAGE DETECTOR] Initializing detector on device: {self.device} (conf={self.conf_threshold})...")
        
        pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Load user's custom trained model weights (best_yolov8.pt)
        custom_weights = custom_model_path or os.path.join(pkg_dir, "data", "models", "best_yolov8.pt")
        if not os.path.exists(custom_weights):
            custom_weights = os.path.join(pkg_dir, "data", "models", "custom_tiger_detector.pt")
        if not os.path.exists(custom_weights):
            custom_weights = r"c:\Users\Lenovo\Desktop\Pench_TIger_Images\best_yolov8.pt"

        self.tiger_model = None
        if os.path.exists(custom_weights):
            try:
                print(f"[CUSTOM TIGER MODEL] Loading user's trained YOLOv8 Tiger Detector from: {custom_weights}...")
                self.tiger_model = YOLO(custom_weights)
                print("  ✓ User's Custom Tiger Vision Engine Ready!")
            except Exception as e:
                print(f"[CUSTOM TIGER MODEL] Warning: Could not load custom model ({e}).")

        # Secondary Triage Model for Person/Vehicle/Blank
        self.triage_model = YOLO(model_name)

        self.person_classes = {0}
        self.vehicle_classes = {1, 2, 3, 5, 7}

    def detect_frame(self, image_path):
        """
        Evaluates an image frame using the custom trained Tiger model + Triage engine.
        Returns:
            dict with:
                - is_blank: bool
                - is_tiger: bool
                - category: 'tiger' | 'person' | 'vehicle' | 'animal' | 'blank'
                - max_confidence: float
                - detections: list of detections [{class_id, class_name, confidence, bbox_xyxy}]
        """
        try:
            detections = []
            is_tiger = False
            has_person = False
            has_vehicle = False
            max_conf = 0.0

            # Step 1: Run User's Custom Trained Tiger Model
            if self.tiger_model is not None:
                try:
                    t_results = self.tiger_model(image_path, imgsz=640, conf=self.conf_threshold, verbose=False)[0]
                    for b in t_results.boxes:
                        conf = float(b.conf.item())
                        xywhn = [round(x, 4) for x in b.xywhn[0].tolist()]
                        xyxy = [int(x) for x in b.xyxy[0].tolist()]
                        max_conf = max(max_conf, conf)

                        is_tiger = True
                        detections.append({
                            "class_id": 99,
                            "class_name": "tiger",
                            "confidence": conf,
                            "bbox_xywhn": xywhn,
                            "bbox_xyxy": xyxy
                        })
                except Exception as e:
                    print(f"[TIGER MODEL ERROR] {e}")

            # Step 2: Run Secondary MegaDetector for Humans/Vehicles/Blanks
            try:
                m_results = self.triage_model(image_path, imgsz=640, conf=self.conf_threshold, verbose=False)[0]
                for b in m_results.boxes:
                    cls_id = int(b.cls.item())
                    conf = float(b.conf.item())
                    cls_name = self.triage_model.names[cls_id]
                    xywhn = [round(x, 4) for x in b.xywhn[0].tolist()]
                    xyxy = [int(x) for x in b.xyxy[0].tolist()]

                    max_conf = max(max_conf, conf)

                    if cls_id in self.person_classes:
                        has_person = True
                    elif cls_id in self.vehicle_classes:
                        has_vehicle = True

                    detections.append({
                        "class_id": cls_id,
                        "class_name": cls_name,
                        "confidence": conf,
                        "bbox_xywhn": xywhn,
                        "bbox_xyxy": xyxy
                    })
            except Exception:
                pass

            # Step 3: Categorize Frame
            if is_tiger:
                category = "tiger"
                is_blank = False
            elif has_person:
                category = "person"
                is_blank = False
            elif has_vehicle:
                category = "vehicle"
                is_blank = False
            elif len(detections) > 0 and max_conf >= self.conf_threshold:
                category = "animal"
                is_blank = False
            else:
                category = "blank"
                is_blank = True

            return {
                "is_blank": is_blank,
                "is_tiger": is_tiger,
                "category": category,
                "max_confidence": round(max_conf, 4),
                "detections": detections
            }

        except Exception as e:
            print(f"[TRIAGE ERROR] Error processing {image_path}: {e}")
            return {
                "is_blank": False,
                "is_tiger": True,
                "category": "tiger",
                "max_confidence": 0.0,
                "detections": []
            }
