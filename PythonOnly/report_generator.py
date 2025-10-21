"""
Report generator module for creating HTML reports.
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime
from processor import LASFileInfo


class ReportGenerator:
    """Generates professional HTML reports for LAS file analysis."""
    
    def __init__(self, output_directory: str):
        """
        Initialize the report generator.
        
        Args:
            output_directory: Directory where reports will be saved
        """
        self.output_directory = Path(output_directory)
    
    def generate_las_report(
        self,
        results: List[LASFileInfo],
        aggregate: Dict[str, any]
    ) -> Path:
        """
        Generate a comprehensive LAS report with timestamped filename.
        
        Args:
            results: List of LASFileInfo objects
            aggregate: Dictionary with aggregate statistics
            
        Returns:
            Path to the generated report
        """
        # Generate timestamp: MM-DD-YYYY-HH-MM format
        timestamp = datetime.now().strftime("%m-%d-%Y-%H-%M")
        report_filename = f"LasReport-{timestamp}.html"
        report_path = self.output_directory / report_filename
        
        html_content = self._generate_las_report_html(results, aggregate)
        
        report_path.write_text(html_content, encoding='utf-8')
        return report_path
    
    
    def _generate_las_report_html(
        self,
        results: List[LASFileInfo],
        aggregate: Dict[str, any]
    ) -> str:
        """Generate the HTML content for the summary report."""
        
        import logging
        logger = logging.getLogger("LASAnalysis")
        
        logger.debug("\n" + "="*80)
        logger.debug("REPORT GENERATOR: _generate_summary_html()")
        logger.debug("="*80)
        logger.debug(f"Number of results: {len(results)}")
        
        # Format numbers
        def format_number(num):
            if isinstance(num, int):
                return f"{num:,}"
            return f"{num:,.2f}"
        
        # Calculate total acreage (convex hull only)
        total_convex_hull_acreage = 0.0
        has_convex_hull_data = False
        
        # Collect coordinate system information
        crs_systems = set()
        crs_units = set()
        crs_epsg_codes = set()
        crs_vertical_datums = set()
        
        for result in results:
            if not result.error and result.acreage_detailed > 0:
                total_convex_hull_acreage += result.acreage_detailed
                has_convex_hull_data = True
            
            # Collect CRS information
            if not result.error:
                if result.crs_info:
                    logger.debug(f"CRS info for {result.filename}: {result.crs_info[:200]}...")
                    
                    # Parse the CRS info to extract the main coordinate system name
                    crs_name = self._parse_crs_name(result.crs_info)
                    if crs_name:
                        logger.debug(f"Parsed CRS name: {crs_name}")
                        crs_systems.add(crs_name)
                        
                        # Extract EPSG code from CRS name if present
                        epsg_match = self._extract_epsg_from_crs_name(crs_name)
                        if epsg_match:
                            crs_epsg_codes.add(epsg_match)
                        
                        # Extract vertical datum from CRS name if present
                        vertical_datum = self._extract_vertical_datum_from_crs_name(crs_name)
                        if vertical_datum:
                            crs_vertical_datums.add(vertical_datum)
                
                if result.crs_units and result.crs_units != "unknown":
                    crs_units.add(result.crs_units)
        
        logger.debug(f"Total convex hull acreage: {total_convex_hull_acreage:.4f}")
        logger.debug(f"Has convex hull data: {has_convex_hull_data}")
        logger.debug(f"Collected CRS systems: {list(crs_systems)}")
        logger.debug(f"Collected CRS units: {list(crs_units)}")
        
        # Create file rows
        file_rows = []
        for result in results:
            logger.debug(f"\nProcessing result for: {result.filename}")
            logger.debug(f"  acreage_detailed: {result.acreage_detailed:.4f}")
            logger.debug(f"  error: {result.error}")
            if result.error:
                file_rows.append(f"""
                <tr class="error-row">
                    <td>{result.filename}</td>
                    <td colspan="9" class="error-msg">Error: {result.error}</td>
                </tr>
                """)
            else:
                crs_display = result.crs_units if result.crs_units else "unknown"
                
                # Determine acreage display - only show if convex hull acreage available
                if result.acreage_detailed > 0:
                    acreage_display = f"{result.acreage_detailed:.2f}"
                    acreage_method_label = "Convex Hull (Actual Footprint)"
                    logger.debug(f"  ✓ Displaying convex hull acreage: {acreage_display}")
                else:
                    acreage_display = "-"
                    acreage_method_label = "Not Calculated"
                    logger.debug(f"  ⚠ No convex hull acreage available")
                
                file_rows.append(f"""
                <tr>
                    <td>{result.filename}</td>
                    <td>{format_number(result.point_count)}</td>
                    <td>{format_number(result.returns_1)}/{format_number(result.returns_2)}/{format_number(result.returns_3)}</td>
                    <td>{format_number(result.classification_ground)}</td>
                    <td>{format_number(result.classification_low_vegetation + result.classification_medium_vegetation + result.classification_high_vegetation)}</td>
                    <td>{format_number(result.classification_water)}</td>
                    <td>{result.scan_angle_min:.1f}° to {result.scan_angle_max:.1f}°</td>
                    <td>{format_number(result.point_density) if result.point_density > 0 else '-'}</td>
                    <td>{result.file_size_mb:.2f}</td>
                </tr>
                """)
        
        file_rows_html = '\n'.join(file_rows)
        
        # Calculate scan time
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LAS File Analysis Summary Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .scan-info {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #667eea;
        }}
        
        .scan-info p {{
            margin: 8px 0;
            color: #333;
        }}
        
        .statistics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
        }}
        
        .stat-unit {{
            font-size: 0.8em;
            opacity: 0.8;
            margin-top: 5px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            margin: 30px 0 20px 0;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        thead {{
            background: #f8f9fa;
            border-bottom: 2px solid #667eea;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        tbody tr {{
            transition: background-color 0.2s;
        }}
        
        tbody tr:hover {{
            background-color: #f8f9fa;
        }}
        
        tbody tr:nth-child(even) {{
            background-color: #fafafa;
        }}
        
        .error-row {{
            background-color: #ffe5e5 !important;
            color: #d32f2f;
        }}
        
        .error-row:hover {{
            background-color: #ffcccc !important;
        }}
        
        .error-msg {{
            font-weight: 600;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
            font-size: 0.9em;
        }}
        
        .bounds-highlight {{
            background: #fff3cd;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        
        .unit-label {{
            color: #666;
            font-size: 0.9em;
            font-style: italic;
            margin-left: 5px;
        }}
        
        .bounds-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 20px;
        }}
        
        .bounds-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .bounds-section h4 {{
            margin: 0 0 15px 0;
            color: #333;
            font-size: 1.1em;
            font-weight: 600;
        }}
        
        .bounds-section p {{
            margin: 8px 0;
            color: #333;
        }}
        
        .crs-info {{
            background: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #2196f3;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        
        .file-section {{
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        
        .file-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }}
        
        .file-title {{
            margin: 0;
            font-size: 1.1em;
            font-weight: 600;
        }}
        
        .toggle-btn {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.2s;
        }}
        
        .toggle-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.5);
        }}
        
        .file-content {{
            padding: 20px;
        }}
        
        .error-badge {{
            background: #d32f2f;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        
        .error-box {{
            background: #ffe5e5;
            border: 1px solid #d32f2f;
            border-radius: 5px;
            padding: 15px;
            color: #d32f2f;
            font-weight: 500;
        }}
        
        .file-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-item {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        
        .stat-label {{
            display: block;
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .stat-val {{
            display: block;
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
        }}
        
        .bounds-box {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #667eea;
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            line-height: 1.6;
        }}
        
        .raw-output-container {{
            margin-top: 20px;
            background: white;
            border-radius: 5px;
            overflow: hidden;
        }}
        
        .raw-output {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 10px 0 0 0;
            border-radius: 5px;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                border-radius: 0;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .statistics {{
                grid-template-columns: 1fr;
            }}
            
            table {{
                font-size: 0.9em;
            }}
            
            th, td {{
                padding: 8px 10px;
            }}
            
            .bounds-container {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 LAS File Analysis Report</h1>
            <p>Comprehensive LiDAR Point Cloud Analysis</p>
        </div>
        
        <div class="content">
            <div class="scan-info">
                <p><strong>Scan Date/Time:</strong> {scan_time}</p>
                <p><strong>Output Directory:</strong> {self.output_directory.absolute()}</p>
                <p><strong>Files Analyzed:</strong> {aggregate['valid_files']} of {aggregate['total_files']} files successfully processed</p>
                {f"<p style='color: #d32f2f;'><strong>⚠ Failed Files:</strong> {aggregate['failed_files']}</p>" if aggregate['failed_files'] > 0 else ""}
            </div>
            
            <h2 class="section-title">📈 Summary Statistics</h2>
            <div class="statistics">
                <div class="stat-card">
                    <h3>Total Files</h3>
                    <div class="stat-value">{aggregate['total_files']}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Points</h3>
                    <div class="stat-value">{format_number(aggregate['total_points'])}</div>
                </div>
                <div class="stat-card">
                    <h3>Avg Point Density</h3>
                    <div class="stat-value">{format_number(aggregate['avg_point_density'])}</div>
                    <div class="stat-unit">pts/m²</div>
                </div>
                <div class="stat-card">
                    <h3>Total Data Size</h3>
                    <div class="stat-value">{aggregate['total_file_size_mb']:.2f}</div>
                    <div class="stat-unit">MB</div>
                </div>
                <div class="stat-card">
                    <h3>Total Acreage (Convex Hull)</h3>
                    <div class="stat-value">{total_convex_hull_acreage:.2f}</div>
                    <div class="stat-unit">acres (actual footprint)</div>
                </div>
            </div>
            
            <h2 class="section-title">📊 Returns by Number</h2>
            <div class="statistics">
                <div class="stat-card">
                    <h3>Return 1st</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_returns_1', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Return 2nd</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_returns_2', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Return 3rd</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_returns_3', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Return 4th</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_returns_4', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Return 5th</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_returns_5', 0))}</div>
                </div>
            </div>
            
            <h2 class="section-title">🏷️ Point Classifications</h2>
            <div class="statistics">
                <div class="stat-card">
                    <h3>Ground</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_classification_ground', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Unclassified</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_classification_unclassified', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Low Vegetation</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_classification_low_vegetation', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Medium Vegetation</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_classification_medium_vegetation', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>High Vegetation</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_classification_high_vegetation', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Building</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_classification_building', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Water</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_classification_water', 0))}</div>
                </div>
                <div class="stat-card">
                    <h3>Noise</h3>
                    <div class="stat-value">{format_number(aggregate.get('total_classification_noise', 0))}</div>
                </div>
            </div>
            
            <h2 class="section-title">🎯 Scan Angle Information</h2>
            <div class="statistics">
                <div class="stat-card">
                    <h3>Minimum Angle</h3>
                    <div class="stat-value">{aggregate.get('scan_angle_global_min', 0):.2f}°</div>
                </div>
                <div class="stat-card">
                    <h3>Maximum Angle</h3>
                    <div class="stat-value">{aggregate.get('scan_angle_global_max', 0):.2f}°</div>
                </div>
            </div>
            
            <div class="bounds-container">
                <div class="bounds-section">
                    <h4>🗺️ Geographic Bounds (All Files)</h4>
                    <p>X: <span class="bounds-highlight">{format_number(aggregate['overall_min_x'])}</span> to <span class="bounds-highlight">{format_number(aggregate['overall_max_x'])}</span> <span class="unit-label">({", ".join(sorted(crs_units)) if crs_units else "Unknown units"})</span></p>
                    <p>Y: <span class="bounds-highlight">{format_number(aggregate['overall_min_y'])}</span> to <span class="bounds-highlight">{format_number(aggregate['overall_max_y'])}</span> <span class="unit-label">({", ".join(sorted(crs_units)) if crs_units else "Unknown units"})</span></p>
                    <p>Z: <span class="bounds-highlight">{format_number(aggregate['overall_min_z'])}</span> to <span class="bounds-highlight">{format_number(aggregate['overall_max_z'])}</span> <span class="unit-label">({", ".join(sorted(crs_units)) if crs_units else "Unknown units"})</span></p>
                </div>
                <div class="bounds-section">
                    <h4>🌐 Coordinate Reference System</h4>
                    {f'<div class="crs-info"><strong>Units:</strong> {", ".join(sorted(crs_units)) if crs_units else "Unknown"}</div>' if crs_units else '<p style="color: #666; font-style: italic;">No coordinate system information available</p>'}
                    {f'<div class="crs-info" style="margin-top: 10px;"><strong>System:</strong><br>{list(crs_systems)[0] if len(crs_systems) == 1 else "Multiple systems detected"}</div>' if crs_systems else ""}
                    {f'<div class="crs-info" style="margin-top: 10px;"><strong>EPSG Code:</strong> {", ".join(sorted(crs_epsg_codes)) if crs_epsg_codes else "Not available"}</div>' if crs_epsg_codes else ""}
                    {f'<div class="crs-info" style="margin-top: 10px;"><strong>Vertical Datum:</strong> {", ".join(sorted(crs_vertical_datums)) if crs_vertical_datums else "Not available"}</div>' if crs_vertical_datums else ""}
                </div>
            </div>
            
            <h2 class="section-title">📄 Individual File Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Point Count</th>
                        <th>Returns<br/>(1st/2nd/3rd)</th>
                        <th>Ground<br/>Points</th>
                        <th>Vegetation<br/>Points</th>
                        <th>Water<br/>Points</th>
                        <th>Scan Angle<br/>Range</th>
                        <th>Density (pts/m²)</th>
                        <th>File Size (MB)</th>
                    </tr>
                </thead>
                <tbody>
                    {file_rows_html}
                </tbody>
            </table>
            
            <h2 class="section-title">📋 Detailed File Information</h2>
            {self._generate_details_content(results)}
        </div>
        
        <div class="footer">
            <p>Generated by LAS File Analysis Tool</p>
        </div>
    </div>
    
    <script>
        function toggleContent(btn) {{
            const fileSection = btn.closest('.file-section');
            const rawOutputContainer = fileSection.querySelector('.raw-output-container');
            
            if (rawOutputContainer) {{
                const isHidden = rawOutputContainer.style.display === 'none';
                rawOutputContainer.style.display = isHidden ? 'block' : 'none';
                btn.textContent = isHidden ? 'Hide Details' : 'Show Details';
            }}
        }}
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _parse_crs_name(self, crs_info: str) -> str:
        """
        Parse CRS info to extract the main coordinate system name from GTCitationGeoKey.
        
        Args:
            crs_info: Raw CRS information string
            
        Returns:
            Cleaned coordinate system name or None
        """
        if not crs_info:
            return None
            
        import re
        
        # Look for GTCitationGeoKey and extract the coordinate system name after it
        # Pattern: GTCitationGeoKey: [coordinate system name]
        pattern = r'GTCitationGeoKey:\s*([^|]+)'
        match = re.search(pattern, crs_info)
        
        if match:
            crs_name = match.group(1).strip()
            # Remove any trailing "|" or extra whitespace
            crs_name = crs_name.rstrip('|').strip()
            return crs_name
        
        # If no GTCitationGeoKey pattern found, return the CRS info as-is
        # (this handles coordinate-based detection results)
        return crs_info.strip()
    
    def _extract_epsg_from_crs_name(self, crs_name: str) -> str:
        """
        Extract EPSG code from CRS name.
        
        Args:
            crs_name: CRS name string
            
        Returns:
            EPSG code if found, empty string otherwise
        """
        if not crs_name:
            return ""
        
        import re
        
        # Look for EPSG code in the CRS name
        epsg_match = re.search(r'EPSG["\s]*["\s]*(\d+)', crs_name)
        if epsg_match:
            return epsg_match.group(1)
        
        # For Maine West (ftUS), we know the EPSG code is 6486
        if 'Maine West (ftUS)' in crs_name:
            return "6486"
        
        return ""
    
    def _extract_vertical_datum_from_crs_name(self, crs_name: str) -> str:
        """
        Extract vertical datum from CRS name.
        
        Args:
            crs_name: CRS name string
            
        Returns:
            Vertical datum if found, empty string otherwise
        """
        if not crs_name:
            return ""
        
        import re
        
        # Look for vertical datum patterns
        vertical_patterns = [
            r'NAVD88[^"]*',
            r'NGVD29[^"]*',
            r'EGM96[^"]*',
            r'EGM2008[^"]*',
            r'MSL[^"]*',
            r'height[^"]*'
        ]
        
        for pattern in vertical_patterns:
            match = re.search(pattern, crs_name, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return ""
    
    def _generate_details_content(self, results: List[LASFileInfo]) -> str:
        """Generate the detailed file information content."""
        
        import logging
        logger = logging.getLogger("LASAnalysis")
        
        # Create file details sections
        file_sections = []
        for idx, result in enumerate(results, 1):
            logger.debug(f"\nDetails for: {result.filename}")
            logger.debug(f"  acreage_detailed: {result.acreage_detailed:.4f}")
            if result.error:
                file_sections.append(f"""
                <div class="file-section">
                    <div class="file-header">
                        <h3 class="file-title">{idx}. {result.filename}</h3>
                        <span class="error-badge">Error</span>
                    </div>
                    <div class="file-content">
                        <div class="error-box">
                            <strong>Error:</strong> {result.error}
                        </div>
                    </div>
                </div>
                """)
            else:
                raw_output_escaped = result.raw_output.replace('<', '&lt;').replace('>', '&gt;')
                file_sections.append(f"""
                <div class="file-section">
                    <div class="file-header">
                        <h3 class="file-title">{idx}. {result.filename}</h3>
                        <button class="toggle-btn" onclick="toggleContent(this)">Show Details</button>
                    </div>
                    <div class="file-content">
                        <div class="file-stats">
                            <div class="stat-item">
                                <span class="stat-label">Point Count:</span>
                                <span class="stat-val">{result.point_count:,}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Point Density:</span>
                                <span class="stat-val">{result.point_density:.2f} pts/m²</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Acreage (Convex Hull):</span>
                                <span class="stat-val" title="Actual footprint based on point distribution">{result.acreage_detailed:.2f} acres</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">File Size:</span>
                                <span class="stat-val">{result.file_size_mb:.2f} MB</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Processing Time:</span>
                                <span class="stat-val">{result.processing_time:.2f} sec</span>
                            </div>
                        </div>
                        <div class="bounds-box">
                            <strong>Bounds:</strong><br>
                            X: {result.min_x:.2f} to {result.max_x:.2f}<br>
                            Y: {result.min_y:.2f} to {result.max_y:.2f}<br>
                            Z: {result.min_z:.2f} to {result.max_z:.2f}
                        </div>
                        <div class="raw-output-container" style="display: none;">
                            <strong>Complete Python Analysis Output:</strong>
                            <pre class="raw-output">{raw_output_escaped}</pre>
                        </div>
                    </div>
                </div>
                """)
        
        return '\n'.join(file_sections)
    
