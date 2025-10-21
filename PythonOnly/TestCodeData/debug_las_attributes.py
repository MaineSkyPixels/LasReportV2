#!/usr/bin/env python3
"""Debug script to check laspy attributes."""

import laspy
from pathlib import Path

las_file = Path("cloud5.las")

if las_file.exists():
    with laspy.open(las_file) as las:
        las_data = las.read()
        print("LAS Data Attributes:")
        print(dir(las_data))
        print("\n" + "="*60)
        print("\nKey attributes:")
        print(f"  return_num: {hasattr(las_data, 'return_num')}")
        print(f"  return_number: {hasattr(las_data, 'return_number')}")
        print(f"  classification: {hasattr(las_data, 'classification')}")
        print(f"  scan_angle_rank: {hasattr(las_data, 'scan_angle_rank')}")
        print(f"  scan_angle: {hasattr(las_data, 'scan_angle')}")
        
        # Try different names
        if hasattr(las_data, 'return_num'):
            print(f"\nreturn_num type: {type(las_data.return_num)}")
            print(f"return_num sample: {las_data.return_num[:5]}")
        
        if hasattr(las_data, 'return_number'):
            print(f"\nreturn_number type: {type(las_data.return_number)}")
            print(f"return_number sample: {las_data.return_number[:5]}")
        
        if hasattr(las_data, 'classification'):
            print(f"\nclassification type: {type(las_data.classification)}")
            print(f"classification sample: {las_data.classification[:5]}")
        
        if hasattr(las_data, 'scan_angle_rank'):
            print(f"\nscan_angle_rank type: {type(las_data.scan_angle_rank)}")
            print(f"scan_angle_rank sample: {las_data.scan_angle_rank[:5]}")
        
        if hasattr(las_data, 'scan_angle'):
            print(f"\nscan_angle type: {type(las_data.scan_angle)}")
            print(f"scan_angle sample: {las_data.scan_angle[:5]}")
else:
    print(f"File not found: {las_file}")
