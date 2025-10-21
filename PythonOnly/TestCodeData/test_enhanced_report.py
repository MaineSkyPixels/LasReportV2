#!/usr/bin/env python3
"""
Test script to verify enhanced LAS report with return counts, classifications, and scan angles.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processor_python_only import PythonLASProcessor
from report_generator import ReportGenerator

def test_enhanced_report():
    """Test enhanced report generation."""
    
    print("Testing Enhanced LAS Report")
    print("=" * 60)
    
    # Initialize processor
    processor = PythonLASProcessor(
        use_detailed_acreage=True,
        max_workers=2,
        low_ram_mode=False
    )
    
    # Find LAS files
    las_files = [Path("cloud5.las")]
    
    if not las_files[0].exists():
        print(f"[ERROR] LAS file not found: {las_files[0]}")
        return
    
    print(f"Processing {len(las_files)} file(s)...")
    
    # Process files
    results, aggregate = processor.process_files(las_files)
    
    print(f"Processing completed. Results: {len(results)} files")
    
    # Display per-file information
    for result in results:
        print(f"\nFile: {result.filename}")
        print(f"  Point Count: {result.point_count:,}")
        print(f"  Returns:")
        print(f"    1st: {result.returns_1:,}")
        print(f"    2nd: {result.returns_2:,}")
        print(f"    3rd: {result.returns_3:,}")
        print(f"  Classifications:")
        print(f"    Ground: {result.classification_ground:,}")
        print(f"    Low Veg: {result.classification_low_vegetation:,}")
        print(f"    Med Veg: {result.classification_medium_vegetation:,}")
        print(f"    High Veg: {result.classification_high_vegetation:,}")
        print(f"    Water: {result.classification_water:,}")
        print(f"    Building: {result.classification_building:,}")
    
    # Display aggregates
    print(f"\n\nAggregate Statistics:")
    print(f"  Total Points: {aggregate.get('total_points', 0):,}")
    print(f"  Returns:")
    print(f"    1st: {aggregate.get('total_returns_1', 0):,}")
    print(f"    2nd: {aggregate.get('total_returns_2', 0):,}")
    print(f"    3rd: {aggregate.get('total_returns_3', 0):,}")
    print(f"  Classifications:")
    print(f"    Ground: {aggregate.get('total_classification_ground', 0):,}")
    print(f"    Vegetation: {aggregate.get('total_classification_low_vegetation', 0) + aggregate.get('total_classification_medium_vegetation', 0) + aggregate.get('total_classification_high_vegetation', 0):,}")
    print(f"    Water: {aggregate.get('total_classification_water', 0):,}")
    print(f"  Scan Angle:")
    print(f"    Min: {aggregate.get('scan_angle_global_min', 0):.1f}°")
    print(f"    Max: {aggregate.get('scan_angle_global_max', 0):.1f}°")
    
    # Generate report
    print(f"\nGenerating report...")
    generator = ReportGenerator(output_directory=Path("."))
    report_path = generator.generate_las_report(results, aggregate)
    
    print(f"[OK] Report generated: {report_path}")

if __name__ == "__main__":
    test_enhanced_report()
