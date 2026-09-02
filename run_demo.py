import os
import sys
import time
import subprocess
import webbrowser
import importlib
from pathlib import Path

def check_dependencies():
    """Checks if required libraries are installed, suggesting pip command if missing."""
    print("Checking system dependencies...")
    missing = []
    libs = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "geopandas": "geopandas",
        "shapely": "shapely",
        "rasterio": "rasterio",
        "ezdxf": "ezdxf",
        "cv2": "opencv-python-headless",
        "pyproj": "pyproj",
        "fiona": "fiona"
    }
    
    for lib_import, lib_pip in libs.items():
        try:
            importlib.import_module(lib_import)
        except ImportError:
            missing.append(lib_pip)
            
    if missing:
        print(f"\n[Warning] The following dependencies are missing: {', '.join(missing)}")
        print("Attempting to install them automatically using pip...")
        try:
            # Proactively install missing packages
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("Successfully installed missing packages.")
        except subprocess.CalledProcessError as e:
            print(f"\n[Error] Automatic package installation failed: {e}")
            print("Please run: pip install -r requirements.txt manually.\n")
            sys.exit(1)
    else:
        print("All required Python dependencies are present.")

def print_diagnostics():
    """Prints GPU/CPU device availability details for Stable Diffusion."""
    print("\n--- System Diagnostics ---")
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"CUDA status: AVAILABLE")
            print(f"GPU Device: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA status: UNAVAILABLE (will use high-fidelity CPU rendering).")
    except ImportError:
        print("PyTorch / Diffusers not installed (using high-fidelity CPU/OpenCV rendering mode).")
    print("--------------------------\n")

def main():
    # 1. Verify working directory
    base_dir = Path(__file__).resolve().parent
    os.chdir(base_dir)

    # 2. Run dependency checks
    check_dependencies()
    
    # 3. Print device diagnostics
    print_diagnostics()

    # 4. Generate mock data assets
    print("Initializing mock georeferenced spatial vectors and raster imagery...")
    try:
        import generate_mock_data
        generate_mock_data.main()
    except Exception as e:
        print(f"Error generating mock datasets: {e}")
        sys.exit(1)

    # 5. Launch FastAPI server
    print("\nLaunching CityTwin Compliance REST Server via Uvicorn...")
    server_process = None
    try:
        # Run uvicorn as a subprocess
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "backend.app:app", 
            "--host", "127.0.0.1", 
            "--port", "8000"
        ])
        
        # Wait a moment for server initialization
        time.sleep(2.5)
        
        # 6. Open dashboard in default browser
        dashboard_url = "http://127.0.0.1:8000/index.html"
        print(f"Opening dashboard viewport in browser: {dashboard_url}")
        webbrowser.open(dashboard_url)
        
        # Keep process running
        print("\nCityTwin AI running. Press Ctrl+C to terminate the session.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down server connection...")
    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("Server terminated successfully.")

if __name__ == "__main__":
    main()
