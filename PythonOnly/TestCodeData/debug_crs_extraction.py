#!/usr/bin/env python3
"""
Debug script to see what CRS information is being extracted from VLRs.
"""

import laspy
from pathlib import Path
import re

def debug_crs_extraction():
    """Debug CRS extraction from VLRs."""
    
    print("Debugging CRS Extraction from VLRs")
    print("=" * 50)
    
    las_file = Path("cloud5.las")
    
    if not las_file.exists():
        print(f"[ERROR] LAS file not found: {las_file}")
        return
    
    try:
        with laspy.open(las_file) as las_file_obj:
            header = las_file_obj.header
            
            print(f"Number of VLRs: {len(header.vlrs)}")
            print()
            
            for i, vlr in enumerate(header.vlrs):
                print(f"VLR {i+1}:")
                print(f"  Record ID: {vlr.record_id}")
                print(f"  User ID: {vlr.user_id}")
                print(f"  Description: {vlr.description}")
                
                if hasattr(vlr, 'string') and vlr.string:
                    try:
                        if isinstance(vlr.string, bytes):
                            vlr_string = vlr.string.decode('utf-8', errors='ignore')
                        else:
                            vlr_string = str(vlr.string)
                        
                        print(f"  String Content: {vlr_string[:200]}...")
                        
                        # Test the regex patterns
                        if 'GTCitationGeoKey' in vlr_string:
                            match = re.search(r'GTCitationGeoKey:\s*([^|]+)', vlr_string)
                            if match:
                                print(f"  GTCitationGeoKey match: '{match.group(1).strip()}'")
                        
                        if 'NAD83' in vlr_string and 'Maine' in vlr_string:
                            match = re.search(r"'([^']*NAD83[^']*Maine[^']*)'", vlr_string)
                            if match:
                                print(f"  NAD83/Maine match: '{match.group(1).strip()}'")
                        
                        # Look for the full CRS name pattern
                        if 'NAD83(2011) / Maine West (ftUS) + NAVD88 height (ftUS)' in vlr_string:
                            print(f"  Found full CRS name in VLR!")
                        
                    except Exception as e:
                        print(f"  Error processing string: {str(e)}")
                else:
                    print(f"  String Content: None")
                
                print()
                
    except Exception as e:
        print(f"[ERROR] Error reading LAS file: {str(e)}")

if __name__ == "__main__":
    debug_crs_extraction()
