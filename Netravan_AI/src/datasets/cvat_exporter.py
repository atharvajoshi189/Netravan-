"""
TigerTraceAI — Step 15C: CVAT Project Exporter.

Converts staged wildlife pilot imagery and provisional proposals into
CVAT for Images 1.1 XML format for standard computer vision annotation workflows.
"""

from __future__ import annotations

import json
import logging
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.dom import minidom

import cv2

logger = logging.getLogger("cvat_exporter")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


class CVATProjectExporter:
    """Exports staged images and candidate proposals to CVAT XML format."""

    CANONICAL_LABELS = [
        {"name": "chital", "color": "#00FF00"},
        {"name": "sambar", "color": "#FF8800"},
        {"name": "gaur", "color": "#0000FF"},
        {"name": "nilgai", "color": "#8800FF"},
        {"name": "unknown_uncertain", "color": "#888888"},
    ]

    def __init__(self, staging_dir: Path, output_dir: Optional[Path] = None):
        self.staging_dir = Path(staging_dir)
        self.images_dir = self.staging_dir / "images"
        self.manifest_path = self.staging_dir / "manifests" / "staging_manifest.json"
        self.proposals_path = self.staging_dir / "provisional_proposals" / "provisional_proposals.json"
        self.output_dir = Path(output_dir) if output_dir else self.staging_dir / "cvat_project"

    def export(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load manifest
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        samples = manifest_data.get("samples", [])

        # 2. Load proposals if available
        proposals_by_sample: Dict[str, List[Dict[str, Any]]] = {}
        if self.proposals_path.exists():
            with open(self.proposals_path, "r", encoding="utf-8") as f:
                prop_data = json.load(f)
            for prop in prop_data.get("proposals", []):
                s_id = prop["sample_id"]
                proposals_by_sample.setdefault(s_id, []).append(prop)

        # 3. Build XML tree
        annotations_elem = ET.Element("annotations")

        # Version
        version_elem = ET.SubElement(annotations_elem, "version")
        version_elem.text = "1.1"

        # Meta
        meta_elem = ET.SubElement(annotations_elem, "meta")
        task_elem = ET.SubElement(meta_elem, "task")
        ET.SubElement(task_elem, "id").text = "1"
        ET.SubElement(task_elem, "name").text = "TigerTraceAI_Prey_Pilot_Step15C"
        ET.SubElement(task_elem, "size").text = str(len(samples))
        ET.SubElement(task_elem, "mode").text = "annotation"
        ET.SubElement(task_elem, "overlap").text = "0"
        ET.SubElement(task_elem, "bugtracker")

        # Labels
        labels_elem = ET.SubElement(task_elem, "labels")
        for lbl in self.CANONICAL_LABELS:
            l_elem = ET.SubElement(labels_elem, "label")
            ET.SubElement(l_elem, "name").text = lbl["name"]
            ET.SubElement(l_elem, "color").text = lbl["color"]
            attributes_elem = ET.SubElement(l_elem, "attributes")

            # Occlusion attribute
            attr1 = ET.SubElement(attributes_elem, "attribute")
            ET.SubElement(attr1, "name").text = "occlusion"
            ET.SubElement(attr1, "mutable").text = "True"
            ET.SubElement(attr1, "input_type").text = "select"
            ET.SubElement(attr1, "default_value").text = "none"
            ET.SubElement(attr1, "values").text = "none\nlow\nmedium\nhigh"

            # Review status attribute
            attr2 = ET.SubElement(attributes_elem, "attribute")
            ET.SubElement(attr2, "name").text = "verified_status"
            ET.SubElement(attr2, "mutable").text = "True"
            ET.SubElement(attr2, "input_type").text = "select"
            ET.SubElement(attr2, "default_value").text = "unreviewed_proposal"
            ET.SubElement(attr2, "values").text = "unreviewed_proposal\nhuman_accepted\nhuman_modified\nmanual_drawn"

        # 4. Images & provisional boxes
        for idx, sample in enumerate(samples):
            s_id = sample["sample_id"]
            img_filename = f"{s_id}.jpg"
            img_path = self.images_dir / img_filename

            width = sample.get("width_px", 800)
            height = sample.get("height_px", 600)
            if img_path.exists():
                im = cv2.imread(str(img_path))
                if im is not None:
                    height, width = im.shape[:2]

            img_elem = ET.SubElement(annotations_elem, "image")
            img_elem.set("id", str(idx + 1))
            img_elem.set("name", img_filename)
            img_elem.set("width", str(width))
            img_elem.set("height", str(height))

            # Add provisional proposals
            props = proposals_by_sample.get(s_id, [])
            for p in props:
                x1, y1, x2, y2 = p["bbox_pixel_xyxy"]
                # Default label set to the occurrence species label as suggestion, but marked unreviewed
                species_sugg = sample["canonical_class_name"]

                box_elem = ET.SubElement(img_elem, "box")
                box_elem.set("label", species_sugg)
                box_elem.set("occluded", "0")
                box_elem.set("source", p["proposal_source"])
                box_elem.set("xtl", str(x1))
                box_elem.set("ytl", str(y1))
                box_elem.set("xbr", str(x2))
                box_elem.set("ybr", str(y2))
                box_elem.set("z_order", "0")

                attr_tag = ET.SubElement(box_elem, "attribute")
                attr_tag.set("name", "verified_status")
                attr_tag.text = "unreviewed_proposal"

        # 5. Format and write XML
        xml_str = ET.tostring(annotations_elem, encoding="utf-8")
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ", encoding="utf-8")

        xml_path = self.output_dir / "annotations.xml"
        with open(xml_path, "wb") as f:
            f.write(pretty_xml)

        # 6. Write CVAT task setup guide
        manifest_guide = self.output_dir / "cvat_task_manifest.json"
        with open(manifest_guide, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "project_name": "TigerTraceAI_Step15C_Prey_Pilot",
                    "annotation_format": "CVAT for Images 1.1",
                    "xml_file": "annotations.xml",
                    "images_directory": str(self.images_dir.resolve()),
                    "total_images": len(samples),
                    "supported_labels": [lbl["name"] for lbl in self.CANONICAL_LABELS],
                    "instructions": [
                        "1. Open CVAT (cvat.ai or local instance).",
                        "2. Create a new task named 'TigerTraceAI_Prey_Pilot_Step15C'.",
                        "3. Attach images from the staging directory.",
                        "4. Upload 'annotations.xml' as pre-annotated CVAT 1.1 file.",
                        "5. Review, adjust boxes, and classify as Chital, Sambar, Gaur, Nilgai, or Unknown.",
                        "6. Export completed annotations as CVAT for Images 1.1 or YOLO 1.1.",
                    ],
                },
                f,
                indent=2,
            )

        logger.info(f"CVAT annotation project generated at {self.output_dir}")
        return xml_path


def main():
    exporter = CVATProjectExporter(staging_dir=Path("TigerTrace_AI/data/staging_wildlife_pilot"))
    xml_out = exporter.export()
    print(f"CVAT XML exported successfully to: {xml_out}")


if __name__ == "__main__":
    main()
