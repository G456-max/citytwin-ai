# CityTwin AI: Dual-Core Geospatial Compliance & Generative Verification Engine

CityTwin AI is an enterprise geospatial platform for municipal Right-of-Way (RoW) compliance auditing and photorealistic visual verification. It solves the critical disconnect between raw CAD blueprints, satellite/drone GIS data, and on-ground municipal reality.

---

## 🌟 Key Capabilities

### 1. Deterministic Geospatial Compliance Auditing (Zero Hallucination Math)
* **Metric UTM Projection:** Reprojects WGS84 GPS coordinates to local UTM Zone 44N (EPSG:32644).
* **Polygon Intersection Math:** Calculates exact square-meter encroachment areas (^2$) and maximum intrusion depths ({\text{max}}$).
* **Automated Risk Triage:** Grades violations into **Compliant**, **Low**, **Medium**, or **Critical** risk, assigning a corridor compliance grade (**A+ to F**).

### 2. Blueprint-Locked Generative Diffusion
* **Geometry-Constrained AI:** Uses ControlNet depth conditioning tied to Digital Elevation Models (DEM) to synthesize photorealistic road previews without altering engineered road geometry.
* **Environmental Styling Presets:** Simulates *Realistic Daylight*, *Nighttime Illumination*, *Monsoon Weather*, and *Eco-Green Corridors*.
* **Deterministic Fallback:** Includes a CPU-friendly OpenCV procedural rendering pipeline.

### 3. Tree Canopy & Green Cover Auditing
* **HSV Vegetation Filtering:** Detects foliage cover ( \le H \le 85$).
* **Canopy Loss Quantification:** Calculates exact canopy clearing area (^2$) and estimates tree removal counts for environmental clearance.

### 4. 3-Point GCP Affine Snapping
* **Least-Squares Solver:** Solves affine transformation matrices ($\mathbf{T} \cdot [x, y, 1]^T$) to auto-align unanchored CAD blueprints to real-world GPS benchmarks.

### 5. Automated Municipal PDF Reporting
* **Print-Ready Certificates:** Automatically compiles audit metrics, GIS coordinate logs, tree clearing stats, and digital signature stamps using ReportLab.

---

## 🏗️ Architecture

`mermaid
graph TD
    subgraph Ingestion
        A[Drone Orthomosaic GeoTIFF] --> B[Spatial Anchor Engine]
        C[CAD / Blueprints] --> B
        D[OSM / CartoDB Vectors] --> B
        B -->|3-Point GCP Snapping| E[Georeferenced WGS84 Base]
    end

    subgraph Backend Core
        E --> F[Discrepancy Engine]
        E --> G[Tree Canopy Auditor]
        E --> H[ControlNet Generative Engine]
        F & G --> I[PDF Report Generator]
    end

    subgraph Frontend Dashboard
        F --> J[Leaflet GIS Map]
        H --> K[Split Wipe Comparison Slider]
        I --> L[PDF Download]
    end
`

---

## 🚀 Quickstart

### Prerequisites
* Python 3.10+
* Windows / Linux / macOS

### Installation
`ash
git clone https://github.com/G456-max/citytwin-ai.git
cd citytwin-ai
pip install -r requirements.txt
`

### Launch the Platform
`ash
python run_real_demo.py
`
This automatically boots the FastAPI backend and opens the dashboard at http://127.0.0.1:8000.

---

## 🧪 Testing

Run the automated test suite:
`ash
python -m unittest test_real_suite.py
`

---

## 📜 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | /api/health | Hardware diagnostics and module load state |
| POST | /api/audit/run | Executes spatial discrepancy audit in UTM space |
| POST | /api/render/generate | Generates style-conditioned visual renders |
| POST | /api/addons/trees | Computes green canopy loss metrics |
| GET | /api/reports/download-pdf | Streams the formal municipal compliance report PDF |

---

## 📄 License
Apache 2.0 / MIT License.
