import os
import json
import numpy as np
import cv2
import geopandas as gpd
from shapely.geometry import LineString, Polygon, mapping
import rasterio
from rasterio.transform import from_bounds
from pathlib import Path
from backend.config import RAW_DIR, DATA_DIR

def generate_depth_map(output_path: str):
    """Generates a synthetic 16-bit depth map of an elevated flyover."""
    print("Generating synthetic CAD depth map...")
    h, w = 512, 512
    # Grayscale image (0-255 representing depth buffer)
    depth = np.zeros((h, w), dtype=np.uint8)
    
    # Draw a curved flyover road in perspective
    # Define centerline path points for the road
    points = np.array([
        [150, 480],
        [200, 360],
        [260, 240],
        [290, 150],
        [300, 30]
    ], dtype=np.int32)
    
    # Draw the main bridge structure with varying width (simulating perspective)
    # At depth = 20 (base level) to depth = 220 (elevated deck)
    for i in range(len(points) - 1):
        pt1, pt2 = points[i], points[i+1]
        
        # Calculate width of bridge deck at this section (perspective narrowing)
        w1 = int(75 - (480 - pt1[1]) * 0.08)
        w2 = int(75 - (480 - pt2[1]) * 0.08)
        
        # Calculate normal vectors to find edge points
        dx, dy = pt2[0] - pt1[0], pt2[1] - pt1[1]
        length = np.hypot(dx, dy)
        nx, ny = -dy / length, dx / length
        
        # Left and right boundary coordinates for deck polygon
        l1 = pt1 + nx * w1
        r1 = pt1 - nx * w1
        l2 = pt2 + nx * w2
        r2 = pt2 - nx * w2
        
        poly = np.array([l1, r1, r2, l2], dtype=np.int32)
        
        # Depth value changes gradually from 30 (close) to 180 (far elevated deck)
        depth_val = int(40 + (480 - (pt1[1] + pt2[1])/2) * 0.3)
        cv2.fillPoly(depth, [poly], depth_val)
        
    # Apply a light gaussian blur to smooth depth transitions
    depth_smooth = cv2.GaussianBlur(depth, (15, 15), 0)
    
    # Save as 8-bit png (which functions as 16-bit depth buffer mock)
    cv2.imwrite(output_path, depth_smooth)
    print(f"CAD depth map saved to {output_path}")

def generate_gis_vectors():
    """Generates synthetic GeoJSON files for the road boundary and structures."""
    print("Generating GIS vector layers...")
    
    # Corridor centerline path in EPSG:4326 (WGS84)
    centerline_coords = [
        (80.3250, 26.4710),
        (80.3252, 26.4712),
        (80.3255, 26.4715),
        (80.3258, 26.4718),
        (80.3260, 26.4720),
        (80.3262, 26.4722),
        (80.3265, 26.4725),
        (80.3268, 26.4728),
        (80.3270, 26.4730)
    ]
    
    centerline = LineString(centerline_coords)
    
    # Convert to metric UTM CRS to perform precise buffering (12m width)
    # UTM Zone 44N (EPSG:32644) covers Kanpur, India (80E coordinates)
    gdf_center = gpd.GeoDataFrame(geometry=[centerline], crs="EPSG:4326")
    gdf_center_m = gdf_center.to_crs("EPSG:32644")
    
    # Buffer by 6.0m (results in a 12.0m Right-of-Way corridor)
    gdf_row_m = gdf_center_m.copy()
    gdf_row_m.geometry = gdf_center_m.geometry.buffer(6.0)
    
    # Reproject back to WGS84
    gdf_row = gdf_row_m.to_crs("EPSG:4326")
    row_path = RAW_DIR / "sanctioned_road_boundary.geojson"
    gdf_row.to_file(str(row_path), driver="GeoJSON")
    print(f"Sanctioned road RoW saved to {row_path}")

    # Generate 3 building structure polygons
    # Struct 1: Compliant (outside RoW buffer)
    # Struct 2: Encroaching (overlaps boundary by ~3.2m)
    # Struct 3: Critically Encroaching (overlaps boundary by ~4.5m)
    
    structures_data = [
        {
            "id": "BUILDING_001",
            "name": "Compliant Commercial Plaza",
            "geometry": Polygon([
                (80.3248, 26.4716),
                (80.3250, 26.4716),
                (80.3250, 26.4718),
                (80.3248, 26.4718)
            ])
        },
        {
            "id": "BUILDING_002",
            "name": "Illegal Shop Extension",
            "geometry": Polygon([
                (80.3259, 26.4718),
                (80.3262, 26.4718),
                (80.3262, 26.47195),
                (80.3259, 26.47195)
            ])
        },
        {
            "id": "BUILDING_003",
            "name": "Residential Boundary Wall",
            "geometry": Polygon([
                (80.32645, 26.4725),
                (80.3267, 26.4725),
                (80.3267, 26.4727),
                (80.32645, 26.4727)
            ])
        }
    ]
    
    gdf_structs = gpd.GeoDataFrame(structures_data, crs="EPSG:4326")
    structs_path = RAW_DIR / "detected_structures.geojson"
    gdf_structs.to_file(str(structs_path), driver="GeoJSON")
    print(f"Detected structures saved to {structs_path}")

def generate_orthomosaic_tiff():
    """Generates a synthetic georeferenced GeoTIFF orthomosaic image."""
    print("Generating synthetic orthomosaic TIFF...")
    tif_path = RAW_DIR / "corridor_orthomosaic.tif"
    
    # 500x500 3-band raster (RGB)
    width, height = 500, 500
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Fill with base ground color (earthy gray-green)
    image[:, :, 0] = 75  # R
    image[:, :, 1] = 95  # G
    image[:, :, 2] = 80  # B
    
    # Draw a diagonal road matching the flight path coordinates
    # We map coordinates to pixel bounds
    cv2.line(image, (50, 450), (450, 50), (60, 60, 62), 65) # Road baseline asphalt
    cv2.line(image, (50, 450), (450, 50), (255, 255, 255), 3) # Center divider (white)
    
    # Draw building footprints onto the raw orthomosaic
    # Shop extension (violator)
    cv2.rectangle(image, (260, 240), (320, 280), (120, 100, 80), -1)
    # Residential Wall (violator)
    cv2.rectangle(image, (380, 120), (420, 180), (140, 140, 140), -1)
    # Compliant commercial
    cv2.rectangle(image, (80, 380), (130, 420), (100, 110, 130), -1)

    # Set spatial bounds (same coordinate bounds as our study corridor)
    # minx, miny, maxx, maxy
    minx, miny = 80.3245, 26.4705
    maxx, maxy = 80.3275, 26.4735
    
    # Create coordinate transform
    transform = from_bounds(minx, miny, maxx, maxy, width, height)
    
    # Write GeoTIFF using rasterio
    with rasterio.open(
        tif_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=3,
        dtype='uint8',
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        # Transpose image array to shape (channels, height, width)
        dst.write(image[:, :, 0], 1) # Red
        dst.write(image[:, :, 1], 2) # Green
        dst.write(image[:, :, 2], 3) # Blue
        
    print(f"Orthomosaic TIFF saved to {tif_path}")

def generate_drone_video():
    """Generates a synthetic MP4 video representing drone footage sweep."""
    print("Generating synthetic drone footage video...")
    video_path = RAW_DIR / "corridor_flight.mp4"
    
    # 640x360 resolution video, 30 frames
    width, height = 640, 360
    fps = 10
    duration_sec = 4
    total_frames = fps * duration_sec
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
    
    # Render frames showing top-down corridor flying forward
    for f in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Background grass ground
        frame[:, :] = [45, 80, 50]
        
        # Draw road scrolling down (simulating flying forward)
        offset = int((f / total_frames) * 150)
        
        # Diagonal road
        cv2.line(frame, (0 - offset, height + offset), (width - offset, 0 - offset), (65, 65, 65), 80)
        cv2.line(frame, (0 - offset, height + offset), (width - offset, 0 - offset), (255, 255, 255), 2)
        
        # Add random noise to simulate drone camera jitter
        # Periodically make frames blurry to test Laplacian blur filtering (e.g. frame 10 and 20)
        if f in (8, 9, 18, 19):
            # Blurry frame
            frame = cv2.GaussianBlur(frame, (31, 31), 0)
            cv2.putText(frame, "CAMERA JITTER BLUR", (150, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        else:
            # Sharp frame
            cv2.putText(frame, f"DRONE CH: 0+{f*15:03d}m", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
        out.write(frame)
        
    out.release()
    print(f"Drone video flight sweep saved to {video_path}")

def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(DATA_DIR / "processed", exist_ok=True)
    
    generate_depth_map(str(RAW_DIR / "cad_depth.png"))
    generate_gis_vectors()
    generate_orthomosaic_tiff()
    generate_drone_video()
    print("Mock data generation completed successfully!")

if __name__ == "__main__":
    main()
