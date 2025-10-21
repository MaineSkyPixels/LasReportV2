#!/usr/bin/env python3
"""
Simple script to dump all LAS header information to a text file.
"""

import laspy
from pathlib import Path
from datetime import datetime

def dump_las_header(las_file_path: Path, output_file: Path):
    """
    Dump all LAS header information to a text file.
    
    Args:
        las_file_path: Path to LAS file
        output_file: Path to output text file
    """
    
    print(f"Dumping header information from: {las_file_path.name}")
    print(f"Output file: {output_file.name}")
    
    try:
        with laspy.open(las_file_path) as las_file:
            header = las_file.header
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"LAS File Header Information Dump\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Source File: {las_file_path.name}\n")
                f.write("=" * 80 + "\n\n")
                
                # Get all available attributes
                f.write("ALL AVAILABLE HEADER ATTRIBUTES\n")
                f.write("-" * 40 + "\n")
                
                # Get all attributes of the header object
                header_attrs = [attr for attr in dir(header) if not attr.startswith('_')]
                
                for attr in sorted(header_attrs):
                    try:
                        value = getattr(header, attr)
                        if not callable(value):
                            f.write(f"{attr}: {value}\n")
                    except Exception as e:
                        f.write(f"{attr}: Error accessing - {str(e)}\n")
                
                f.write("\n")
                
                # Try to access common LAS header fields safely
                f.write("COMMON LAS HEADER FIELDS\n")
                f.write("-" * 40 + "\n")
                
                common_fields = [
                    'point_count', 'scale', 'offset', 'min', 'max', 
                    'point_format', 'vlrs', 'evlrs'
                ]
                
                for field in common_fields:
                    try:
                        value = getattr(header, field, 'Not available')
                        f.write(f"{field}: {value}\n")
                    except Exception as e:
                        f.write(f"{field}: Error - {str(e)}\n")
                
                f.write("\n")
                
                # Variable Length Records (VLRs)
                f.write("VARIABLE LENGTH RECORDS (VLRs)\n")
                f.write("-" * 40 + "\n")
                vlrs = getattr(header, 'vlrs', None)
                if vlrs is not None:
                    f.write(f"Number of VLRs: {len(vlrs)}\n\n")
                else:
                    f.write("Number of VLRs: None\n\n")
                
                if vlrs is not None:
                    for i, vlr in enumerate(vlrs):
                        f.write(f"VLR {i+1}:\n")
                        f.write(f"  Record ID: {vlr.record_id}\n")
                        f.write(f"  User ID: {vlr.user_id}\n")
                        f.write(f"  Description: {vlr.description}\n")
                        
                        # Try to get string content
                        if hasattr(vlr, 'string') and vlr.string:
                            try:
                                if isinstance(vlr.string, bytes):
                                    vlr_string = vlr.string.decode('utf-8', errors='ignore')
                                else:
                                    vlr_string = str(vlr.string)
                                
                                f.write(f"  String Content:\n")
                                # Write string content with proper indentation
                                for line in vlr_string.split('\n'):
                                    f.write(f"    {line}\n")
                            except Exception as e:
                                f.write(f"  String Content: Error decoding - {str(e)}\n")
                        else:
                            f.write(f"  String Content: None\n")
                        
                        f.write("\n")
                
                # Extended Variable Length Records (EVLRs)
                f.write("EXTENDED VARIABLE LENGTH RECORDS (EVLRs)\n")
                f.write("-" * 40 + "\n")
                evlrs = getattr(header, 'evlrs', None)
                if evlrs is not None:
                    f.write(f"Number of EVLRs: {len(evlrs)}\n\n")
                else:
                    f.write("Number of EVLRs: None\n\n")
                
                if evlrs is not None:
                    for i, evlr in enumerate(evlrs):
                        f.write(f"EVLR {i+1}:\n")
                        f.write(f"  Record ID: {evlr.record_id}\n")
                        f.write(f"  User ID: {evlr.user_id}\n")
                        f.write(f"  Description: {evlr.description}\n")
                        
                        # Try to get string content
                        if hasattr(evlr, 'string') and evlr.string:
                            try:
                                if isinstance(evlr.string, bytes):
                                    evlr_string = evlr.string.decode('utf-8', errors='ignore')
                                else:
                                    evlr_string = str(evlr.string)
                                
                                f.write(f"  String Content:\n")
                                # Write string content with proper indentation
                                for line in evlr_string.split('\n'):
                                    f.write(f"    {line}\n")
                            except Exception as e:
                                f.write(f"  String Content: Error decoding - {str(e)}\n")
                        else:
                            f.write(f"  String Content: None\n")
                        
                        f.write("\n")
                
                f.write("=" * 80 + "\n")
                f.write("End of LAS Header Information Dump\n")
        
        print(f"[OK] Header information successfully dumped to: {output_file.name}")
        
    except Exception as e:
        print(f"[ERROR] Error dumping header information: {str(e)}")
        return False
    
    return True

def main():
    """Main function to dump LAS header information."""
    
    # Look for cloud5.las in current directory
    las_file = Path("cloud5.las")
    
    if not las_file.exists():
        print(f"[ERROR] LAS file not found: {las_file}")
        print("Make sure cloud5.las is in the current directory")
        return
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"cloud5_las_header_dump_{timestamp}.txt")
    
    # Dump header information
    success = dump_las_header(las_file, output_file)
    
    if success:
        print(f"\n[OK] Header dump complete!")
        print(f"Output file: {output_file.absolute()}")
        print(f"File size: {output_file.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()
