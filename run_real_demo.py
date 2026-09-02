import os
import sys
import webbrowser
import uvicorn
import torch
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from backend.config import RAW_DIR

def check_datasets():
    """Checks if target real-world GIS folders hold downloaded files; queries Overpass if missing."""
    ortho = RAW_DIR.parent / "real_corridor" / "corridor_orthomosaic.tif"
    row = RAW_DIR.parent / "real_corridor" / "sanctioned_road_boundary.geojson"
    depth = RAW_DIR.parent / "real_corridor" / "real_corridor_depth.png"
    
    if not (ortho.exists() and row.exists() and depth.exists()):
        print("Required real-world Kanpur/Rajamahendravaram datasets missing. Launching downloader...")
        import download_real_data
        download_real_data.main()
    else:
        print("Geospatial datasets found. Proceeding to startup...")

def probe_acceleration():
    """Identifies if CUDA is active and prints device configuration logs."""
    cuda = torch.cuda.is_available()
    print("--------------------------------------------------")
    print("CITYTWIN AI COMPLIANCE ENGINE - DEVICE PROFILING")
    print("--------------------------------------------------")
    if cuda:
        print(f"GPU ACCELERATION: ACTIVE (Device: {torch.cuda.get_device_name(0)})")
    else:
        print("GPU ACCELERATION: INACTIVE (Device: CPU Core Fallback)")
    print("--------------------------------------------------")

def main():
    # 1. Ingest real-world geospatial layers
    check_datasets()

    # 2. Probe system hardware acceleration
    probe_acceleration()

    # 3. Open browser view in background thread (FastAPI finishes booting in ~1s)
    webbrowser.open("http://127.0.0.1:8000")

    # 4. Start Uvicorn server
    print("Launching Uvicorn server on http://127.0.0.1:8000...")
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
