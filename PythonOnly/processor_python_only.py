"""
Python-only LAS file processor using laspy, scipy, and numpy.
Eliminates dependency on external lasinfo executable.
"""

import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import threading
from system_utils import (calculate_safe_decimation, get_available_ram_gb, 
                         validate_file_size, estimate_total_ram_needed,
                         calculate_optimal_threads)

try:
    import laspy
    HAS_LASPY = True
except ImportError:
    HAS_LASPY = False

try:
    from scipy.spatial import ConvexHull
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class LASFileInfo:
    """Data class for storing parsed LAS file information."""
    filename: str
    filepath: Path
    point_count: int = 0
    point_density: float = 0.0
    acreage_detailed: float = 0.0  # Convex hull acreage (if available)
    min_x: float = 0.0
    max_x: float = 0.0
    min_y: float = 0.0
    max_y: float = 0.0
    min_z: float = 0.0
    max_z: float = 0.0
    scale_x: float = 0.0
    scale_y: float = 0.0
    scale_z: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0
    crs_info: str = ""
    crs_units: str = "unknown"  # "meters", "feet", "us_survey_feet", or "unknown"
    point_format: str = ""
    raw_output: str = ""  # Will contain Python-generated summary instead of lasinfo output
    file_size_mb: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None


class PythonLASProcessor:
    """Handles LAS file processing using only Python libraries (laspy, scipy, numpy)."""
    
    def __init__(self, max_workers: int = 4, use_detailed_acreage: bool = False, 
                 low_ram_mode: bool = False):
        """
        Initialize the processor.
        
        Args:
            max_workers: Maximum number of parallel threads for file processing
            use_detailed_acreage: If True, calculate convex hull acreage (RAM intensive)
            low_ram_mode: If True, force maximum decimation for all files
        """
        self.max_workers = max_workers
        self.use_detailed_acreage = use_detailed_acreage and HAS_LASPY and HAS_SCIPY
        self.low_ram_mode = low_ram_mode
        self.cancel_event = threading.Event()  # For cancelling ongoing processing
        
        # Debug logging
        import logging
        logger = logging.getLogger("LASAnalysis")
        available_ram = get_available_ram_gb()
        logger.info(f"System RAM: {available_ram:.1f} GB available")
        logger.info(f"PythonLASProcessor initialized: use_detailed_acreage={use_detailed_acreage}, "
                   f"HAS_LASPY={HAS_LASPY}, HAS_SCIPY={HAS_SCIPY}, "
                   f"effective_detailed_acreage={self.use_detailed_acreage}, "
                   f"low_ram_mode={low_ram_mode}, "
                   f"max_workers={max_workers}")
    
    def process_files(self, file_paths: List[Path], progress_callback: Optional[Callable] = None) -> List[LASFileInfo]:
        """
        Process multiple LAS files in parallel using Python libraries only.
        
        Args:
            file_paths: List of LAS file paths to process
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of LASFileInfo objects with processing results
        """
        if not HAS_LASPY:
            return [LASFileInfo(
                filename=path.name,
                filepath=path,
                error="laspy library not available - cannot process LAS files"
            ) for path in file_paths]
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files for processing
            future_to_path = {
                executor.submit(self._process_single_file, path, progress_callback): path
                for path in file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                if self.cancel_event.is_set():
                    # Cancel remaining tasks
                    for f in future_to_path:
                        f.cancel()
                    break
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    path = future_to_path[future]
                    results.append(LASFileInfo(
                        filename=path.name,
                        filepath=path,
                        error=f"Processing failed: {str(e)}"
                    ))
        
        return results
    
    def _process_single_file(self, filepath: Path, progress_callback: Optional[Callable] = None) -> LASFileInfo:
        """
        Process a single LAS file using laspy.
        
        Args:
            filepath: Path to LAS file
            progress_callback: Optional callback for progress updates
            
        Returns:
            LASFileInfo object with file information
        """
        start_time = datetime.now()
        file_info = LASFileInfo(
            filename=filepath.name,
            filepath=filepath,
            file_size_mb=filepath.stat().st_size / (1024 * 1024)
        )
        
        try:
            # Open LAS file with laspy
            with laspy.open(filepath) as las_file:
                # Extract header information
                header = las_file.header
                
                # Basic file information
                file_info.point_count = header.point_count
                file_info.point_format = f"Format {header.point_format.id}"
                
                # Scale factors and offsets
                file_info.scale_x = header.scale[0]
                file_info.scale_y = header.scale[1] 
                file_info.scale_z = header.scale[2]
                file_info.offset_x = header.offset[0]
                file_info.offset_y = header.offset[1]
                file_info.offset_z = header.offset[2]
                
                # Bounds
                file_info.min_x = header.min[0]
                file_info.max_x = header.max[0]
                file_info.min_y = header.min[1]
                file_info.max_y = header.max[1]
                file_info.min_z = header.min[2]
                file_info.max_z = header.max[2]
                
                # Extract CRS information from Variable Length Records (VLRs)
                file_info.crs_info, file_info.crs_units = self._extract_crs_info(header.vlrs)
                
                # Calculate point density
                if file_info.min_x != file_info.max_x and file_info.min_y != file_info.max_y and file_info.point_count > 0:
                    file_info.point_density = self._calculate_point_density(file_info)
                
                # Generate Python-based summary (replaces lasinfo output)
                file_info.raw_output = self._generate_python_summary(file_info, header)
                
                # Calculate convex hull acreage if requested
                if self.use_detailed_acreage and HAS_SCIPY and HAS_NUMPY:
                    self._calculate_convex_hull_acreage(filepath, file_info, progress_callback)
                
        except Exception as e:
            file_info.error = f"Error reading LAS file: {str(e)}"
        
        # Calculate processing time
        file_info.processing_time = (datetime.now() - start_time).total_seconds()
        
        return file_info
    
    def _extract_crs_info(self, vlrs) -> tuple[str, str]:
        """
        Extract coordinate reference system information from VLRs.
        
        Args:
            vlrs: Variable Length Records from LAS header
            
        Returns:
            Tuple of (crs_info, crs_units)
        """
        crs_info = ""
        crs_units = "unknown"
        
        try:
            for vlr in vlrs:
                # Look for GeoTIFF VLRs that contain CRS information
                if hasattr(vlr, 'string') and vlr.string:
                    vlr_string = vlr.string.decode('utf-8', errors='ignore')
                    
                    # Extract coordinate system name
                    if 'GTCitationGeoKey' in vlr_string:
                        match = re.search(r'GTCitationGeoKey:\s*([^|]+)', vlr_string)
                        if match:
                            crs_info = match.group(1).strip()
                    
                    # Detect units
                    if 'US survey foot' in vlr_string or 'Linear_Foot_US_Survey' in vlr_string:
                        crs_units = "us_survey_feet"
                    elif 'linear_foot' in vlr_string.lower() or 'ftus' in vlr_string.lower():
                        crs_units = "feet"
                    elif 'meter' in vlr_string.lower() and ('linear_meter' in vlr_string.lower() or 'unit[' in vlr_string.lower()):
                        crs_units = "meters"
                        
        except Exception as e:
            # If CRS extraction fails, continue with defaults
            pass
        
        return crs_info, crs_units
    
    def _calculate_point_density(self, file_info: LASFileInfo) -> float:
        """
        Calculate point density in points per square meter.
        
        Args:
            file_info: LASFileInfo object with bounds and point count
            
        Returns:
            Point density in pts/m²
        """
        # Calculate area in the units of the file
        area = abs(file_info.max_x - file_info.min_x) * abs(file_info.max_y - file_info.min_y)
        
        # Convert to square meters if coordinates are in feet
        if file_info.crs_units == "us_survey_feet":
            # US Survey Foot = 0.3048006096 meters
            us_survey_ft_to_meters = 0.3048006096
            area_sq_meters = area * (us_survey_ft_to_meters ** 2)
        elif file_info.crs_units == "feet":
            # International Foot = 0.3048 meters
            feet_to_meters = 0.3048
            area_sq_meters = area * (feet_to_meters ** 2)
        else:
            # Assume meters
            area_sq_meters = area
        
        # Calculate density
        if area_sq_meters > 0:
            return file_info.point_count / area_sq_meters
        
        return 0.0
    
    def _generate_python_summary(self, file_info: LASFileInfo, header) -> str:
        """
        Generate a Python-based summary to replace lasinfo output.
        
        Args:
            file_info: LASFileInfo object with file information
            header: LAS file header object
            
        Returns:
            Formatted summary string
        """
        summary_lines = [
            f"Python LAS Analysis Report for '{file_info.filename}'",
            "=" * 60,
            "",
            "LAS Header Information:",
            f"  File signature: {header.file_signature}",
            f"  Version: {header.version_major}.{header.version_minor}",
            f"  System identifier: {header.system_identifier}",
            f"  Generating software: {header.generating_software}",
            f"  File creation day/year: {header.file_creation_day}/{header.file_creation_year}",
            f"  Header size: {header.header_size}",
            f"  Point data format: {header.point_format.id}",
            f"  Point data record length: {header.point_data_record_length}",
            f"  Number of point records: {header.point_count:,}",
            "",
            "Scale factors and offsets:",
            f"  Scale factor x y z: {header.scale[0]:.6f} {header.scale[1]:.6f} {header.scale[2]:.6f}",
            f"  Offset x y z: {header.offset[0]:.6f} {header.offset[1]:.6f} {header.offset[2]:.6f}",
            "",
            "Bounds:",
            f"  Min x y z: {header.min[0]:.6f} {header.min[1]:.6f} {header.min[2]:.6f}",
            f"  Max x y z: {header.max[0]:.6f} {header.max[1]:.6f} {header.max[2]:.6f}",
            "",
            "Calculated metrics:",
            f"  Point density: {file_info.point_density:.2f} pts/m²",
            f"  File size: {file_info.file_size_mb:.2f} MB",
            f"  Processing time: {file_info.processing_time:.2f} sec",
        ]
        
        if file_info.crs_info:
            summary_lines.extend([
                "",
                "Coordinate Reference System:",
                f"  System: {file_info.crs_info}",
                f"  Units: {file_info.crs_units}",
            ])
        
        if file_info.acreage_detailed > 0:
            summary_lines.extend([
                "",
                "Convex Hull Analysis:",
                f"  Acreage (actual footprint): {file_info.acreage_detailed:.2f} acres",
            ])
        
        return "\n".join(summary_lines)
    
    def _calculate_convex_hull_acreage(self, filepath: Path, file_info: LASFileInfo, 
                                     progress_callback: Optional[Callable] = None) -> None:
        """
        Calculate convex hull acreage using scipy and numpy.
        
        Args:
            filepath: Path to LAS file
            file_info: LASFileInfo object to update
            progress_callback: Optional callback for progress updates
        """
        if not HAS_LASPY or not HAS_SCIPY or not HAS_NUMPY:
            return
        
        try:
            # Read the LAS file and extract X, Y coordinates
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            
            if progress_callback:
                progress_callback("sub_progress", "dummy", f"Reading {filepath.name} ({file_size_mb:.0f}MB) for convex hull calculation...")
            
            with laspy.open(filepath) as las_file:
                # Read all points
                las_data = las_file.read()
                point_count = len(las_data)
                
                if point_count == 0:
                    return
                
                if progress_callback:
                    progress_callback("sub_progress", "dummy", f"Extracting {point_count:,} coordinates...")
                
                # Extract X and Y coordinates only
                points_xy = numpy.column_stack((las_data.x, las_data.y))
                
                if progress_callback:
                    progress_callback("sub_progress", "dummy", "Computing convex hull...")
                
                # Compute convex hull
                hull = ConvexHull(points_xy)
                hull_points = points_xy[hull.vertices]
                
                if progress_callback:
                    progress_callback("sub_progress", "dummy", "Calculating area...")
                
                # Calculate area using shoelace formula
                area = self._polygon_area(hull_points)
                
                # Convert to acres based on CRS units
                if area > 0:
                    if file_info.crs_units == "us_survey_feet":
                        # Area is in sq feet, convert to acres
                        acres_per_sq_ft = 1.0 / 43560.0
                        file_info.acreage_detailed = area * acres_per_sq_ft
                    elif file_info.crs_units == "feet":
                        # Area is in sq feet, convert to acres
                        acres_per_sq_ft = 1.0 / 43560.0
                        file_info.acreage_detailed = area * acres_per_sq_ft
                    else:
                        # Assume meters, convert to acres
                        sq_meters_per_acre = 4046.8564224
                        file_info.acreage_detailed = area / sq_meters_per_acre
                    
                    # Update point density based on convex hull area
                    if file_info.crs_units == "us_survey_feet":
                        us_survey_ft_to_meters = 0.3048006096
                        area_sq_meters = area * (us_survey_ft_to_meters ** 2)
                    elif file_info.crs_units == "feet":
                        feet_to_meters = 0.3048
                        area_sq_meters = area * (feet_to_meters ** 2)
                    else:
                        area_sq_meters = area
                    
                    if area_sq_meters > 0:
                        file_info.point_density = file_info.point_count / area_sq_meters
                
        except Exception as e:
            # If convex hull calculation fails, continue without it
            pass
    
    def _polygon_area(self, vertices: List[List[float]]) -> float:
        """
        Calculate area of polygon using shoelace formula.
        
        Args:
            vertices: List of [x, y] coordinates in order
            
        Returns:
            Area of polygon
        """
        if len(vertices) < 3:
            return 0.0
        
        area = 0.0
        n = len(vertices)
        
        for i in range(n):
            j = (i + 1) % n
            x1, y1 = vertices[i]
            x2, y2 = vertices[j]
            area += x1 * y2 - x2 * y1
        
        return abs(area) / 2.0
    
    def cancel_processing(self):
        """Cancel ongoing processing."""
        self.cancel_event.set()
