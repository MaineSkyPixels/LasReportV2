"""
Scanner module for finding LAS files in directories.
"""

from pathlib import Path
from typing import List


def find_las_files(directory: str) -> List[Path]:
    """
    Find all LAS files in a directory (non-recursive).
    
    Args:
        directory: Path to the directory to scan
        
    Returns:
        List of Path objects for all .las files found
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    # Find all .las files in current directory only (case-insensitive)
    las_files = list(dir_path.glob("*.las")) + list(dir_path.glob("*.LAS"))
    
    # Remove duplicates and sort
    las_files = sorted(set(las_files))
    
    return las_files

