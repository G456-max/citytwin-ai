import os
import rasterio
from shapely.geometry import box
import geopandas as gpd

class OrthomosaicHandler:
    """Manages raw GeoTIFF files, reads metadata, and calculates spatial footprints."""

    @staticmethod
    def get_raster_info(tif_path: str) -> dict:
        """
        Inspects the GeoTIFF raster to retrieve spatial parameters.
        
        Args:
            tif_path: Path to the GeoTIFF file.

        Returns:
            Dictionary containing metadata, spatial bounds, CRS, and pixel width/height.
        """
        if not os.path.exists(tif_path):
            raise FileNotFoundError(f"Target GeoTIFF raster not found: {tif_path}")

        with rasterio.open(tif_path) as src:
            bounds = src.bounds
            crs = src.crs.to_string() if src.crs else "EPSG:4326"
            width = src.width
            height = src.height
            count = src.count
            transform = src.transform
            
            # Estimate GSD (Ground Sampling Distance) in degrees/meters based on transform scale
            gsd_x = abs(transform[0])
            gsd_y = abs(transform[4])
            
        return {
            "bounds": {
                "left": bounds.left,
                "bottom": bounds.bottom,
                "right": bounds.right,
                "top": bounds.top
            },
            "crs": crs,
            "width": width,
            "height": height,
            "band_count": count,
            "gsd": (gsd_x + gsd_y) / 2.0
        }

    @staticmethod
    def create_aoi_footprint(tif_path: str, output_geojson_path: str) -> gpd.GeoDataFrame:
        """Extracts the spatial bounds of the raster and writes it as an AOI boundary GeoJSON."""
        info = OrthomosaicHandler.get_raster_info(tif_path)
        bounds = info["bounds"]
        
        # Create rectangular bounding box geometry
        aoi_polygon = box(bounds["left"], bounds["bottom"], bounds["right"], bounds["top"])
        gdf = gpd.GeoDataFrame(geometry=[aoi_polygon], crs=info["crs"])
        
        # Save to file
        os.makedirs(os.path.dirname(output_geojson_path), exist_ok=True)
        gdf.to_crs("EPSG:4326").to_file(output_geojson_path, driver="GeoJSON")
        
        return gdf
