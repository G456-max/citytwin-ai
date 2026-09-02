import os
import ezdxf
import fiona
import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import unary_union
import pyproj
from pathlib import Path
from typing import Optional, Union

# Enable KML driver in Fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

class CADVectorProcessor:
    """Ingests municipal engineering and GIS formats, converting them to standard georeferenced GeoJSON."""

    @staticmethod
    def _parse_dxf(input_path: str) -> gpd.GeoDataFrame:
        """Parses a DXF file using ezdxf and converts layers to a GeoDataFrame."""
        try:
            doc = ezdxf.readfile(input_path)
        except Exception as e:
            raise ValueError(f"Failed to parse DXF file: {str(e)}")
            
        msp = doc.modelspace()
        features = []
        
        # We search for lines, polylines, lwpolylines, and circles
        for entity in msp:
            layer = entity.dxf.layer
            geom = None
            
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                geom = LineString([(start.x, start.y), (end.x, end.y)])
                
            elif entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                points = []
                for p in entity.get_points():
                    # get_points returns a tuple where the first elements are x and y
                    points.append((p[0], p[1]))
                if len(points) >= 2:
                    if entity.is_closed:
                        # If closed and has at least 3 points, make a polygon
                        if len(points) >= 3:
                            # Ensure we don't repeat the start point when constructing Polygon, Shapely handles it
                            geom = Polygon(points)
                        else:
                            geom = LineString(points)
                    else:
                        geom = LineString(points)
                        
            if geom is not None:
                features.append({
                    "geometry": geom,
                    "properties": {
                        "layer": layer,
                        "dxftype": entity.dxftype()
                    }
                })
                
        if not features:
            raise ValueError(f"No valid geometric entities found in DXF file: {input_path}")
            
        gdf = gpd.GeoDataFrame.from_features(features)
        return gdf

    @classmethod
    def convert_to_standard_geojson(
        cls, 
        input_path: str, 
        output_geojson_path: str, 
        source_crs: Optional[str] = None,
        target_crs: str = "EPSG:4326"
    ) -> gpd.GeoDataFrame:
        """
        Ingests vectors (DXF, SHP, KML, GeoJSON) and outputs standard reprojected GeoJSON.

        Args:
            input_path: Path to the input file.
            output_geojson_path: Path to save the processed GeoJSON.
            source_crs: CRS of input data if not automatically detectable (e.g. for DXF).
            target_crs: Target coordinate system.

        Returns:
            The reprojected GeoDataFrame.
        """
        input_path_obj = Path(input_path)
        ext = input_path_obj.suffix.lower()
        
        # Ingest the source file
        if ext == ".dxf":
            gdf = cls._parse_dxf(input_path)
        else:
            # geopandas read_file handles SHP, GeoJSON, and KML (via fiona KML driver)
            gdf = gpd.read_file(input_path)
            
        if gdf.empty:
            raise ValueError(f"Loaded dataset is empty: {input_path}")

        # Set or detect CRS
        if gdf.crs is None:
            if source_crs:
                gdf.set_crs(source_crs, inplace=True)
            else:
                # Default to metric/local UTM coordinates or WGS84 depending on dimensions
                # Check if coordinates are in degrees (lat/lon look like numbers under 180)
                bounds = gdf.total_bounds
                is_geographic = all(-180 <= val <= 180 for val in bounds)
                detected = "EPSG:4326" if is_geographic else "EPSG:32644"
                gdf.set_crs(detected, inplace=True)
        
        # Reproject to target
        gdf_reprojected = gdf.to_crs(target_crs)
        
        # Ensure geometry is valid
        gdf_reprojected.geometry = gdf_reprojected.geometry.make_valid()
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_geojson_path), exist_ok=True)
        
        # Save as GeoJSON
        # If writing KML properties or lists, convert properties to clean strings to prevent write errors
        clean_properties = {}
        for col in gdf_reprojected.columns:
            if col != 'geometry':
                gdf_reprojected[col] = gdf_reprojected[col].astype(str)
                
        gdf_reprojected.to_file(output_geojson_path, driver="GeoJSON")
        
        return gdf_reprojected
