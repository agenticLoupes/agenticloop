# Dental AI Mobile App Architecture Guide

## Overview

This document outlines the technical design, computer vision (CV) strategy, and agentic workflows for building a smartphone application capable of real-time intraoral video analysis, tooth tracking, patient health record integration, and voice/video assistance.

---

## 1. Computer Vision & Agentic Pipeline Architecture

Building a real-time intraoral analysis tool on a smartphone requires balancing local processing power with cloud-based reasoning engines.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SMARTPHONE (LOCAL)                             │
│                                                                             │
│  Camera Stream ──► Local YOLO (System 1) ──► Quality Filter / Gatekeeper     │
│   (30 FPS)          • Draws UI boxes          • Drops blurry frames         │
│                     • Tracks tooth IDs        • Triggers 1 high-res photo   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                         High-Res Snapshot + Boxes
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLOUD BACKEND (API)                              │
│                                                                             │
│  1. SAM 2 / Google VLM (Gemini 2.0 / PaliGemma 2)                           │
│     Generates fine-grained tooth masks or validates 2D spatial coordinates   │
│                                                                             │
│  2. Gemini Multimodal Live / ChatGPT Realtime API                           │
│     Reads snapshot + patient dental graph history                           │
│     Synthesizes findings & streams real-time audio back to phone            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technical Stack & Architecture Options

### System 1: Local On-Device CV (The "Eyes / Gatekeeper")

* **Model:** YOLOv8 / YOLOv11 Nano (or MobileSAM).
* **Execution:** CoreML (iOS Neural Engine) or TFLite / ONNX Runtime (Android NPU).
* **Performance:** Takes **<10 MB RAM**, runs locally at **30–60+ FPS** at **<15ms latency**.
* **Role:**
  * Detects teeth using FDI (11–48) or Universal (1–32) numbering systems.
  * Tracks camera motion locally using trackers like ByteTRACK.
  * Runs Laplacian variance blur checks and exposure checks to drop unusable frames.
  * Captures a single pristine high-resolution snapshot when camera focus stabilizes.

### System 2: Cloud Engine & Orchestrator (The "Brain / Voice")

* **Models:** SAM 2 (Segment Anything Model 2) + Gemini Multimodal Live API / OpenAI Realtime API.
* **Execution:** Cloud GPU instances (e.g., AWS EC2, Modal, RunPod).
* **Role:**
  * **SAM 2 / Multimodal VLM:** Receives snapshot + YOLO bounding box coordinates to generate pixel-perfect masks or perform deep spatial verification.
  * **Gemini/ChatGPT Live:** Connects via WebSockets/WebRTC to stream sub-second voice assistance, manage conversational flow, and reference persistent patient data.

---

## 3. Comparing Local CV (YOLO) vs. Google VLMs (Gemini 2.0 / PaliGemma 2)

Google offers specialized Vision-Language Models with spatial reasoning capabilities:
1. **Gemini 2.0 / 1.5 (Cloud VLMs):** Natively detects objects and outputs 2D bounding boxes in normalized `[ymin, xmin, ymax, xmax]` format.
2. **PaliGemma 2 (Fine-Tuned Open VLM):** A lightweight (3B) open-weights VLM designed for direct fine-tuning on detection/segmentation tasks via text prompts (e.g., `"detect tooth 19"`).

### Tradeoff Comparison Matrix

| Metric / Dimension | Traditional Local CV (YOLO + SAM 2) | Large Cloud VLM (Gemini 2.0 / 1.5) | Fine-Tuned Open VLM (PaliGemma 2) |
| :--- | :--- | :--- | :--- |
| **Inference Speed** | **30 to 60+ FPS** (Local NPU) | **1 to 2 FPS** (Cloud API dependency) | **5 to 15 FPS** (Requires edge GPU/RAM) |
| **Edge Deployment** | Runs natively on **iPhone / Android** | **Cloud Only** (Requires Internet) | **Borderline** (Requires ~3GB–6GB Mobile RAM) |
| **Bounding Box Precision**| **Sub-pixel exact** (Math-driven) | **Approximate** (Tokenized integers 0–1000) | **Moderate** (Tokenized locations `<loc0500>`) |
| **Training Effort** | Medium (Requires bounding box annotations) | **Zero** (Zero-shot via prompt) | Low (Standard text-to-text JSON dataset) |
| **Cost at Scale** | **$0 / hour** (Runs on device) | Paid per image token via API | Server hosting costs per GPU instance |

### Leveraging Google VLMs in Your Pipeline
* **Auto-Annotation Strategy:** Pass unlabelled dental images into **Gemini 2.0 Flash** with a spatial prompt (`"Return 2D bounding boxes and FDI labels for all teeth"`) to automatically generate initial training labels for fine-tuning your fast on-device YOLO model.
* **Two-Tier Strategy:** Use on-device YOLO for ultra-fast 30 FPS bounding box overlays on the camera screen, while passing stabilized keyframes to **Gemini 2.0** for deep clinical reasoning and natural voice interaction.

---

## 4. Data Flow & Dental Graph Memory State

To prevent VLMs from hallucinating tooth numbers or losing track of context across video frames, maintain a structured **Patient Dental Graph**:

```json
{
  "patient_id": "P-88204",
  "scanned_teeth": {
    "FDI_19": {
      "spatial_status": "in_frame",
      "tracked_confidence": 0.94,
      "clinical_history": {
        "restoration": "Composite (2024)",
        "periodontal_depth": "3mm",
        "historical_notes": "Watch for distal margin wear"
      },
      "current_cv_detections": [
        {"class": "calculus_gingival", "confidence": 0.88},
        {"class": "gingival_redness", "severity": "mild"}
      ]
    }
  }
}
```

### Prompting Strategy
When sending data to the cloud VLM orchestrator, pass:
1. High-resolution cropped snapshot of the target tooth.
2. The structured JSON context object above containing historical dental records.
3. System instruction detailing non-diagnostic, educational conversational guidelines.

---

## 5. Real-World Optical & Hardware Considerations

### Smartphone Challenges & Workarounds
1. **Focus Limits (Macro DoF):** Standard phone lenses cannot focus closer than ~8–10 cm.
   * *Fix:* Use an inexpensive clip-on smartphone macro lens ($10–$15) to reduce focal distance to 2–3 cm.
2. **Specular Reflection (Saliva Glare):** Phone flashes cause bright white blown-out highlights on wet enamel.
   * *Fix:* Use software specular-filtering algorithms or attach a clip-on polarized light filter / tissue paper diffuser.

### Why Hands-Free / Meta Ray-Ban Wearables Present Challenges
* **No Near-Macro Focus:** Meta Ray-Bans and similar smart glasses are hyper-focalized for 1m to infinity. At 15–20 cm from a patient's mouth, video frames are completely blurry.
* **Parallax Error:** Temple-mounted cameras do not align with the wearer's exact line of sight at close range.
* **Recommended Hardware Alternative:** Pair smartphone software with an inexpensive intraoral Wi-Fi/USB video wand ($20–$50) featuring fixed macro focus and built-in ring LEDs.

---

## 6. Proof-of-Concept (PoC) Action Plan

1. **Benchmark Local Model:** Download the **Ultralytics App** on iOS/Android to test live YOLO inference speeds (30–60 FPS) on your handheld device.
2. **Build WebSocket Client:** Set up a lightweight mobile client (Flutter or React Native) streaming 1–2 FPS JPEG camera frames + PCM audio to Gemini Multimodal Live API via WebSockets.
3. **Train System 1 Model:** Fine-tune YOLOv11-Nano on open-source dental datasets (e.g., UFBA-UESC or IO150k) to classify teeth bounding boxes and numbering systems locally, using Gemini 2.0 to auto-label raw training images.