#!/usr/bin/env python3
"""
Test script to check CRS information collection.
"""

from processor_python_only import PythonLASProcessor
from pathlib import Path

def test_crs_collection():
    """Test CRS information collection."""
    
    print("Testing CRS Information Collection")
    print("=" * 40)
    
    # Look for LAS files
    las_files = list(Path(".").glob("*.las"))
    
    if not las_files:
        print("No LAS files found")
        return
    
    # Initialize processor
    processor = PythonLASProcessor(
        max_workers=1,
        use_detailed_acreage=False,  # Skip convex hull for faster testing
        low_ram_mode=False
    )
    
    # Process files
    results, aggregate = processor.process_files(las_files)
    
    print(f"Processed {len(results)} files")
    print()
    
    for result in results:
        print(f"File: {result.filename}")
        print(f"  CRS Info: '{result.crs_info}'")
        print(f"  CRS Units: '{result.crs_units}'")
        print(f"  Error: {result.error}")
        print()
    
    # Test report generator CRS collection
    from report_generator import ReportGenerator
    
    generator = ReportGenerator(Path("."))
    
    # Collect CRS information like the report generator does
    crs_systems = set()
    crs_units = set()
    
    for result in results:
        if not result.error:
            if result.crs_info:
                print(f"Processing CRS info for {result.filename}: {result.crs_info[:100]}...")
                crs_name = generator._parse_crs_name(result.crs_info)
                if crs_name:
                    print(f"  Parsed CRS name: {crs_name}")
                    crs_systems.add(crs_name)
                else:
                    print(f"  Failed to parse CRS name")
            
            if result.crs_units and result.crs_units != "unknown":
                crs_units.add(result.crs_units)
    
    print(f"\nCollected CRS Systems: {list(crs_systems)}")
    print(f"Collected CRS Units: {list(crs_units)}")

if __name__ == "__main__":
    test_crs_collection()
