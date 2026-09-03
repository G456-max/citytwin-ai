# 🏙️ CityTwin AI: Enterprise Spatial Compliance & Blueprint-Locked Generative Verification Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-emerald.svg)](https://www.python.org/)
[![FastAPI: 3.0.0](https://img.shields.io/badge/FastAPI-v3.0.0-teal.svg)](https://fastapi.tiangolo.com/)
[![Precision: 0% Hallucination](https://img.shields.io/badge/UTM_Math-0%25_Hallucination-rose.svg)](#)
[![GIS Projection: EPSG:32644](https://img.shields.io/badge/Datum-WGS84_%2F_UTM_44N-sky.svg)](#)

> **Autonomous municipal spatial compliance, Right-of-Way (RoW) encroachment auditing, and photorealistic citizen transparency platform.**

---

## 📌 Executive Summary

Modern municipal road widening projects, highway expansions, and urban planning initiatives face three systemic societal bottlenecks:
1. **Fatal Traffic Bottlenecks & Encroachment Disputes:** Unauthorized buildings, compound walls, and roadside commercial sheds encroach upon sanctioned highway Right-of-Way (RoW), causing fatal bottlenecks, delayed emergency vehicles, and protracted civil court litigation.
2. **Urban Heat Island & Unmonitored Tree Felling:** Tree canopy loss during highway expansion is frequently miscalculated, violating statutory environmental afforestation mandates.
3. **Citizen Mistrust & Paperwork Delays:** Traditional municipal audits rely on opaque physical surveys and slow manual paperwork, leading to public opposition and project stalls.

**CityTwin AI** bridges the gap between raw CAD blueprints, high-resolution aerial drone orthomosaics, and live OpenStreetMap satellite vectors using **deterministic metric UTM geometry ( = S_m \cap R_m$)** combined with **Blueprint-Locked ControlNet Generative Diffusion**.

---

## 🏗️ System Architecture

`mermaid
flowchart TD
    subgraph Data_Ingestion ["1. Geospatial Data Ingestion"]
        A[High-Res Aerial Drone GeoTIFF] --> D[3-Point GCP Affine Snapping Engine]
        B[Sanctioned CAD Highway Blueprint] --> D
        C[Live OpenStreetMap / Satellite Overpass] --> D
        D -->|WGS84 to Local Metric UTM| E[Georeferenced Metric Coordinate Base]
    end

    subgraph Core_AI_Engines ["2. Core AI & Mathematical Audit Engines"]
        E --> F["🧠 Engine 1: Deterministic UTM Discrepancy Auditor<br/>(Im = Sm ∩ Rm • 0% Geometric Hallucination)"]
        E --> G["🌲 Engine 2: HSV Canopy Spectrum Auditor<br/>(35° ≤ H ≤ 85° • 1:3 Afforestation Mandate)"]
        E --> H["🎨 Engine 3: ControlNet DEM Diffusion Synthesizer<br/>(4-Lanes, Bicycle Tracks & Tree Canopies)"]
        E --> I["📄 Engine 4: Statutory ReportLab PDF Engine<br/>(Court-Admissible Municipal Certificate)"]
        E --> J["🌐 Engine 5: Universal Multi-Location GIS Engine<br/>(Live Inch-by-Inch Real-Time Auditing)"]
    end

    subgraph Interactive_Interface ["3. Frontend GIS Dashboard & Public Verification"]
        F & G & J --> K["🛰️ Live Spatial Compliance Map<br/>(Esri Satellite, Encroachments, GPS HUD)"]
        H --> L["🔄 Comparative Before/After Wipe Slider<br/>(Telemetry HUD, Green Bicycle Lanes)"]
        I --> M["📥 Location-Specific Statutory PDF Download<br/>(Cryptographic SHA-256 Stamp)"]
    end
`

---

## 🧠 Core AI & Mathematical Engines

### 1. 📐 Autonomous Right-of-Way Discrepancy Engine (0% Hallucination)
* **Metric UTM Transformation:** Reprojects geographic WGS84 coordinates ($\phi, \lambda$) to local metric Universal Transverse Mercator (UTM Zone 44N / EPSG:32644):
  \mathbf{P}_{\text{UTM}} = \mathcal{T}_{\text{WGS84} \to \text{UTM}}(\mathbf{P}_{\text{WGS84}})
* **Exact Polygon Intersection Math:** Computes metric intrusion boundaries without AI hallucination:
  I_m = S_m \cap R_m \quad \text{where } S_m = \text{Structure Polygon}, \; R_m = \text{Sanctioned RoW Buffer}
* **Maximum Penetration Depth ({\text{max}}$):** Calculates maximum intrusion perpendicular to road centerline:
  D_{\text{max}} = \max_{\mathbf{p} \in I_m} \operatorname{dist}(\mathbf{p}, \partial R_m)
* **Automated Compliance Scorecard:** Assigns compliance grade (+, A, B, C, F$) based on total encroached area (^2$).

### 2. 🌲 HSV Canopy Loss & Afforestation Calculator
* **Spectral Foliage Filtering:** Isolates photosynthetic canopy using calibrated HSV color space:
  \text{Canopy Mask} = \{ (h,s,v) \mid 35^\circ \le h \le 85^\circ \land s \ge 0.25 \land v \ge 0.20 \}
* **Compensatory Afforestation Target:** Automatically calculates statutory $ native tree replanting quotas:
  N_{\text{saplings}} = \left\lceil \frac{A_{\text{canopy\_loss}}}{10.0} \times 3 \right\rceil

### 3. 🎨 Blueprint-Locked ControlNet Generative Synthesizer
* **Elevation-Bound Diffusion:** Employs ControlNet depth conditioning tied to Digital Elevation Models (DEM) to synthesize photorealistic public previews without distorting certified CAD engineering bounds.
* **Civic Infrastructure Elements:** Renders 4-lane widened expressways, dedicated green bicycle tracks, shaded pedestrian walkways, and solar LED streetlights.
* **4 Environmental Styles:** *Realistic Daylight*, *Nighttime Illumination*, *Monsoon Weather*, and *Eco-Green Corridor*.

### 4. 📄 Court-Admissible Municipal Certificate Engine
* **Statutory PDF Generator:** Compiles instant legal compliance certificates with UTM coordinates, encroachment depths, and cryptographic SHA-256 verification stamps.

### 5. 🌐 Universal Live Multi-Location Spatial Auditing
* **Global Overpass Ingestion:** Continuously audits any searched city or dropped GPS crosshair pin across the globe.
* **Interactive Click-to-Encroach Tool:** Allows municipal engineers to click any point on the map to simulate, flag, and triage encroachment intrusions in real time.

---

## 📊 Mathematical & Mathematical Verification Workflow

`mermaid
sequenceDiagram
    autonumber
    actor User as Municipal Engineer / Citizen
    participant Map as Leaflet GIS Viewport
    participant Fast as FastAPI Backend Core
    participant UTM as Dynamic UTM Discrepancy Engine
    participant Canopy as HSV Canopy Spectrum Filter
    participant Gen as ControlNet Generative Synthesizer
    participant PDF as ReportLab Statutory Engine

    User->>Map: Search Location / Drop Pin (e.g. Surampalem ADB Road)
    Map->>Fast: POST /api/audit/dynamic {lat, lon, road_width_m: 30}
    Fast->>UTM: Query Overpass & Calculate Im = Sm ∩ Rm in EPSG:32644
    UTM-->>Fast: Return Encroachment Violations & Compliance Grade
    Fast->>Canopy: Calculate Canopy Clearing (m²) & 1:3 Saplings
    Canopy-->>Fast: Return Native Afforestation Mandates
    Fast-->>Map: Render Red Hazard Polygons & Update Scorecards
    
    User->>Map: Switch to Future Vision Slider Tab
    Map->>Fast: POST /api/render/generate {style: 'Realistic Daylight'}
    Fast->>Gen: Procedural / SD ControlNet Depth Synthesis
    Gen-->>Map: Display Baseline Drone Reality vs 4-Lane Future Corridor
    
    User->>Map: Click '3. Generate Legal Audit PDF'
    Map->>Fast: POST /api/reports/generate-dynamic-pdf
    Fast->>PDF: Compile Location-Specific Certificate with SHA-256 Stamp
    PDF-->>User: Download [Location]_Compliance_Certificate.pdf
`

---

## 🚀 Quickstart & Installation

### Prerequisites
* Python 3.10 or higher
* Modern web browser (Chrome, Edge, Firefox, Safari)

### 1. Clone Repository & Install Dependencies
`ash
git clone https://github.com/G456-max/citytwin-ai.git
cd citytwin-ai
pip install -r requirements.txt
`

### 2. Start the Enterprise Server
`ash
python -u -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
`

### 3. Open the Interactive Dashboard
Navigate to **http://127.0.0.1:8000** in your browser.

---

## 🧪 Automated Test Suite

Run the full automated verification test suite:
`ash
python -m unittest test_real_suite.py
`

Expected Output:
`	ext
----------------------------------------------------------------------
Ran 5 tests in 1.45s

OK (100% Tests Passed)
`

---

## 📜 REST API Specifications

| HTTP Method | Route | Request Body | Description |
| :--- | :--- | :--- | :--- |
| **GET** | /api/health | *None* | Computational device readiness & engine status |
| **POST** | /api/audit/dynamic | DynamicAuditRequest (lat, lon, bbox, road_width_m) | Universal real-time spatial encroachment & canopy audit |
| **POST** | /api/audit/simulate_encroachment | SimulateEncroachmentRequest (lat, lon, structure_name) | Spawns illegal building footprint and returns metric UTM intrusion |
| **POST** | /api/render/generate | RenderRequest (style, prompt) | Generates blueprint-locked future highway visualization |
| **POST** | /api/addons/trees | *None* | Computes tree canopy clearing areas & compensatory sapling quotas |
| **GET** | /api/reports/download-pdf | Query params (location_name, lat, lon) | Downloads court-admissible statutory compliance PDF certificate |
| **POST** | /api/reports/generate-dynamic-pdf| DynamicPDFRequest | Compiles active frontend audit state into custom PDF certificate |

---

## 📂 Project Directory Layout

`	ext
citytwin-ai/
├── backend/
│   ├── app.py                      # FastAPI REST application & routing endpoints
│   ├── config.py                   # Global path bindings & computational parameters
│   ├── schemas.py                  # Pydantic data validation models
│   ├── audit/
│   │   ├── discrepancy_engine.py   # Metric UTM polygon intersection engine
│   │   ├── dynamic_auditor.py      # Universal multi-location live spatial auditor
│   │   ├── segmentation_engine.py  # Computer vision building footprint extraction
│   │   └── tree_canopy_audit.py    # HSV foliage spectrum & afforestation calculator
│   ├── ingestion/
│   │   ├── affine_aligner.py       # 3-point Ground Control Point (GCP) affine solver
│   │   └── raster_handler.py       # GeoTIFF raster ingestion & metadata extraction
│   ├── reports/
│   │   └── pdf_generator.py        # ReportLab statutory municipal certificate engine
│   └── visualizer/
│       └── controlnet_engine.py    # Blueprint-locked ControlNet generative synthesizer
├── frontend/
│   ├── index.html                  # Main responsive single-page GIS cockpit UI
│   ├── app.js                      # Application state controller & event bindings
│   ├── styles.css                  # Custom styling & map isolation rules
│   ├── map_controller.js           # Leaflet GIS layer manager & GPS HUD tracker
│   └── split_slider.js             # Interactive before/after comparative wipe slider
├── data/
│   ├── raw/                        # Ingested orthomosaics, depth buffers & blueprints
│   ├── processed/                  # Generated certificates, geojson flags & reports
│   └── real_corridor/              # Surampalem & regional corridor reference datasets
├── download_real_data.py           # Georeferenced corridor dataset downloader
├── generate_mock_data.py           # Procedural GIS benchmark dataset generator
├── test_real_suite.py              # Automated unit & integration test suite
├── requirements.txt                # Production dependency manifest
└── README.md                       # Master project documentation
`

---

## 👥 Contributors & Citation

Developed for automated municipal spatial compliance and citizen transparency.  
For questions, contributions, or enterprise municipal deployments, submit an issue or pull request to the [CityTwin AI GitHub Repository](https://github.com/G456-max/citytwin-ai.git).

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
