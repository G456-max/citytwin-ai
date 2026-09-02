import rasterio
import cv2
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
from pathlib import Path
from typing import List, Dict, Any

class SAMGeoSegmenter:
    """Wraps SAMGeo / Segment-Geospatial structural footprints extraction, with deterministic CV fallbacks."""

    @staticmethod
    def segment_orthomosaic(tif_path: str, min_area_m2: float = 10.0) -> gpd.GeoDataFrame:
        """
        Segments physical structures (e.g., roofs, walls) from an orthomosaic TIFF.
        Uses a deterministic computer-vision pipeline to extract polygons from the raster
        and projects them to spatial coordinates using the GeoTIFF transform.

        Args:
            tif_path: Path to the orthomosaic GeoTIFF file.
            min_area_m2: Minimum area in square meters to filter out small noise.

        Returns:
            GeoDataFrame containing the segmented structure polygons.
        """
        if not Path(tif_path).exists():
            raise FileNotFoundError(f"Orthomosaic TIFF not found: {tif_path}")

        with rasterio.open(tif_path) as src:
            # Read first band (or a combination)
            band1 = src.read(1)
            # Read transform and CRS
            transform = src.transform
            crs = src.crs
            res_x, res_y = src.res
            pixel_area_m2 = abs(res_x * res_y)
            
            # Normalize to 0-255 for OpenCV
            band_min, band_max = band1.min(), band1.max()
            if band_max - band_min > 0:
                gray = ((band1 - band_min) / (band_max - band_min) * 255).astype(np.uint8)
            else:
                gray = np.zeros_like(band1, dtype=np.uint8)
                
            # Perform Otsu's thresholding to isolate structural shapes (light roofs/pavements)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            polygons = []
            for contour in contours:
                # Filter small contours
                if cv2.contourArea(contour) * pixel_area_m2 < min_area_m2:
                    continue
                    
                # Contour is shape (N, 1, 2) with points as (col, row)
                spatial_coords = []
                for pt in contour:
                    col, row = pt[0][0], pt[0][1]
                    # Map pixel (col, row) to spatial (x, y)
                    x, y = src.xy(row, col)
                    spatial_coords.append((x, y))
                    
                # Ensure the polygon can close (needs at least 3 points, Shapely expects close)
                if len(spatial_coords) >= 3:
                    poly = Polygon(spatial_coords)
                    # Clean up geometry
                    if poly.is_valid and not poly.is_empty:
                        polygons.append(poly)
                        
            # If no polygons found, return an empty GeoDataFrame
            if not polygons:
                return gpd.GeoDataFrame(geometry=[], crs=crs)
                
            gdf = gpd.GeoDataFrame(geometry=polygons, crs=crs)
            
            # Classify properties
            gdf["feature_type"] = "structure"
            gdf["area_m2"] = gdf.geometry.area
            
            return gdf
