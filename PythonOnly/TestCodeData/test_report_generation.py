#!/usr/bin/env python3
"""
Test script to generate a report and check the coordinate system information.
"""

import sys
from pathlib import Path
from processor_python_only import PythonLASProcessor
from report_generator import ReportGenerator

def test_report_generation():
    """Test report generation with coordinate system information."""
    
    print("Testing Report Generation with Coordinate System Information")
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
    
    # Check CRS information in results
    for result in results:
        print(f"\nFile: {result.filename}")
        print(f"  CRS Info: {result.crs_info}")
        print(f"  CRS Units: {result.crs_units}")
    
    # Generate report
    print(f"\nGenerating report...")
    generator = ReportGenerator(output_directory=Path("."))
    report_path = generator.generate_las_report(results, aggregate)
    
    print(f"[OK] Report generated: {report_path}")
    
    # Read and display the coordinate system section
    print(f"\nReading coordinate system section from report...")
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Find the coordinate system section
        import re
        crs_section = re.search(r'<h4>🌐 Coordinate Reference System</h4>(.*?)</div>', content, re.DOTALL)
        if crs_section:
            print("Coordinate Reference System Section:")
            print("-" * 40)
            print(crs_section.group(1))
        else:
            print("Coordinate system section not found in report")
        
        # Find the geographic bounds section
        bounds_section = re.search(r'<h4>🗺️ Geographic Bounds \(All Files\)</h4>(.*?)</div>', content, re.DOTALL)
        if bounds_section:
            print("\nGeographic Bounds Section:")
            print("-" * 40)
            print(bounds_section.group(1))
        else:
            print("Geographic bounds section not found in report")

if __name__ == "__main__":
    test_report_generation()
