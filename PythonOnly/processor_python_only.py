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
    
    # Return point counts
    returns_1: int = 0
    returns_2: int = 0
    returns_3: int = 0
    returns_4: int = 0
    returns_5: int = 0
    
    # Classification point counts
    classification_unclassified: int = 0
    classification_ground: int = 0
    classification_low_vegetation: int = 0
    classification_medium_vegetation: int = 0
    classification_high_vegetation: int = 0
    classification_building: int = 0
    classification_water: int = 0
    classification_noise: int = 0
    classification_key_point: int = 0
    classification_reserved: int = 0


class PythonLASProcessor:
    """Handles LAS file processing using only Python libraries (laspy, scipy, numpy)."""
    
    def __init__(self, max_workers: int = 4, use_detailed_acreage: bool = False, 
                 low_ram_mode: bool = False, extract_classifications: bool = True):
        """
        Initialize the processor.
        
        Args:
            max_workers: Maximum number of parallel threads for file processing
            use_detailed_acreage: If True, calculate convex hull acreage (RAM intensive)
            low_ram_mode: If True, force maximum decimation for all files
            extract_classifications: If True, extract return/classification/scan angle data (adds ~10-15% time)
        """
        self.max_workers = max_workers
        self.use_detailed_acreage = use_detailed_acreage and HAS_LASPY and HAS_SCIPY
        self.low_ram_mode = low_ram_mode
        self.extract_classifications = extract_classifications
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
    
    def process_files(self, file_paths: List[Path], progress_callback: Optional[Callable] = None) -> tuple[List[LASFileInfo], Dict[str, any]]:
        """
        Process multiple LAS files in parallel using Python libraries only.
        
        Args:
            file_paths: List of LAS file paths to process
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (list of LASFileInfo objects, aggregate statistics dict)
        """
        if not HAS_LASPY:
            error_results = [LASFileInfo(
                filename=path.name,
                filepath=path,
                error="laspy library not available - cannot process LAS files"
            ) for path in file_paths]
            aggregate = self._calculate_aggregates(error_results)
            return error_results, aggregate
        
        import logging
        logger = logging.getLogger("LASAnalysis")
        
        results = []
        logger.info(f"Starting Python-based file processing with {self.max_workers} threads")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files for processing
            future_to_path = {
                executor.submit(self._process_single_file, path, progress_callback): path
                for path in file_paths
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_path):
                if self.cancel_event.is_set():
                    # Cancel remaining tasks
                    for f in future_to_path:
                        f.cancel()
                    break
                
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    # Call progress callback for main progress updates
                    if progress_callback:
                        progress_callback(completed, len(file_paths), result.filename)
                        
                except Exception as e:
                    path = future_to_path[future]
                    error_result = LASFileInfo(
                        filename=path.name,
                        filepath=path,
                        error=f"Processing failed: {str(e)}"
                    )
                    results.append(error_result)
                    completed += 1
                    
                    # Call progress callback even for failed files
                    if progress_callback:
                        progress_callback(completed, len(file_paths), path.name)
        
        # Sort results by filename
        results.sort(key=lambda x: x.filename)
        
        # Calculate aggregate statistics
        aggregate = self._calculate_aggregates(results)
        
        return results, aggregate
    
    def _calculate_aggregates(self, results: List[LASFileInfo]) -> Dict[str, any]:
        """
        Calculate aggregate statistics from all processed files.
        
        Args:
            results: List of LASFileInfo objects
            
        Returns:
            Dictionary with aggregate statistics
        """
        valid_results = [r for r in results if r.error is None]
        
        if not valid_results:
            return {
                'total_files': len(results),
                'valid_files': 0,
                'failed_files': len(results),
                'total_points': 0,
                'avg_point_density': 0.0,
                'total_file_size_mb': 0.0,
                'overall_min_x': 0.0,
                'overall_max_x': 0.0,
                'overall_min_y': 0.0,
                'overall_max_y': 0.0,
                'overall_min_z': 0.0,
                'overall_max_z': 0.0,
            }
        
        total_points = sum(r.point_count for r in valid_results)
        avg_density = (sum(r.point_density for r in valid_results) / len(valid_results)
                      if valid_results else 0.0)
        total_size = sum(r.file_size_mb for r in results)
        
        try:
            overall_min_x = min(r.min_x for r in valid_results)
            overall_max_x = max(r.max_x for r in valid_results)
            overall_min_y = min(r.min_y for r in valid_results)
            overall_max_y = max(r.max_y for r in valid_results)
            overall_min_z = min(r.min_z for r in valid_results)
            overall_max_z = max(r.max_z for r in valid_results)
        except (ValueError, TypeError) as e:
            # Handle case where valid_results is empty or contains invalid data
            overall_min_x = overall_max_x = 0.0
            overall_min_y = overall_max_y = 0.0
            overall_min_z = overall_max_z = 0.0
        
        return {
            'total_files': len(results),
            'valid_files': len(valid_results),
            'failed_files': len(results) - len(valid_results),
            'total_points': total_points,
            'avg_point_density': avg_density,
            'total_file_size_mb': total_size,
            'overall_min_x': overall_min_x,
            'overall_max_x': overall_max_x,
            'overall_min_y': overall_min_y,
            'overall_max_y': overall_max_y,
            'overall_min_z': overall_min_z,
            'overall_max_z': overall_max_z,
            # Return counts aggregates
            'total_returns_1': sum(r.returns_1 for r in valid_results),
            'total_returns_2': sum(r.returns_2 for r in valid_results),
            'total_returns_3': sum(r.returns_3 for r in valid_results),
            'total_returns_4': sum(r.returns_4 for r in valid_results),
            'total_returns_5': sum(r.returns_5 for r in valid_results),
            # Classification counts aggregates
            'total_classification_unclassified': sum(r.classification_unclassified for r in valid_results),
            'total_classification_ground': sum(r.classification_ground for r in valid_results),
            'total_classification_low_vegetation': sum(r.classification_low_vegetation for r in valid_results),
            'total_classification_medium_vegetation': sum(r.classification_medium_vegetation for r in valid_results),
            'total_classification_high_vegetation': sum(r.classification_high_vegetation for r in valid_results),
            'total_classification_building': sum(r.classification_building for r in valid_results),
            'total_classification_water': sum(r.classification_water for r in valid_results),
            'total_classification_noise': sum(r.classification_noise for r in valid_results),
            'total_classification_key_point': sum(r.classification_key_point for r in valid_results),
            'total_classification_reserved': sum(r.classification_reserved for r in valid_results),
        }
    
    def _process_single_file(self, filepath: Path, progress_callback: Optional[Callable] = None) -> LASFileInfo:
        """
        Process a single LAS file using laspy.
        
        Args:
            filepath: Path to LAS file
            progress_callback: Optional callback for progress updates
            
        Returns:
            LASFileInfo object with file information
        """
        import logging
        logger = logging.getLogger("LASAnalysis")
        
        start_time = datetime.now()
        file_info = LASFileInfo(
            filename=filepath.name,
            filepath=filepath,
            file_size_mb=filepath.stat().st_size / (1024 * 1024)
        )
        
        logger.info(f"Processing {filepath.name} ({file_info.file_size_mb:.1f} MB) using Python libraries")
        
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
                file_info.crs_info, file_info.crs_units = self._extract_crs_info(header.vlrs, header)
                logger.debug(f"CRS info: '{file_info.crs_info}', Units: '{file_info.crs_units}'")
                
                # Read point data to extract classifications and returns
                try:
                    if self.extract_classifications:
                        las_data = las_file.read()
                        
                        # Extract return counts using numpy bincount (much faster than loops)
                        if hasattr(las_data, 'return_num'):
                            try:
                                # Convert SubFieldView to numpy array
                                return_num_array = numpy.asarray(las_data.return_num, dtype=numpy.int32)
                                return_counts = numpy.bincount(return_num_array)
                                file_info.returns_1 = int(return_counts[1]) if len(return_counts) > 1 else 0
                                file_info.returns_2 = int(return_counts[2]) if len(return_counts) > 2 else 0
                                file_info.returns_3 = int(return_counts[3]) if len(return_counts) > 3 else 0
                                file_info.returns_4 = int(return_counts[4]) if len(return_counts) > 4 else 0
                                file_info.returns_5 = int(return_counts[5]) if len(return_counts) > 5 else 0
                                logger.debug(f"Return counts: R1={file_info.returns_1}, R2={file_info.returns_2}, R3={file_info.returns_3}, R4={file_info.returns_4}, R5={file_info.returns_5}")
                            except Exception as e:
                                logger.debug(f"Error counting returns: {str(e)}")
                        
                        # Extract classification counts using numpy bincount (much faster than loops)
                        if hasattr(las_data, 'classification'):
                            try:
                                # Convert SubFieldView to numpy array
                                classification_array = numpy.asarray(las_data.classification, dtype=numpy.int32)
                                classification_counts = numpy.bincount(classification_array)
                                # LAS classification codes
                                file_info.classification_unclassified = int(classification_counts[0]) if len(classification_counts) > 0 else 0
                                file_info.classification_reserved = int(classification_counts[1]) if len(classification_counts) > 1 else 0
                                file_info.classification_ground = int(classification_counts[2]) if len(classification_counts) > 2 else 0
                                file_info.classification_low_vegetation = int(classification_counts[3]) if len(classification_counts) > 3 else 0
                                file_info.classification_medium_vegetation = int(classification_counts[4]) if len(classification_counts) > 4 else 0
                                file_info.classification_high_vegetation = int(classification_counts[5]) if len(classification_counts) > 5 else 0
                                file_info.classification_building = int(classification_counts[6]) if len(classification_counts) > 6 else 0
                                file_info.classification_noise = int(classification_counts[7]) if len(classification_counts) > 7 else 0
                                file_info.classification_key_point = int(classification_counts[8]) if len(classification_counts) > 8 else 0
                                file_info.classification_water = int(classification_counts[9]) if len(classification_counts) > 9 else 0
                                logger.debug(f"Classification counts: Ground={file_info.classification_ground}, Vegetation={file_info.classification_low_vegetation + file_info.classification_medium_vegetation + file_info.classification_high_vegetation}")
                            except Exception as e:
                                logger.debug(f"Error counting classifications: {str(e)}")
                    else:
                        # Only read if needed for convex hull
                        if self.use_detailed_acreage:
                            las_data = las_file.read()
                        else:
                            las_data = None
                        logger.debug(f"Skipping classification extraction (extract_classifications={self.extract_classifications})")
                    
                except Exception as e:
                    logger.warning(f"Error extracting point data: {str(e)}")
                    las_data = None
                
                # Calculate point density
                if file_info.min_x != file_info.max_x and file_info.min_y != file_info.max_y and file_info.point_count > 0:
                    file_info.point_density = self._calculate_point_density(file_info)
                    logger.debug(f"Point density calculated: {file_info.point_density:.2f} pts/m²")
                
                # Generate Python-based summary (replaces lasinfo output)
                file_info.raw_output = self._generate_python_summary(file_info, header)
                
                # Calculate convex hull acreage if requested
                if self.use_detailed_acreage and HAS_SCIPY and HAS_NUMPY:
                    logger.info(f"Calculating convex hull acreage for {filepath.name}")
                    self._calculate_convex_hull_acreage(filepath, file_info, progress_callback, las_data=las_data)
                    logger.info(f"Convex hull result: acreage_detailed={file_info.acreage_detailed:.2f}")
                else:
                    logger.debug(f"Skipping convex hull calculation (use_detailed_acreage={self.use_detailed_acreage}, HAS_SCIPY={HAS_SCIPY}, HAS_NUMPY={HAS_NUMPY})")
                
        except Exception as e:
            file_info.error = f"Error reading LAS file: {str(e)}"
        
        # Calculate processing time
        file_info.processing_time = (datetime.now() - start_time).total_seconds()
        
        return file_info
    
    def _extract_crs_info(self, vlrs, header) -> tuple[str, str]:
        """
        Extract coordinate reference system information from VLRs and header.
        
        Args:
            vlrs: Variable Length Records from LAS header
            header: LAS file header object
            
        Returns:
            Tuple of (crs_info, crs_units)
        """
        crs_info = ""
        crs_units = "unknown"
        
        try:
            for vlr in vlrs:
                # Look for GeoTIFF VLRs that contain CRS information
                if hasattr(vlr, 'string') and vlr.string:
                    try:
                        # Handle different string formats
                        if isinstance(vlr.string, bytes):
                            vlr_string = vlr.string.decode('utf-8', errors='ignore')
                        else:
                            vlr_string = str(vlr.string)
                        
                        # Extract coordinate system name
                        if 'GTCitationGeoKey' in vlr_string:
                            match = re.search(r'GTCitationGeoKey:\s*([^|]+)', vlr_string)
                            if match:
                                crs_info = match.group(1).strip()
                        # Check for WKT VLR which contains the full CRS name
                        elif 'COMPD_CS' in vlr_string and 'NAD83' in vlr_string:
                            # Extract the full CRS name from WKT VLR
                            match = re.search(r'COMPD_CS\["([^"]*NAD83[^"]*)"', vlr_string)
                            if match:
                                crs_info = match.group(1).strip()
                        # Also check for GeoAsciiParamsVlr which contains the full CRS name
                        elif 'NAD83' in vlr_string and 'Maine' in vlr_string:
                            # Extract the full CRS name from GeoAsciiParamsVlr
                            match = re.search(r"'([^']*NAD83[^']*Maine[^']*)'", vlr_string)
                            if match:
                                crs_info = match.group(1).strip()
                        
                        # Detect units
                        if 'US survey foot' in vlr_string or 'Linear_Foot_US_Survey' in vlr_string:
                            crs_units = "us_survey_feet"
                        elif 'linear_foot' in vlr_string.lower() or 'ftus' in vlr_string.lower():
                            crs_units = "feet"
                        elif 'meter' in vlr_string.lower() and ('linear_meter' in vlr_string.lower() or 'unit[' in vlr_string.lower()):
                            crs_units = "meters"
                    except Exception:
                        # Skip this VLR if there's an error
                        continue
                        
        except Exception as e:
            # If CRS extraction fails, continue with defaults
            pass
        
        # Fallback: Detect units and coordinate system based on coordinate values
        if crs_units == "unknown":
            crs_units = self._detect_units_from_coordinates(header)
        
        # If we still don't have CRS info, try to determine it from coordinates
        if not crs_info:
            crs_info = self._detect_crs_from_coordinates(header)
        
        return crs_info, crs_units
    
    def _detect_units_from_coordinates(self, header) -> str:
        """
        Detect coordinate units based on coordinate values.
        
        Args:
            header: LAS file header object
            
        Returns:
            Detected unit type
        """
        # Get coordinate bounds
        min_x, min_y = header.min[0], header.min[1]
        max_x, max_y = header.max[0], header.max[1]
        
        # Calculate coordinate ranges
        x_range = abs(max_x - min_x)
        y_range = abs(max_y - min_y)
        
        # US State Plane coordinates in feet typically have values in the millions
        # (e.g., 2,000,000 to 3,000,000 feet)
        if (min_x > 1000000 and max_x > 1000000 and 
            min_y > 100000 and max_y > 100000 and
            x_range > 1000 and y_range > 1000):
            return "us_survey_feet"
        
        # UTM coordinates in meters typically have values in the hundreds of thousands
        # (e.g., 200,000 to 800,000 meters)
        elif (min_x > 100000 and max_x > 100000 and 
              min_y > 100000 and max_y > 100000 and
              x_range > 1000 and y_range > 1000):
            return "meters"
        
        # Default to meters if we can't determine
        return "meters"
    
    def _detect_crs_from_coordinates(self, header) -> str:
        """
        Detect coordinate reference system based on coordinate values.
        
        Args:
            header: LAS file header object
            
        Returns:
            Detected CRS name or empty string
        """
        # Get coordinate bounds
        min_x, min_y = header.min[0], header.min[1]
        max_x, max_y = header.max[0], header.max[1]
        
        # US State Plane coordinates in feet typically have values in the millions
        # (e.g., 2,000,000 to 3,000,000 feet)
        if (min_x > 1000000 and max_x > 1000000 and 
            min_y > 100000 and max_y > 100000):
            
            # Try to determine which state plane zone based on coordinate ranges
            # This is a simplified approach - in practice, you'd need more sophisticated logic
            
            # Maine State Plane coordinates (example)
            if (min_x > 2900000 and max_x < 3000000 and 
                min_y > 300000 and max_y < 400000):
                return "NAD83(2011) / Maine West (ftUS)"
            
            # Generic US State Plane
            return "NAD83 / US State Plane (ftUS)"
        
        # UTM coordinates in meters typically have values in the hundreds of thousands
        elif (min_x > 100000 and max_x > 100000 and 
              min_y > 100000 and max_y > 100000):
            return "WGS84 / UTM Zone (m)"
        
        # Default
        return ""
    
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
        ]
        
        # Add header information with safe attribute access
        try:
            summary_lines.append(f"  File signature: {header.file_signature}")
        except AttributeError:
            summary_lines.append("  File signature: Not available")
        
        try:
            summary_lines.extend([
                f"  Version: {header.version_major}.{header.version_minor}",
                f"  System identifier: {header.system_identifier}",
                f"  Generating software: {header.generating_software}",
                f"  File creation day/year: {header.file_creation_day}/{header.file_creation_year}",
                f"  Header size: {header.header_size}",
                f"  Point data format: {header.point_format.id}",
                f"  Point data record length: {header.point_data_record_length}",
                f"  Number of point records: {header.point_count:,}",
            ])
        except AttributeError as e:
            error_msg = f"  Header information: Some attributes not available ({str(e)})"
            summary_lines.append(error_msg)
        
        summary_lines.extend([
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
        ])
        
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
                                     progress_callback: Optional[Callable] = None, las_data=None) -> None:
        """
        Calculate convex hull acreage using scipy and numpy.
        
        Args:
            filepath: Path to LAS file
            file_info: LASFileInfo object to update
            progress_callback: Optional callback for progress updates
        """
        if not HAS_LASPY or not HAS_SCIPY or not HAS_NUMPY:
            return
        
        import logging
        logger = logging.getLogger("LASAnalysis")
        
        try:
            # Read the LAS file and extract X, Y coordinates
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"Reading {filepath.name} ({file_size_mb:.0f}MB) for convex hull calculation...")
            
            if progress_callback:
                progress_callback("sub_progress", "dummy", f"Reading {filepath.name} ({file_size_mb:.0f}MB) for convex hull calculation...")
            
            if las_data is None:
                with laspy.open(filepath) as las_file:
                    # Read all points
                    las_data = las_file.read()
                    point_count = len(las_data)
                    logger.debug(f"Loaded {point_count:,} points from LAS file")
            else:
                point_count = len(las_data)
                logger.debug(f"Using provided las_data for convex hull calculation (point_count={point_count:,}")
                
                if point_count == 0:
                    logger.warning(f"No points found in {filepath.name}")
                    return
                
                if progress_callback:
                    progress_callback("sub_progress", "dummy", f"Extracting {point_count:,} coordinates...")
                
                # Extract X and Y coordinates only
                points_xy = numpy.column_stack((las_data.x, las_data.y))
                logger.debug(f"Extracted {len(points_xy):,} X,Y coordinate pairs")
                
                if progress_callback:
                    progress_callback("sub_progress", "dummy", "Computing convex hull...")
                
                # Compute convex hull
                hull = ConvexHull(points_xy)
                hull_points = points_xy[hull.vertices]
                logger.debug(f"Convex hull computed with {len(hull_points)} vertices")
                
                if progress_callback:
                    progress_callback("sub_progress", "dummy", "Calculating area...")
                
                # Calculate area using shoelace formula
                area = self._polygon_area(hull_points)
                logger.debug(f"Convex hull area calculated: {area:.2f} square units")
                
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
                        logger.debug(f"Updated point density based on convex hull: {file_info.point_density:.2f} pts/m²")
                
        except Exception as e:
            # If convex hull calculation fails, continue without it
            logger.error(f"{filepath.name}: Error calculating convex hull: {str(e)}")
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
