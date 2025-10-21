#!/usr/bin/env python3
"""
Debug script to examine CRS information in LAS files.
"""

import laspy
from pathlib import Path

def debug_crs_info(filepath: Path):
    """Debug CRS information extraction from LAS file."""
    
    print(f"Debugging CRS info for: {filepath.name}")
    print("=" * 60)
    
    try:
        with laspy.open(filepath) as las_file:
            header = las_file.header
            
            print("Header Information:")
            print(f"  Point count: {header.point_count:,}")
            print(f"  Scale factors: {header.scale}")
            print(f"  Offsets: {header.offset}")
            print(f"  Bounds: min={header.min}, max={header.max}")
            print()
            
            print("Variable Length Records (VLRs):")
            print(f"  Number of VLRs: {len(header.vlrs)}")
            
            for i, vlr in enumerate(header.vlrs):
                print(f"\n  VLR {i+1}:")
                print(f"    Record ID: {vlr.record_id}")
                print(f"    User ID: {vlr.user_id}")
                print(f"    Description: {vlr.description}")
                
                if hasattr(vlr, 'string') and vlr.string:
                    try:
                        vlr_string = vlr.string.decode('utf-8', errors='ignore')
                        print(f"    String content (first 200 chars):")
                        print(f"      {vlr_string[:200]}...")
                        
                        # Look for specific CRS-related terms
                        crs_terms = ['US survey foot', 'Linear_Foot_US_Survey', 'linear_foot', 'ftus', 
                                   'meter', 'linear_meter', 'GTCitationGeoKey', 'NAD83', 'WGS']
                        
                        found_terms = []
                        for term in crs_terms:
                            if term.lower() in vlr_string.lower():
                                found_terms.append(term)
                        
                        if found_terms:
                            print(f"    Found CRS terms: {found_terms}")
                            
                    except Exception as e:
                        print(f"    Error decoding string: {e}")
                else:
                    print(f"    No string content")
            
            # Calculate bounds area in raw units
            area_raw = abs(header.max[0] - header.min[0]) * abs(header.max[1] - header.min[1])
            print(f"\nCalculations:")
            print(f"  Raw area (in file units): {area_raw:,.2f}")
            print(f"  Point density (raw): {header.point_count / area_raw:,.2f} pts/unit²")
            
            # If we assume US Survey Feet
            us_survey_ft_to_meters = 0.3048006096
            area_sq_meters_usft = area_raw * (us_survey_ft_to_meters ** 2)
            density_usft = header.point_count / area_sq_meters_usft
            print(f"  If US Survey Feet: {density_usft:,.2f} pts/m²")
            
            # If we assume International Feet
            feet_to_meters = 0.3048
            area_sq_meters_ft = area_raw * (feet_to_meters ** 2)
            density_ft = header.point_count / area_sq_meters_ft
            print(f"  If International Feet: {density_ft:,.2f} pts/m²")
            
            # If we assume Meters
            density_m = header.point_count / area_raw
            print(f"  If Meters: {density_m:,.2f} pts/m²")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Look for LAS files in current directory
    las_files = list(Path(".").glob("*.las"))
    
    if not las_files:
        print("No LAS files found in current directory")
    else:
        for las_file in las_files:
            debug_crs_info(las_file)
            print("\n" + "="*80 + "\n")
