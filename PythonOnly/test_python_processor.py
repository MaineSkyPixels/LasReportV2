#!/usr/bin/env python3
"""
Test script for Python-only LAS processor.
Demonstrates the functionality without external lasinfo dependency.
"""

import sys
from pathlib import Path
from processor_python_only import PythonLASProcessor

def test_python_processor():
    """Test the Python-only LAS processor."""
    
    print("Python-Only LAS Processor Test")
    print("=" * 40)
    
    # Check if we have the required libraries
    try:
        import laspy
        print("[OK] laspy available")
    except ImportError:
        print("[ERROR] laspy not available - install with: pip install laspy")
        return False
    
    try:
        import scipy
        print("[OK] scipy available")
    except ImportError:
        print("[ERROR] scipy not available - install with: pip install scipy")
        return False
    
    try:
        import numpy
        print("[OK] numpy available")
    except ImportError:
        print("[ERROR] numpy not available - install with: pip install numpy")
        return False
    
    # Initialize processor
    processor = PythonLASProcessor(
        max_workers=2,
        use_detailed_acreage=True,
        low_ram_mode=False
    )
    
    print(f"\nProcessor initialized:")
    print(f"  - Max workers: {processor.max_workers}")
    print(f"  - Detailed acreage: {processor.use_detailed_acreage}")
    print(f"  - Low RAM mode: {processor.low_ram_mode}")
    
    # Look for LAS files in current directory
    las_files = list(Path(".").glob("*.las"))
    
    if not las_files:
        print("\n[ERROR] No LAS files found in current directory")
        print("   Place some .las files in the current directory to test")
        return False
    
    print(f"\nFound {len(las_files)} LAS file(s):")
    for file in las_files:
        print(f"  - {file.name}")
    
    # Process files
    print(f"\nProcessing {len(las_files)} file(s)...")
    
    def progress_callback(message_type, filename, message):
        print(f"  {message}")
    
    results = processor.process_files(las_files, progress_callback)
    
    # Display results
    print(f"\nProcessing Results:")
    print("=" * 40)
    
    for result in results:
        print(f"\nFile: {result.filename}")
        print(f"  Point Count: {result.point_count:,}")
        print(f"  File Size: {result.file_size_mb:.2f} MB")
        print(f"  Processing Time: {result.processing_time:.2f} sec")
        print(f"  Point Density: {result.point_density:.2f} pts/m²")
        print(f"  Bounds X: {result.min_x:.2f} to {result.max_x:.2f}")
        print(f"  Bounds Y: {result.min_y:.2f} to {result.max_y:.2f}")
        print(f"  Bounds Z: {result.min_z:.2f} to {result.max_z:.2f}")
        print(f"  CRS Units: {result.crs_units}")
        if result.crs_info:
            print(f"  CRS Info: {result.crs_info}")
        if result.acreage_detailed > 0:
            print(f"  Convex Hull Acreage: {result.acreage_detailed:.2f} acres")
        if result.error:
            print(f"  [ERROR] Error: {result.error}")
        else:
            print(f"  [OK] Success")
    
    print(f"\n[OK] Test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_python_processor()
    sys.exit(0 if success else 1)
