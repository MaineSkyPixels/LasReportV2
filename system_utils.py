"""
System utilities for RAM detection and resource management.
"""

import psutil
import logging
import os
from pathlib import Path
from typing import List, Tuple


def get_available_ram_gb() -> float:
    """
    Get currently available RAM in GB.
    
    Returns:
        Available RAM in gigabytes
    """
    return psutil.virtual_memory().available / (1024 ** 3)


def get_total_ram_gb() -> float:
    """
    Get total system RAM in GB.
    
    Returns:
        Total RAM in gigabytes
    """
    return psutil.virtual_memory().total / (1024 ** 3)


def calculate_safe_decimation(file_size_mb: float, available_ram_gb: float) -> float:
    """
    Calculate safe decimation factor based on file size and available RAM.
    
    Strategy:
    - Assume loading LAS file uses ~file_size_mb of RAM
    - XY coordinate array uses ~(point_count * 16 bytes)
    - For typical LAS files: ~30 bytes per point
    - So XY array is roughly file_size * 0.5
    - Total RAM needed: file_size * 1.5
    - Keep usage under 50% of available RAM for safety
    
    Args:
        file_size_mb: Size of LAS file in MB
        available_ram_gb: Available RAM in GB
        
    Returns:
        Decimation factor (0.01 to 1.0)
    """
    logger = logging.getLogger("LASAnalysis")
    
    file_size_gb = file_size_mb / 1024
    estimated_ram_needed_gb = file_size_gb * 1.5  # File + XY arrays
    
    # Target using max 50% of available RAM
    safe_ram_budget_gb = available_ram_gb * 0.5
    
    if estimated_ram_needed_gb <= safe_ram_budget_gb:
        # Plenty of RAM, use 100%
        logger.debug(f"Sufficient RAM: need {estimated_ram_needed_gb:.1f}GB, have {safe_ram_budget_gb:.1f}GB available → 100% decimation")
        return 1.0
    
    # Calculate needed decimation
    # XY array scales linearly with decimation
    # decimation = safe_budget / estimated_need
    decimation = safe_ram_budget_gb / estimated_ram_needed_gb
    decimation = max(0.01, min(1.0, decimation))  # Clamp to [0.01, 1.0]
    
    logger.info(f"Adaptive decimation: file={file_size_mb:.0f}MB, available RAM={available_ram_gb:.1f}GB → {decimation*100:.0f}% decimation")
    
    return decimation


def check_minimum_ram(minimum_gb: float = 8.0) -> tuple[bool, float]:
    """
    Check if system has minimum required RAM.
    
    Args:
        minimum_gb: Minimum required RAM in GB
        
    Returns:
        Tuple of (meets_requirement, available_ram_gb)
    """
    available = get_available_ram_gb()
    return (available >= minimum_gb, available)


def format_ram_size(gb: float) -> str:
    """
    Format RAM size in human-readable format.
    
    Args:
        gb: RAM size in GB
        
    Returns:
        Formatted string (e.g., "15.7 GB")
    """
    return f"{gb:.1f} GB"


def validate_file_size(file_path: Path, max_size_gb: float = 20.0) -> Tuple[bool, str]:
    """
    Validate that a file doesn't exceed maximum size limit.
    
    Args:
        file_path: Path to the file to check
        max_size_gb: Maximum allowed file size in GB (default: 20GB)
        
    Returns:
        Tuple of (is_valid, message)
    """
    logger = logging.getLogger("LASAnalysis")
    
    try:
        file_size_gb = os.path.getsize(file_path) / (1024 ** 3)
        
        if file_size_gb > max_size_gb:
            message = f"File '{file_path.name}' is {file_size_gb:.1f}GB, exceeds {max_size_gb}GB limit"
            logger.error(message)
            return False, message
        
        return True, f"File size OK: {file_size_gb:.1f}GB"
    except Exception as e:
        message = f"Error checking file size: {str(e)}"
        logger.error(message)
        return False, message


def estimate_total_ram_needed(file_paths: List[Path]) -> float:
    """
    Estimate total RAM needed to process all files.
    Assumes each file needs roughly 1.5x its size in RAM (file data + XY arrays).
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        Estimated total RAM needed in GB
    """
    total_size_gb = 0.0
    for file_path in file_paths:
        try:
            size_gb = os.path.getsize(file_path) / (1024 ** 3)
            total_size_gb += size_gb
        except Exception:
            pass
    
    # Each file needs ~1.5x its size: file + XY arrays
    estimated_ram_gb = total_size_gb * 1.5
    return estimated_ram_gb


def estimate_concurrent_ram_needed(file_paths: List[Path], num_threads: int) -> float:
    """
    Estimate RAM needed for only the concurrent threads that will run simultaneously.
    This is more accurate than total RAM needed since threads process files sequentially.
    
    Args:
        file_paths: List of file paths to process
        num_threads: Number of concurrent threads
        
    Returns:
        Estimated RAM needed in GB for concurrent operations
    """
    if not file_paths or num_threads < 1:
        return 0.0
    
    # Calculate average file size
    total_size_gb = sum(os.path.getsize(f) / (1024 ** 3) for f in file_paths if os.path.exists(f))
    average_file_size_gb = total_size_gb / len(file_paths) if file_paths else 0
    
    # Concurrent RAM = (average file size * 1.5) * number of threads
    # This accounts for the files that will be loaded simultaneously
    concurrent_ram_gb = (average_file_size_gb * 1.5) * num_threads
    
    return concurrent_ram_gb


def calculate_optimal_threads(total_ram_needed_gb: float, available_ram_gb: float, 
                             use_convex_hull: bool = False) -> int:
    """
    Calculate optimal number of threads based on RAM availability.
    
    Strategy:
    - Minimum 8GB available RAM assumed
    - Base thread count: 12 for normal, 4 for convex hull (RAM intensive)
    - Scale down if total RAM needed > 50% of available
    - Never go below 1, never above 12
    
    Args:
        total_ram_needed_gb: Total estimated RAM needed in GB
        available_ram_gb: Available system RAM in GB
        use_convex_hull: Whether convex hull calculation is enabled (uses more RAM)
        
    Returns:
        Optimal number of threads (1-12)
    """
    logger = logging.getLogger("LASAnalysis")
    
    # Base thread count depends on workload
    base_threads = 4 if use_convex_hull else 12
    
    # If total RAM needed fits comfortably, use base threads
    safe_ram_budget = available_ram_gb * 0.5
    if total_ram_needed_gb <= safe_ram_budget:
        logger.debug(f"Optimal threads: {base_threads} (RAM within budget: {total_ram_needed_gb:.1f}GB / {safe_ram_budget:.1f}GB)")
        return base_threads
    
    # Scale down threads based on RAM pressure
    # If we need more than 50% available RAM, reduce parallelism
    ratio = safe_ram_budget / total_ram_needed_gb
    scaled_threads = max(1, int(base_threads * ratio))
    scaled_threads = min(base_threads, scaled_threads)
    
    logger.info(f"Optimal threads scaled down: {scaled_threads} (high RAM usage: {total_ram_needed_gb:.1f}GB needed, {safe_ram_budget:.1f}GB safe budget)")
    return scaled_threads


def calculate_optimal_threads_smart(file_paths: List[Path], available_ram_gb: float, 
                                   use_convex_hull: bool = False) -> int:
    """
    Calculate optimal number of concurrent threads based on actual file sizes and available RAM.
    This is more accurate than using total batch size, since only concurrent threads matter.
    
    Strategy:
    - Calculate average file size from actual files
    - Estimate RAM per concurrent file: avg_size × 1.0 (file size only, OS overhead in 85% budget)
    - Max concurrent threads: floor(available_ram × 0.90 / (avg_size × 1.0))
    - Cap at reasonable limits: 4 for convex hull, 12 for normal
    - Never go below 1
    
    Args:
        file_paths: List of LAS file paths
        available_ram_gb: Available system RAM in GB
        use_convex_hull: Whether convex hull calculation is enabled (uses more RAM)
        
    Returns:
        Optimal number of threads (1-12)
    """
    logger = logging.getLogger("LASAnalysis")
    
    if not file_paths:
        return 1
    
    # Calculate average file size
    total_size_gb = sum(os.path.getsize(f) / (1024 ** 3) for f in file_paths if os.path.exists(f))
    avg_file_size_gb = total_size_gb / len(file_paths) if file_paths else 1.0
    
    # RAM per concurrent file (1.5x file size for overhead)
    ram_per_concurrent_file = avg_file_size_gb * 1.0
    
    # Calculate max threads that fit in available RAM (use 75% as safe limit)
    safe_ram_for_processing = available_ram_gb * 0.90
    max_threads_by_ram = int(safe_ram_for_processing / ram_per_concurrent_file)
    max_threads_by_ram = max(1, max_threads_by_ram)  # Never less than 1
    
    # Cap at reasonable limits
    max_threads_base = 4 if use_convex_hull else 12
    optimal_threads = min(max_threads_by_ram, max_threads_base)
    optimal_threads = max(1, optimal_threads)
    
    logger.info(f"Thread calculation: avg_file={avg_file_size_gb:.1f}GB, "
               f"ram_per_file={ram_per_concurrent_file:.1f}GB, "
               f"available_ram={available_ram_gb:.1f}GB, "
               f"max_by_ram={max_threads_by_ram}, "
               f"max_by_config={max_threads_base}, "
               f"optimal={optimal_threads}")
    
    return optimal_threads


def get_process_disk_io_speed() -> float:
    """
    Get current disk I/O speed for the current process in MB/s.
    Uses psutil to monitor read/write bytes per second.
    
    Returns:
        Current disk I/O speed in MB/s (smoothed average)
    """
    try:
        process = psutil.Process()
        io_counters = process.io_counters()
        
        # Get read bytes (this includes system caching)
        read_bytes = io_counters.read_bytes
        
        # For more accurate disk speed, we'd need to sample twice with a small delay
        # This is a simplified version that works for ongoing operations
        # In practice, this gets called repeatedly and we calculate speed from delta
        
        return read_bytes / (1024 ** 2)  # Convert to MB
    except (AttributeError, psutil.NoSuchProcess, psutil.AccessDenied):
        # Disk I/O not available or process not accessible
        return 0.0


class DiskIOMonitor:
    """Monitor and calculate disk I/O speed for the current process."""
    
    def __init__(self):
        """Initialize the disk I/O monitor."""
        self.last_io_bytes = 0
        self.last_time = 0
        self.current_speed_mbs = 0.0
        self.speeds = []  # Rolling average of last 10 samples
        
        try:
            process = psutil.Process()
            io_counters = process.io_counters()
            self.last_io_bytes = io_counters.read_bytes
            import time
            self.last_time = time.time()
        except Exception:
            pass
    
    def update(self) -> float:
        """
        Update the current disk I/O speed.
        Should be called repeatedly (e.g., every 500ms) during processing.
        
        Returns:
            Current disk I/O speed in MB/s
        """
        try:
            import time
            current_time = time.time()
            process = psutil.Process()
            io_counters = process.io_counters()
            current_io_bytes = io_counters.read_bytes
            
            time_delta = current_time - self.last_time
            if time_delta > 0:
                # Calculate speed in MB/s
                bytes_delta = current_io_bytes - self.last_io_bytes
                speed_mbs = (bytes_delta / (1024 ** 2)) / time_delta if time_delta > 0 else 0
                
                # Keep rolling average of last 10 samples
                self.speeds.append(max(0, speed_mbs))  # Clamp to non-negative
                if len(self.speeds) > 10:
                    self.speeds.pop(0)
                
                # Calculate smoothed average
                self.current_speed_mbs = sum(self.speeds) / len(self.speeds)
            
            self.last_io_bytes = current_io_bytes
            self.last_time = current_time
            
            return self.current_speed_mbs
        except Exception:
            return 0.0
    
    def get_speed(self) -> float:
        """Get the current smoothed disk I/O speed in MB/s."""
        return self.current_speed_mbs
    
    def reset(self):
        """Reset the monitor for a new measurement cycle."""
        self.speeds.clear()
        try:
            process = psutil.Process()
            io_counters = process.io_counters()
            self.last_io_bytes = io_counters.read_bytes
            import time
            self.last_time = time.time()
        except Exception:
            pass


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        bytes_size: File size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 GB", "512 MB")
    """
    for unit in ['B', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"

