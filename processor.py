"""
Processor module for executing lasinfo and parsing output.
"""

import subprocess
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
    raw_output: str = ""
    file_size_mb: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None


class LASProcessor:
    """Handles execution of lasinfo and parsing of results."""
    
    def __init__(self, max_workers: int = 4, use_detailed_acreage: bool = False, 
                 low_ram_mode: bool = False, prefer_64bit: bool = True):
        """
        Initialize the processor.
        
        Args:
            max_workers: Maximum number of parallel threads for file processing
            use_detailed_acreage: If True, calculate convex hull acreage (RAM intensive)
            low_ram_mode: If True, force maximum decimation for all files
            prefer_64bit: If True, try to use 64-bit lasinfo for large files
        """
        self.max_workers = max_workers
        self.use_detailed_acreage = use_detailed_acreage and HAS_LASPY and HAS_SCIPY
        self.low_ram_mode = low_ram_mode
        self.cancel_event = threading.Event()  # For cancelling ongoing processing
        
        # Detect lasinfo command (64-bit if available, fallback to 32-bit)
        self.lasinfo_cmd = self._detect_lasinfo_command(prefer_64bit)
        
        # Debug logging
        import logging
        logger = logging.getLogger("LASAnalysis")
        available_ram = get_available_ram_gb()
        logger.info(f"System RAM: {available_ram:.1f} GB available")
        logger.info(f"LASProcessor initialized: use_detailed_acreage={use_detailed_acreage}, "
                   f"HAS_LASPY={HAS_LASPY}, HAS_SCIPY={HAS_SCIPY}, "
                   f"effective_detailed_acreage={self.use_detailed_acreage}, "
                   f"low_ram_mode={low_ram_mode}, "
                   f"max_workers={max_workers}, "
                   f"lasinfo_cmd={self.lasinfo_cmd}")
    
    def _detect_lasinfo_command(self, prefer_64bit: bool = True) -> str:
        """
        Detect the best available lasinfo command.
        Prefers 64-bit for handling large files, falls back to 32-bit.
        
        Args:
            prefer_64bit: If True, try 64-bit first
            
        Returns:
            Command string to use (e.g., 'lasinfo64' or 'lasinfo')
            
        Raises:
            FileNotFoundError: If neither 64-bit nor 32-bit lasinfo found
        """
        import shutil
        import logging
        
        logger = logging.getLogger("LASAnalysis")
        
        # Try 64-bit first if preferred
        if prefer_64bit:
            # Check for lasinfo64
            if shutil.which('lasinfo64'):
                logger.info("Using 64-bit lasinfo (lasinfo64) - supports files >2GB")
                return 'lasinfo64'
        
        # Fall back to standard lasinfo
        if shutil.which('lasinfo'):
            logger.info("Using 32-bit lasinfo - limited to files <2GB")
            return 'lasinfo'
        
        # Neither found
        raise FileNotFoundError(
            "lasinfo command not found in PATH. Please install LAStools.\n"
            "For large files (>2GB), ensure lasinfo64 is available.\n"
            "Visit: https://rapidlasso.com/lastools/"
        )
    
    def cancel_processing(self) -> None:
        """Signal all ongoing processing to stop immediately."""
        import logging
        logger = logging.getLogger("LASAnalysis")
        logger.warning("Processing cancellation requested - stopping all threads...")
        self.cancel_event.set()
    
    def process_files(
        self,
        las_files: List[Path],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> tuple[List[LASFileInfo], Dict[str, any]]:
        """
        Process multiple LAS files in parallel.
        
        Args:
            las_files: List of LAS file paths
            progress_callback: Optional callback function(completed, total, current_file)
            
        Returns:
            Tuple of (list of LASFileInfo objects, aggregate statistics dict)
        """
        import logging
        logger = logging.getLogger("LASAnalysis")
        
        # Reset cancellation flag at start of processing
        self.cancel_event.clear()
        
        # Validate all file sizes before processing (20GB hard cap)
        logger.info(f"Validating {len(las_files)} LAS files (20GB per-file limit)...")
        oversized_files = []
        for las_file in las_files:
            is_valid, message = validate_file_size(las_file, max_size_gb=20.0)
            if not is_valid:
                logger.error(message)
                oversized_files.append(message)
        
        if oversized_files:
            # All files failed validation
            error_msg = "File size validation failed:\n" + "\n".join(oversized_files)
            logger.error(error_msg)
            results = []
            for las_file in las_files:
                file_info = LASFileInfo(
                    filename=las_file.name,
                    filepath=las_file,
                    error=f"File exceeds 20GB limit"
                )
                results.append(file_info)
            aggregate = self._calculate_aggregates(results)
            return results, aggregate
        

        # Note: Thread count was already optimized in main.py preflight dialog
        # based on concurrent file processing. Use max_workers directly.
        logger.info(f"Starting file processing with {self.max_workers} threads")
        
        available_ram = get_available_ram_gb()
        logger.info(f"Available RAM: {available_ram:.1f}GB")
        
        # Use max_workers directly (already optimized)
        effective_workers = self.max_workers
        results = []
        
        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            future_to_file = {
                executor.submit(self._process_single_file, las_file, progress_callback): las_file
                for las_file in las_files
            }
            
            completed = 0
            for future in as_completed(future_to_file):
                # Check cancellation flag
                if self.cancel_event.is_set():
                    logger.warning("Processing cancelled by user")
                    # Cancel remaining tasks
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                las_file = future_to_file[future]
                try:
                    file_info = future.result()
                    results.append(file_info)
                except Exception as e:
                    file_info = LASFileInfo(
                        filename=las_file.name,
                        filepath=las_file,
                        error=str(e)
                    )
                    results.append(file_info)
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(las_files), las_file.name)
        
        # Sort results by filename
        results.sort(key=lambda x: x.filename)
        
        # Calculate aggregate statistics
        aggregate = self._calculate_aggregates(results)
        
        return results, aggregate
    
    def _process_single_file(self, filepath: Path, progress_callback=None) -> LASFileInfo:
        """
        Process a single LAS file with lasinfo.
        
        Args:
            filepath: Path to the LAS file
            progress_callback: Optional callback for progress updates during convex hull
            
        Returns:
            LASFileInfo object with parsed data
        """
        start_time = datetime.now()
        file_info = LASFileInfo(
            filename=filepath.name,
            filepath=filepath,
            file_size_mb=filepath.stat().st_size / (1024 * 1024)
        )
        
        # Log large files
        import logging
        logger = logging.getLogger("LASAnalysis")
        if file_info.file_size_mb > 1000:
            logger.info(f"Processing large file: {filepath.name} ({file_info.file_size_mb:.1f} MB) "
                       f"using {self.lasinfo_cmd}")
        
        try:
            # Run lasinfo - output might come on either stdout or stderr
            result = subprocess.run(
                [self.lasinfo_cmd, str(filepath)],
                capture_output=True,
                text=False,  # Get bytes first to handle encoding manually
                timeout=300
            )
            
            # Decode with error handling
            if result.stdout:
                output = result.stdout.decode('utf-8', errors='replace')
            elif result.stderr:
                output = result.stderr.decode('utf-8', errors='replace')
            else:
                output = ""
            
            if result.returncode != 0 and not output:
                file_info.error = f"lasinfo failed: {result.stderr.decode('utf-8', errors='replace')}"
                return file_info
            
            file_info.raw_output = output
            
            # Parse the output
            self._parse_lasinfo_output(output, file_info)
            
            # Calculate convex hull acreage if requested
            logger.info(f"CONVEX HULL CHECK: use_detailed_acreage={self.use_detailed_acreage}, "
                       f"has_error={bool(file_info.error)}, file={filepath.name}")
            if self.use_detailed_acreage and not file_info.error:
                logger.info(f"CONVEX HULL TRIGGER: Starting convex hull calculation for {filepath.name}")
                self._calculate_convex_hull_acreage(filepath, file_info, progress_callback)
                logger.info(f"CONVEX HULL RESULT: acreage_detailed={file_info.acreage_detailed:.2f}")
            else:
                logger.info(f"CONVEX HULL SKIPPED: use_detailed_acreage={self.use_detailed_acreage}, "
                           f"has_error={bool(file_info.error)}")
            
        except subprocess.TimeoutExpired:
            file_info.error = "lasinfo timeout (>5 minutes)"
        except FileNotFoundError:
            file_info.error = "lasinfo command not found - ensure it's in PATH"
        except Exception as e:
            file_info.error = str(e)
        
        end_time = datetime.now()
        file_info.processing_time = (end_time - start_time).total_seconds()
        
        return file_info
    
    def _calculate_convex_hull_acreage(self, filepath: Path, file_info: LASFileInfo, progress_callback=None) -> None:
        """
        Calculate acreage using convex hull of actual point cloud data.
        Always uses 100% of points - no decimation.
        
        Args:
            filepath: Path to the LAS file
            file_info: LASFileInfo object to populate with acreage data
            progress_callback: Optional callback for progress updates during long operations
        """
        import logging
        logger = logging.getLogger("LASAnalysis")
        
        logger.debug(f"\n{'='*80}")
        logger.debug(f"CONVEX HULL CALCULATION START: {filepath.name}")
        logger.debug(f"{'='*80}")
        logger.debug(f"  self.use_detailed_acreage = {self.use_detailed_acreage}")
        logger.debug(f"  HAS_LASPY = {HAS_LASPY}")
        logger.debug(f"  HAS_SCIPY = {HAS_SCIPY}")
        logger.debug(f"  HAS_NUMPY = {HAS_NUMPY}")
        logger.debug(f"  file_info.crs_units = {file_info.crs_units}")
        
        if not self.use_detailed_acreage or not HAS_LASPY or not HAS_SCIPY:
            logger.warning(f"❌ CONVEX HULL PREREQUISITES NOT MET for {filepath.name}:")
            logger.warning(f"   use_detailed_acreage={self.use_detailed_acreage}, "
                          f"HAS_LASPY={HAS_LASPY}, HAS_SCIPY={HAS_SCIPY}")
            return
        
        logger.debug(f"✓ Prerequisites met, proceeding with convex hull calculation...")
        
        try:
            # Read the LAS file and extract X, Y coordinates (100% of points)
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"Reading {filepath.name} ({file_size_mb:.0f}MB) for convex hull calculation...")
            
            if progress_callback:
                progress_callback("sub_progress", "dummy", f"Loading LAS file ({file_size_mb:.0f}MB)...")
            
            las_data = laspy.read(filepath)
            point_count = las_data.header.point_count
            logger.debug(f"{filepath.name}: Loaded LAS with {point_count:,} points (100% - no decimation)")
            
            # Check if we have enough points for convex hull (need at least 3)
            if point_count < 3:
                logger.debug(f"{filepath.name}: Too few points ({point_count}), skipping convex hull")
                return
            
            if progress_callback:
                progress_callback("sub_progress", "dummy", f"Extracting {point_count:,} coordinates...")
            
            # Extract X and Y coordinates only (100% of points)
            points_xy = numpy.column_stack((las_data.x, las_data.y))
            logger.debug(f"{filepath.name}: Extracted {len(points_xy):,} XY points for hull")
            
            if len(points_xy) < 3:
                logger.debug(f"{filepath.name}: XY points < 3, skipping convex hull")
                return
            
            if progress_callback:
                progress_callback("sub_progress", "dummy", "Computing convex hull...")
            
            # Calculate convex hull
            try:
                hull = ConvexHull(points_xy)
                hull_vertices_count = len(hull.vertices)
                logger.debug(f"{filepath.name}: Convex hull computed with {hull_vertices_count} vertices")
                
                if progress_callback:
                    progress_callback("sub_progress", "dummy", "Calculating area...")
                
                # Get hull vertices
                hull_points = points_xy[hull.vertices]
                
                # Calculate area using shoelace formula for polygon
                area = self._polygon_area(hull_points)
                logger.debug(f"{filepath.name}: Hull area = {area:,.2f} sq{file_info.crs_units}")
                
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
                    
                    # Calculate point density based on convex hull area (in square meters)
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
                    
                    logger.info(f"✓ {filepath.name}: Convex hull acreage = {file_info.acreage_detailed:.2f} acres, "
                               f"Density = {file_info.point_density:.2f} pts/m²")
                    logger.debug(f"✓ CONVEX HULL SUCCESS: Final values:")
                    logger.debug(f"    acreage_detailed = {file_info.acreage_detailed:.4f}")
                    logger.debug(f"    point_density = {file_info.point_density:.4f}")
                else:
                    logger.warning(f"❌ {filepath.name}: Hull area = 0, skipping convex hull acreage")
            
            except Exception as e:
                # Degenerate hull or other scipy error
                logger.error(f"❌ {filepath.name}: Convex hull computation failed ({str(e)})")
                logger.error(f"   Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
        
        except Exception as e:
            # Any error in laspy reading
            logger.error(f"{filepath.name}: Error reading LAS for convex hull ({str(e)})")
    
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
        
        # Shoelace formula
        area = 0.0
        n = len(vertices)
        for i in range(n):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % n]
            area += x1 * y2 - x2 * y1
        
        return abs(area) / 2.0

    def _parse_lasinfo_output(self, output: str, file_info: LASFileInfo) -> None:
        """
        Parse lasinfo output and extract key metrics.
        
        Args:
            output: Raw lasinfo output
            file_info: LASFileInfo object to populate
        """
        lines = output.split('\n')
        crs_lines = []  # Collect CRS info lines
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Point count - "number of point records:"
            if 'number of point records:' in line_lower:
                parts = line_stripped.split(':')
                if len(parts) > 1:
                    try:
                        file_info.point_count = int(parts[1].strip().replace(',', ''))
                    except ValueError:
                        pass
            
            # Scale factors - "scale factor x y z:"
            if 'scale factor' in line_lower and 'x' in line_lower and 'y' in line_lower and 'z' in line_lower:
                parts = line_stripped.split(':')
                if len(parts) > 1:
                    values = parts[1].strip().split()
                    if len(values) >= 3:
                        try:
                            file_info.scale_x = float(values[0])
                            file_info.scale_y = float(values[1])
                            file_info.scale_z = float(values[2])
                        except ValueError:
                            pass
            
            # Offset - "offset x y z:"
            if 'offset' in line_lower and 'x' in line_lower and 'y' in line_lower and 'z' in line_lower and 'x y z:' in line_lower:
                parts = line_stripped.split(':')
                if len(parts) > 1:
                    values = parts[1].strip().split()
                    if len(values) >= 3:
                        try:
                            file_info.offset_x = float(values[0])
                            file_info.offset_y = float(values[1])
                            file_info.offset_z = float(values[2])
                        except ValueError:
                            pass
            
            # Min/Max bounds - "min x y z:" and "max x y z:"
            if line_lower.startswith('min x y z:'):
                parts = line_stripped.split(':')
                if len(parts) > 1:
                    values = parts[1].strip().split()
                    if len(values) >= 3:
                        try:
                            file_info.min_x = float(values[0])
                            file_info.min_y = float(values[1])
                            file_info.min_z = float(values[2])
                        except ValueError:
                            pass
            
            if line_lower.startswith('max x y z:'):
                parts = line_stripped.split(':')
                if len(parts) > 1:
                    values = parts[1].strip().split()
                    if len(values) >= 3:
                        try:
                            file_info.max_x = float(values[0])
                            file_info.max_y = float(values[1])
                            file_info.max_z = float(values[2])
                        except ValueError:
                            pass
            
            # Point data format - "point data format:"
            if 'point data format:' in line_lower:
                parts = line_stripped.split(':')
                if len(parts) > 1:
                    file_info.point_format = f"Format {parts[1].strip()}"
            
            # CRS/EPSG information - collect full context
            if any(term in line for term in ['EPSG', 'NAD83', 'WGS', 'ProjLinearUnitsGeoKey', 'ProjectedCSTypeGeoKey', 'Linear_Foot', 'US survey foot', 'GTCitationGeoKey']):
                crs_lines.append(line_stripped)
            
            # Detect coordinate system units
            if 'linear_foot' in line_lower or 'us survey foot' in line_lower or 'ftus' in line_lower:
                if 'Linear_Foot_US_Survey' in line or 'US survey foot' in line:
                    file_info.crs_units = "us_survey_feet"
                else:
                    file_info.crs_units = "feet"
            elif 'meter' in line_lower and ('linear_meter' in line_lower or 'unit[' in line_lower):
                file_info.crs_units = "meters"
        
        # Combine CRS info
        if crs_lines:
            file_info.crs_info = ' | '.join(crs_lines)  # Keep all relevant lines for better parsing
        
        # Calculate point density if we have bounds
        # Convert to square meters if needed
        if file_info.min_x != file_info.max_x and file_info.min_y != file_info.max_y and file_info.point_count > 0:
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
            
            if area_sq_meters > 0:
                # Point density will be calculated using convex hull area if available
                pass
    
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
        }
