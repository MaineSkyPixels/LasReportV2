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
                
                # Basic file information
                f.write("BASIC FILE INFORMATION\n")
                f.write("-" * 40 + "\n")
                f.write(f"File Signature: {getattr(header, 'file_signature', 'Not available')}\n")
                f.write(f"Version: {getattr(header, 'version_major', 'N/A')}.{getattr(header, 'version_minor', 'N/A')}\n")
                f.write(f"System Identifier: {getattr(header, 'system_identifier', 'Not available')}\n")
                f.write(f"Generating Software: {getattr(header, 'generating_software', 'Not available')}\n")
                f.write(f"File Creation Day: {getattr(header, 'file_creation_day', 'Not available')}\n")
                f.write(f"File Creation Year: {getattr(header, 'file_creation_year', 'Not available')}\n")
                f.write(f"Header Size: {getattr(header, 'header_size', 'Not available')}\n")
                f.write(f"Point Data Format: {header.point_format.id}\n")
                f.write(f"Point Data Record Length: {header.point_data_record_length}\n")
                f.write(f"Number of Point Records: {header.point_count:,}\n")
                f.write(f"Number of Points by Return: {getattr(header, 'number_of_points_by_return', 'Not available')}\n")
                f.write("\n")
                
                # Scale factors and offsets
                f.write("SCALE FACTORS AND OFFSETS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Scale Factor X: {header.scale[0]}\n")
                f.write(f"Scale Factor Y: {header.scale[1]}\n")
                f.write(f"Scale Factor Z: {header.scale[2]}\n")
                f.write(f"Offset X: {header.offset[0]}\n")
                f.write(f"Offset Y: {header.offset[1]}\n")
                f.write(f"Offset Z: {header.offset[2]}\n")
                f.write("\n")
                
                # Bounds
                f.write("BOUNDS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Min X: {header.min[0]}\n")
                f.write(f"Max X: {header.max[0]}\n")
                f.write(f"Min Y: {header.min[1]}\n")
                f.write(f"Max Y: {header.max[1]}\n")
                f.write(f"Min Z: {header.min[2]}\n")
                f.write(f"Max Z: {header.max[2]}\n")
                f.write("\n")
                
                # Variable Length Records (VLRs)
                f.write("VARIABLE LENGTH RECORDS (VLRs)\n")
                f.write("-" * 40 + "\n")
                f.write(f"Number of VLRs: {len(header.vlrs)}\n\n")
                
                for i, vlr in enumerate(header.vlrs):
                    f.write(f"VLR {i+1}:\n")
                    f.write(f"  Record ID: {vlr.record_id}\n")
                    f.write(f"  User ID: {vlr.user_id}\n")
                    f.write(f"  Description: {vlr.description}\n")
                    f.write(f"  Record Length After Header: {vlr.record_length_after_header}\n")
                    
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
                f.write(f"Number of EVLRs: {len(header.evlrs)}\n\n")
                
                for i, evlr in enumerate(header.evlrs):
                    f.write(f"EVLR {i+1}:\n")
                    f.write(f"  Record ID: {evlr.record_id}\n")
                    f.write(f"  User ID: {evlr.user_id}\n")
                    f.write(f"  Description: {evlr.description}\n")
                    f.write(f"  Record Length After Header: {evlr.record_length_after_header}\n")
                    
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
                
                # Additional header attributes
                f.write("ADDITIONAL HEADER ATTRIBUTES\n")
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
