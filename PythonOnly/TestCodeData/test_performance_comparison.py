#!/usr/bin/env python3
"""
Performance comparison test: with and without classification extraction.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processor_python_only import PythonLASProcessor

def test_performance():
    """Test and compare performance."""
    
    print("Performance Comparison Test")
    print("=" * 60)
    
    las_files = [Path("cloud5.las")]
    
    if not las_files[0].exists():
        print(f"[ERROR] LAS file not found: {las_files[0]}")
        return
    
    # Test WITH classification extraction
    print("\n1. Processing WITH Classification Extraction...")
    print("-" * 60)
    start_time = time.time()
    
    processor = PythonLASProcessor(
        max_workers=4,
        use_detailed_acreage=True,
        low_ram_mode=False,
        extract_classifications=True
    )
    
    results1, aggregate1 = processor.process_files(las_files)
    elapsed1 = time.time() - start_time
    
    print(f"  Processing time: {elapsed1:.2f} seconds")
    for result in results1:
        print(f"  Ground points: {result.classification_ground:,}")
        print(f"  Returns 1st: {result.returns_1:,}")
        print(f"  Scan angle range: {result.scan_angle_min:.1f}° to {result.scan_angle_max:.1f}°")
    
    # Test WITHOUT classification extraction
    print("\n2. Processing WITHOUT Classification Extraction...")
    print("-" * 60)
    start_time = time.time()
    
    processor = PythonLASProcessor(
        max_workers=4,
        use_detailed_acreage=True,
        low_ram_mode=False,
        extract_classifications=False
    )
    
    results2, aggregate2 = processor.process_files(las_files)
    elapsed2 = time.time() - start_time
    
    print(f"  Processing time: {elapsed2:.2f} seconds")
    for result in results2:
        print(f"  Ground points: {result.classification_ground:,}")
        print(f"  Returns 1st: {result.returns_1:,}")
        print(f"  Scan angle range: {result.scan_angle_min:.1f}° to {result.scan_angle_max:.1f}°")
    
    # Summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"With classifications:    {elapsed1:.2f} seconds")
    print(f"Without classifications: {elapsed2:.2f} seconds")
    print(f"Speedup:                 {elapsed1/elapsed2:.2f}x")
    print(f"Time saved:              {elapsed1-elapsed2:.2f} seconds ({(1-elapsed2/elapsed1)*100:.1f}%)")

if __name__ == "__main__":
    test_performance()
