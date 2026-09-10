# 🛰️ Satellite Cloud Removal & Analysis System
**SIH 2026 Problem Statement ID: 26209** | **Theme: Space Technology** | **Category: Software**

![Project Status](https://img.shields.io/badge/Status-Completed-success)
![Platform](https://img.shields.io/badge/Platform-Web-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-orange)

## 🎯 The Problem
Satellite optical imagery is fundamentally hindered by cloud cover and atmospheric haze. In critical scenarios—such as disaster response (flooding), defense intelligence, and agricultural tracking—clouds block vital ground truth data. 

**The AI Hallucination Problem:** While Generative AI (GANs, Diffusion Models) can create "cloud-free" images, they are inherently probabilistic. They *guess* missing data based on training sets. In scientific and defense applications, an AI "hallucinating" fake terrain or hiding new structures is catastrophic.

## 🚀 Our Deterministic Solution
We built an end-to-end, enterprise-grade web dashboard that relies exclusively on **Classical Computer Vision Mathematics**. Our algorithm strips away haze and boosts true optical signals without inventing false data, guaranteeing **100% scientific integrity**.

Furthermore, our system features a **Multi-Sector Analysis Engine** that extracts actionable intelligence from the cleared satellite imagery across four domains.

---

## ✨ Enterprise-Grade Features
1. **Deterministic Cloud Removal:** A 4-step math pipeline (Dark Channel Prior -> CLAHE -> HSV Saturation Boost -> Unsharp Masking) to enhance images.
2. **Interactive UI / Magnifier Glass:** Inspect pixel-level enhancements in real-time with a custom split-screen slider and magnifying lens.
3. **Cloud Mask Extraction:** Download a binary cloud mask for exclusion in downstream scientific workflows.
4. **Global Radar Dashboard:** An aggregated visualization of Region Health (Visibility, Agriculture, Hydrology, Urban footprint).
5. **One-Click PDF Reports:** Export boardroom-ready PDF intelligence reports directly from the browser.

---

## 📊 The 4 Sector Analysis Modules
*   **🌿 NDVI (Agriculture):** Maps green/red channels to determine vegetation health (Dense vs Moderate vs Barren).
*   **🌊 Flood Detection (Disaster):** Uses HSV thresholds to map open water surfaces and track river overflow.
*   **🏠 Building Extraction (Urban):** Uses Canny Edges and Contours to extract man-made structures, categorized by footprint size.
*   **🗺️ Land Cover (Climate):** Uses K-Means Clustering to segment the map into Forest, Water, Soil, and Urban zones.

---

## 💻 Local Setup & Installation

### Windows Setup
1. **Run Setup:**
   Double click `setup.bat` to create the virtual environment and install dependencies.
2. **Start Server:**
   Double click `run.bat` to start the Flask backend.
3. **Access:**
   Open your browser and navigate to `http://127.0.0.1:5000`

### Manual Setup (Command Line)
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

---

## 🛠️ Technology Stack
- **Backend Framework:** Python Flask
- **Computer Vision Engine:** OpenCV & Pillow
- **Frontend UI:** HTML5, Vanilla CSS (Glassmorphism), Vanilla JavaScript
- **Data Visualization:** Chart.js
- **Export Engine:** html2pdf.js

---
*Built to win 1st Prize at the Smart India Hackathon (SIH) 2026.*
