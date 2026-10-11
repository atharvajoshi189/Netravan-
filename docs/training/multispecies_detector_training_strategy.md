# Multi-Species Wildlife Detector Training Strategy

**Document Version:** 1.0.0  
**Target:** 17-Class Central India Wildlife Detector (Tiger + 16 Prey Species)  
**Hardware Context:** Intel Integrated Graphics Laptop (CPU PyTorch) + Cloud Accelerator Path

---

## 1. Executive Summary

TigerTraceAI currently uses a single-class (`tiger`) YOLOv8 model (`TigerTrace_AI/data/models/best_yolov8.pt`) and an off-the-shelf COCO model (`yolov8n.pt`) for human/vehicle filtering. Expanding this to a genuine 17-class multi-species detector requires training a multi-class model on real wildlife imagery.

This document evaluates compute constraints, explains why training cannot run locally on the user's Intel integrated graphics, and details a reproducible cloud-accelerated training pipeline.

---

## 2. Local Hardware & Compute Audit

The system audit of the current developer workstation recorded the following specifications:

| Resource | Value | Evaluation for Model Training |
|---|---|---|
| **Operating System** | Windows 10/11 (AMD64) | Standard development workstation |
| **Python Environment**| Python 3.10.11 | Compatible with Ultralytics and PyTorch |
| **PyTorch Version** | `2.10.0+cpu` | **CPU-only build**, no CUDA libraries compiled |
| **Accelerator Support**| `CUDA Available: False` | **Zero dedicated GPU acceleration** |
| **Graphics Hardware** | Intel Integrated Graphics | Shares DDR4/DDR5 system RAM; no CUDA cores |
| **System RAM** | 15.44 GB Total, ~4.45 GB Available | Inadequate for large batch caching |
| **Disk Storage** | Drive D: 199.3 GB Free | Ample space for project code and weights |

---

## 3. Why Intel Integrated Graphics Is NOT Suitable for Training

### 3.1 Architecture Incompatibility
- Ultralytics YOLOv8 and PyTorch rely on **NVIDIA CUDA kernels** and **cuDNN acceleration** for convolutional and matrix multiplication layers.
- Intel Integrated Graphics (UHD / Iris Xe) does not support NVIDIA CUDA. While Intel offers OpenVINO and Intel Extension for PyTorch (IPEX) for *inference*, PyTorch backward-pass backpropagation during multi-epoch neural network training on integrated graphics is either completely unsupported or falls back to generic CPU execution.

### 3.2 Memory Bandwidth and Latency
- Dedicated deep-learning GPUs (e.g. RTX 3090, Tesla T4, A100) feature dedicated GDDR6 or HBM memory with bandwidth exceeding **300 to 1,500 GB/s**.
- Intel integrated graphics shares dual-channel system memory (DDR4/DDR5) with typical bandwidth of only **25 to 50 GB/s**. This creates an insurmountable memory bandwidth bottleneck during gradient aggregation.

### 3.3 Training Time and Thermal Reality
- A modest 17-class dataset of 10,000 images at $640 \times 640$ resolution:
  - **On Cloud GPU (NVIDIA T4 or RTX 3090):** ~2 to 3 minutes per epoch $\rightarrow$ **1.5 to 2.5 hours total for 50 epochs**.
  - **On Intel Laptop CPU:** ~4 to 8 hours per epoch $\rightarrow$ **200 to 400 continuous hours (8 to 16 days)** of 100% CPU saturation.
- Sustained multi-day CPU load at 100% causes thermal throttling (clocks drop to 1.2–1.8 GHz), severe fan noise, battery/hardware degradation, and frequent Windows OS freezes.

### 3.4 Inference vs. Training Distinction
- **Training (Unsuitable locally):** Forward pass + backward gradient calculation + optimizer updates on thousands of images.
- **Inference (Fully suitable locally):** Forward pass on a single camera-trap image takes **150–350 ms** on CPU using OpenVINO/ONNX. The Intel laptop is therefore fully capable of running the production web dashboard and triage filter.

---

## 4. Recommended Pretrained Model Selection

### Recommended Architecture: `YOLOv8s` (or `YOLOv8m`)
1. **Balance of Accuracy and Edge Efficiency:**
   - `YOLOv8n` (3.2M params): Fast, but struggles with fine species distinctions (e.g., distinguishing female Sambar vs. Nilgai in night IR frames).
   - `YOLOv8s` (11.2M params): Sweet spot for wildlife detection; high mAP@50-95 while maintaining sub-300ms CPU inference in field deployments.
   - `YOLOv8m` (25.9M params): Ideal if cloud GPU allows and server-side accuracy is paramount.

2. **Pretrained Backbone Weights:**
   - **Option A (Recommended):** Weights fine-tuned from **MegaDetector v5a** (trained on ~4.5 million camera-trap bounding boxes across LILA BC). This already possesses internal representations for nocturnal camera artifacts, motion blur, and foliage camouflage.
   - **Option B (Fallback):** Standard `yolov8s.pt` (MS COCO pretrained) fine-tuned on the multi-species dataset.

---

## 5. Recommended Training Environments

| Environment | Cost | GPU Specs | Pros | Cons |
|---|---|---|---|---|
| **Kaggle Kernels** | **100% Free** | 2x NVIDIA Tesla T4 (16 GB VRAM each) | 30 free GPU hours/week, no credit card required, easy data upload | 12-hour session timeout limit |
| **Google Colab (Free)**| **Free** | 1x NVIDIA Tesla T4 (15 GB) | Zero setup, direct Google Drive integration | Disconnect timeouts, unpredictable GPU assignment |
| **Google Colab Pro** | ~$10 / month | NVIDIA A100 (40 GB) or V100 | Fast training (<45 mins for 50 epochs), high RAM | Paid subscription |
| **RunPod / Lambda Labs** | ~$0.20 – $0.45 / hr | RTX 3090 / RTX 4090 (24 GB) | Dedicated root environment, persistent storage, sub-$1 cost per run | Requires cloud account and SSH setup |

**Recommendation:** Start with **Kaggle Kernels** or **Google Colab (Free T4)**. Training a 50-epoch YOLOv8s model on 5,000–10,000 images will take under 2 hours at zero cost.

---

## 6. Preservation of Existing Application Safeguards

When the trained model is eventually brought into TigerTraceAI, the following safeguards remain strictly preserved:

1. **Step 9A (Human Privacy Blurring):**
   - High-confidence human detections (`person` class) automatically trigger privacy face/torso blurring before storage or UI display.
2. **Step 9B (Bounding Box Scaling):**
   - Tiger crops sent to the Re-ID pipeline retain the 15% margin scaling so stripe features along flanks are not clipped.
3. **Step 13 & 14 (Human Review Queue & Re-ID Decision Policy):**
   - Prey detections (classes 1–16) are logged as species sightings and census counts.
   - Only `tiger` crops are routed to the Re-ID pipeline. Candidate tiger matches are routed to `review_required` in the Human Review Queue; automatic verification remains strictly disabled.
4. **Zero Production Disruption:**
   - Existing checkpoints (`best_yolov8.pt`) remain in place.
   - The new multi-species checkpoint will be validated in a separate staging evaluation script before any production swap.
