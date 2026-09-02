import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FRAMES_DIR = PROCESSED_DIR / "frames"

# Ensure directories exist
for directory in [DATA_DIR, RAW_DIR, PROCESSED_DIR, FRAMES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Compliance parameters
BLUR_THRESHOLD = 100.0
FRAME_INTERVAL = 15  # Extract keyframe every 15 frames

# Geospatial parameters
DEFAULT_WGS84 = "EPSG:4326"
DEFAULT_UTM = "EPSG:32644"  # Default local UTM zone for test corridor (UTM Zone 44N)

# Image synthesis constants
IMAGE_WIDTH = 512
IMAGE_HEIGHT = 512
