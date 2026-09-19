# Dental AI Mobile App Architecture Guide (Executive Summary)

## 1. System Architecture: Dual-Tier (Hybrid) Model

To handle live intraoral video, split processing between local edge computing and cloud reasoning:

```
┌─────────────────────────────────────────────────────────┐
│                      SMARTPHONE                         │
│  • Camera Stream (30 FPS)                               │
│  • Local YOLO (System 1): Bounding boxes, tooth IDs     │
│  • Quality Filter: Drops blurry/overexposed frames      │
└────────────────────────────┬────────────────────────────┘
                             │ Clean Snapshot + Boxes
                             ▼
┌─────────────────────────────────────────────────────────┐
│                      CLOUD BACKEND                      │
│  • SAM 2 / VLM: Fine-grained tooth segmentation         │
│  • Gemini Multimodal Live API: Voice & reasoning        │
│  • Patient Dental Graph: Historical state memory        │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Model Selection & Trade-Offs

| Component | Role | Best Model | Execution | Key Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Local CV (System 1)** | Real-time tracking & frame selection | **YOLOv11 Nano** | On-Device NPU (CoreML/TFLite) | **30+ FPS**, zero internet cost, smooth UI |
| **Cloud VLM (System 2)** | Voice assistant & spatial verification | **Gemini 2.0 / PaliGemma 2** | Cloud API (WebSockets) | Multimodal voice + zero-shot 2D detection |

### Using Google VLMs
* **Auto-Annotation:** Use **Gemini 2.0 Flash** to automatically draw 2D bounding boxes on unlabelled dental photos to generate training data for your local YOLO model.
* **Spatial Prompting:** Send clean snapshots to Gemini alongside a patient's historical records to discuss findings in natural language.

---

## 3. Data Linking via Patient Dental Graph

Do not stream raw video directly to an LLM. Map frame detections into a persistent JSON state layer:

```json
{
  "patient_id": "P-88204",
  "tooth_id": "FDI_19",
  "history": {"restoration": "Composite (2024)", "pocket_depth": "3mm"},
  "current_detection": {"class": "calculus", "confidence": 0.88}
}
```
*Send this JSON alongside the high-resolution snapshot to the cloud VLM for context-aware voice feedback.*

---

## 4. Hardware & PoC Strategy

* **Hardware Fixes:** Standard phone cameras cannot focus closer than ~8cm. Use a **$10 clip-on macro lens** and a light diffuser to prevent glare off saliva.
* **3-Minute Benchmark:** Download the **Ultralytics App** on your phone to test live YOLO inference speeds (30–60 FPS) immediately.
* **PoC Setup:** Build a simple app streaming 1–2 FPS frames + mic audio to the **Gemini Multimodal Live API** via WebSockets, gated by a local frame-quality filter.