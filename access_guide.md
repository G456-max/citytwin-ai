# CityTwin AI - Quick Access & Setup Guide

This guide provides step-by-step instructions to configure, run, and interact with the **CityTwin AI** corridor compliance viewport.

---

## 1. Prerequisites

Before starting, ensure your local machine has:
- **Python 3.10 to 3.12** installed and configured in your system environment PATH variables.
- An active internet connection (required for the initial OpenStreetMap vector downloads and satellite map stitches).
- **Pip** (Python package installer) upgraded to the latest version.

---

## 2. Virtual Environment Configuration

Navigate to the project root directory and configure a clean virtual environment to prevent package conflicts:

### Windows PowerShell
```powershell
# Navigate to the OneDrive Desktop copy
cd "C:\Users\gudae mahalakshmi\OneDrive\Documents\Desktop\citytwin-ai"

# Create a clean virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies (FastAPI, GeoPandas, Rasterio, ReportLab, etc.)
pip install -r requirements.txt
```

---

## 3. Launching the System

The platform features an automated launcher script that automatically handles raw data ingestion, compiles terrain DEM grids, profiles hardware acceleration, boots Uvicorn, and launches the dashboard in your web browser:

```powershell
# Run the demo orchestrator
python run_real_demo.py
```

- **Dashboard UI URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **FastAPI OpenAPI Documentations:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 4. REST API Endpoint Catalog (cURL Examples)

You can query all compliance modules programmatically using `curl` or Postman. Ensure the FastAPI server is running beforehand.

### 4.1 System Health check
Queries computational devices (GPU availability) and active module status:
```bash
curl -X GET http://127.0.0.1:8000/api/health
```

### 4.2 Execute Compliance Audit
Segments the georeferenced orthomosaic and runs overlay checks on UTM projection:
```bash
curl -X POST http://127.0.0.1:8000/api/audit/run
```

### 4.3 Trigger Canopy Clearing Audit
Performs vegetation index classification and returns tree loss metrics:
```bash
curl -X POST http://127.0.0.1:8000/api/addons/trees
```

### 4.4 Render Future widening Synthesis
Generates depth-locked contextual forecasts based on specific styling presets:
```bash
curl -X POST http://127.0.0.1:8000/api/render/generate \
     -H "Content-Type: application/json" \
     -d '{"style": "Eco-Green Corridor", "prompt": "flyover deck with vertical green plants"}'
```

### 4.5 Stream Executive Compliance PDF
Streams a formal print-ready engineering audit sheet:
```bash
curl -o compliance_report.pdf http://127.0.0.1:8000/api/reports/download-pdf
```

---

## 5. Dashboard Visual Tour & Operations

Once the dashboard is loaded in your browser:

1. **Check Server Health:** Locate the indicator dot in the top right. A pulsing green dot labeled **ACCEL ACTIVE** indicates the FastAPI backend is running and connected.
2. **Execute Compliance Audit:** Click **Run Corridor Audit** in the header. The system segments structures, runs overlay math, draws blue statutory corridors and red physical violations on the Leaflet map, and populates cards in the sidebar.
3. **Verify Deviances:** Scroll through the sidebar. Each card outlines a structural encroachment (ID, area in $m^2$, max intrusion, and coordinates). Click **Snap Map** on any card to fly the Leaflet window directly to that violation polygon.
4. **Inspect Future Renders:** Navigate to the split slider. Choose a preset style (e.g. *Eco-Green* or *Nighttime*) and click **Render**. Move the slider handle in the center back and forth to overlay and compare the raw aerial photo with the CAD-locked texture forecast.
5. **Download PDF Report:** Click **Download Executive PDF**. The backend compiles the scorecards, generates validation stamps, and streams the document directly into your browser download queue.
