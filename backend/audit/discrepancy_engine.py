import os
import datetime
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from shapely.validation import make_valid
from pathlib import Path
from typing import Dict, Any, List

class CorridorDiscrepancyAuditor:
    """Performs deterministic spatial compliance auditing against sanctioned Right-of-Way (RoW) polygons."""

    def __init__(self, sanctioned_row_path: str):
        """Loads and prepares the sanctioned Right-of-Way boundary corridor."""
        if not os.path.exists(sanctioned_row_path):
            raise FileNotFoundError(f"Sanctioned road boundary file not found at: {sanctioned_row_path}")
            
        self.sanctioned_row_gdf = gpd.read_file(sanctioned_row_path)
        if self.sanctioned_row_gdf.empty:
            raise ValueError(f"Sanctioned road boundary file is empty: {sanctioned_row_path}")
            
        # Ensure standard coordinate system on load
        if self.sanctioned_row_gdf.crs is None:
            self.sanctioned_row_gdf.set_crs("EPSG:4326", inplace=True)
        elif self.sanctioned_row_gdf.crs != "EPSG:4326":
            self.sanctioned_row_gdf = self.sanctioned_row_gdf.to_crs("EPSG:4326")
            
        self.sanctioned_row_gdf.geometry = self.sanctioned_row_gdf.geometry.apply(make_valid)

    def audit_structures(
        self, 
        structures_gdf: gpd.GeoDataFrame, 
        target_utm_crs: str = "EPSG:32644", 
        output_flags_path: str = "data/processed/discrepancy_flags.geojson"
    ) -> Dict[str, Any]:
        """
        Runs spatial intersection, reprojects geometries to calculate metrics, and tags severities.

        Args:
            structures_gdf: GeoDataFrame containing WGS84 structure footprints.
            target_utm_crs: Metric projected CRS (UTM) for calculations.
            output_flags_path: Path to write the WGS84 discrepancy GeoJSON.

        Returns:
            Dictionary containing compliance summary and detailed logs.
        """
        if structures_gdf.empty:
            # Return empty summary structure
            self._save_empty_geojson(output_flags_path)
            return {
                "total_violations": 0,
                "total_encroachment_area_m2": 0.0,
                "violations": []
            }

        # Ensure source CRS is WGS84
        if structures_gdf.crs is None:
            structures_gdf.set_crs("EPSG:4326", inplace=True)
        elif structures_gdf.crs != "EPSG:4326":
            structures_gdf = structures_gdf.to_crs("EPSG:4326")

        # Reproject both datasets to metric UTM system for accurate measurements
        structures_m = structures_gdf.to_crs(target_utm_crs)
        row_m = self.sanctioned_row_gdf.to_crs(target_utm_crs)

        structures_m.geometry = structures_m.geometry.apply(make_valid)
        row_m.geometry = row_m.geometry.apply(make_valid)

        # Build union of RoW polygons
        row_union = row_m.geometry.unary_union
        row_boundary = row_union.boundary

        encroachments = []
        violations_metadata = []
        iso_timestamp = datetime.datetime.now().isoformat()

        # Iterate through detected structures to isolate overlaps
        for idx, row_struct in structures_m.iterrows():
            struct_geom = row_struct.geometry
            if struct_geom is None or struct_geom.is_empty:
                continue

            # Overlay intersection gives the exact encroachment geometry
            intersection = struct_geom.intersection(row_union)

            if not intersection.is_empty and intersection.area > 0.05:  # Tolerance threshold (5cm2)
                area_m2 = intersection.area
                
                # Determine Severity
                if area_m2 > 50.0:
                    severity = "Critical"
                elif area_m2 >= 15.0:
                    severity = "Medium"
                else:
                    severity = "Low"

                # Calculate max perpendicular intrusion depth
                # Find the maximum distance from any vertex of the intersection to the boundary of the RoW
                max_depth = 0.0
                
                # Extrude coordinate vertices
                vertices = []
                if isinstance(intersection, Polygon):
                    vertices = list(intersection.exterior.coords)
                elif isinstance(intersection, MultiPolygon):
                    for poly in intersection.geoms:
                        vertices.extend(list(poly.exterior.coords))
                else:
                    # In case of line/point intersection noise, default to centroid distance
                    max_depth = row_boundary.distance(intersection.centroid)
                    
                if vertices:
                    for coord in vertices:
                        pt = Point(coord)
                        # Ensure vertex is inside RoW to count as intrusion depth
                        if row_union.contains(pt) or row_union.touches(pt):
                            dist = row_boundary.distance(pt)
                            if dist > max_depth:
                                max_depth = dist
                
                if max_depth == 0.0:
                    max_depth = row_boundary.distance(intersection.centroid)

                # Calculate WGS84 centroid
                centroid_m = intersection.centroid
                centroid_wgs = gpd.GeoSeries([centroid_m], crs=target_utm_crs).to_crs("EPSG:4326").iloc[0]
                centroid_lon = centroid_wgs.x
                centroid_lat = centroid_wgs.y

                # Confidence formulation based on footprint match (mock scale)
                confidence = round(0.85 + (0.14 * (1.0 / (1.0 + 0.01 * area_m2))), 2)
                enc_id = f"ENC_{len(violations_metadata) + 1:03d}"
                struct_id = row_struct.get("id", f"STRUCT_{idx+1}")

                violation_info = {
                    "encroachment_id": enc_id,
                    "structure_id": struct_id,
                    "area_m2": round(area_m2, 2),
                    "max_intrusion_depth_m": round(max_depth, 2),
                    "severity": severity,
                    "confidence": confidence,
                    "centroid_lat": round(centroid_lat, 6),
                    "centroid_lon": round(centroid_lon, 6),
                    "timestamp": iso_timestamp
                }
                
                violations_metadata.append(violation_info)

                # Save encroachment geometry as part of spatial export
                encroachments.append({
                    "geometry": intersection,
                    "properties": violation_info
                })

        # Save to WGS84 GeoJSON if encroachments are present
        if encroachments:
            gdf_encroachments = gpd.GeoDataFrame.from_features(encroachments, crs=target_utm_crs)
            gdf_wgs84 = gdf_encroachments.to_crs("EPSG:4326")
            
            # Clean up properties to strings for safe saving
            for col in gdf_wgs84.columns:
                if col != 'geometry':
                    gdf_wgs84[col] = gdf_wgs84[col].astype(str)
                    
            os.makedirs(os.path.dirname(output_flags_path), exist_ok=True)
            gdf_wgs84.to_file(output_flags_path, driver="GeoJSON")
        else:
            self._save_empty_geojson(output_flags_path)

        total_area = sum(v["area_m2"] for v in violations_metadata)

        return {
            "total_violations": len(violations_metadata),
            "total_encroachment_area_m2": round(total_area, 2),
            "violations": violations_metadata
        }

    def _save_empty_geojson(self, output_path: str):
        """Creates an empty georeferenced feature collection file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        empty_gdf.to_file(output_path, driver="GeoJSON")
