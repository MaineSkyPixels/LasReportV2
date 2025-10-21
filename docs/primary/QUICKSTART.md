# Quick Start Guide - LAS File Analysis Tool

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.12 or later** installed
   - Download from: https://www.python.org/downloads/

2. **lasinfo installed and in system PATH**
   - Download LAStools from: https://rapidlasso.com/lastools/
   - Or install from GitHub: https://github.com/LAStools/LAStools
   - Verify installation by running: `lasinfo` in PowerShell/Command Prompt
   - If you see usage information, it's properly installed

## Running the Application

### Step 1: Open PowerShell/Command Prompt
Navigate to the directory containing the LAS analysis tool files.

### Step 2: Run the Application
```powershell
python main.py
```

A window will appear with the LAS File Analysis Tool interface.

### Step 3: Select Directory
1. Click the "📁 Browse" button
2. Select the directory containing your LAS files
3. The tool will recursively scan all subdirectories for `.las` files

### Step 4: Start Scan
1. Click "▶ Start Scan" to begin processing
2. Watch the progress bar and status updates
3. The tool will:
   - Find all LAS files
   - Run lasinfo on each file (in parallel)
   - Parse and aggregate the results
   - Generate two HTML reports

### Step 5: View Reports
Two HTML reports are created in your LAS directory:

- **summary.html** - Professional overview with:
  - Total files and points
  - Average point density
  - Overall geographic bounds
  - Detailed table of each file

- **lasdetails.html** - Complete technical details for each file:
  - Full lasinfo output for inspection
  - Collapsible sections for easy navigation
  - All point cloud metrics

## Output Files

Reports are generated in the same directory as your LAS files:
```
Your LAS Directory/
├── file1.las
├── file2.las
├── summary.html          ← Open this in your browser
├── lasdetails.html       ← Open this for detailed info
└── .las_analysis_logs/   ← Detailed logs (hidden folder)
    └── scan_YYYYMMDD_HHMMSS.log
```

## Logging

Detailed logs are automatically created in a hidden folder:
- Location: `.las_analysis_logs/` in your scanned directory
- Files: `scan_YYYYMMDD_HHMMSS.log`
- Contains: All operations, lasinfo output, metrics, and any errors

## Features

### Multithreaded Processing
- By default processes 4 LAS files in parallel
- Significantly faster than sequential processing
- Automatically scales with your system capabilities

### Comprehensive Metrics Extracted
- Point count
- Point density (points/m²)
- Geographic bounds (X, Y, Z min/max)
- Scale factors
- Offset values
- CRS/EPSG information
- File size and processing time

### Professional Reports
- Modern, responsive HTML design
- Works on desktop and mobile
- Beautiful gradient styling
- Clear data visualization
- Error handling and status tracking

## Troubleshooting

### "lasinfo command not found" Error
**Problem**: Application cannot find lasinfo executable
**Solution**:
1. Verify lasinfo is installed
2. Check that lasinfo is in your system PATH:
   ```powershell
   Get-Command lasinfo
   ```
3. If not found, add LAStools bin directory to PATH:
   - Set System Environment Variable `PATH` to include LAStools directory
   - Restart PowerShell/Command Prompt after setting PATH

### No LAS Files Found
**Problem**: Directory selected but no files detected
**Solution**:
1. Ensure files have `.las` extension (case-insensitive)
2. Check that files are actually LAS format
3. Try selecting parent directory to enable recursive search

### Processing Takes a Long Time
**Problem**: Scan is running slowly
**Solution**:
- This is normal for large files or many files
- Can modify `max_workers` in `main.py` line ~86 to use more threads
- Default is 4 workers - increase to 8 or 12 for faster processing

### HTML Reports Don't Open
**Problem**: Can't open HTML files
**Solution**:
1. Right-click on `summary.html` → Open With → Choose your browser
2. Or drag and drop the file into your browser window
3. HTML files are standard web pages - any modern browser works

## Example Use Case

Scanning a directory with 10 LAS files:
1. GUI opens
2. User clicks Browse and selects `/data/lidar_survey/`
3. Tool finds 10 LAS files
4. Processes them in parallel (4 at a time)
5. Generates reports in ~30-60 seconds (depending on file size)
6. Two HTML reports appear in the directory
7. User opens `summary.html` to see overview
8. User opens `lasdetails.html` to inspect individual file metrics

## Advanced Configuration

### Adjusting Thread Count
Edit `main.py` line 86:
```python
processor = LASProcessor(max_workers=4)  # Change 4 to desired number
```

Higher values = faster but uses more system resources
Recommended: (number of CPU cores - 1)

### Customizing HTML Styling
Edit `report_generator.py` to modify CSS in:
- `_generate_summary_html()` method (summary.html styling)
- `_generate_details_html()` method (details.html styling)

## Support

For issues or questions:
1. Check the logs in `.las_analysis_logs/` directory
2. Review the detailed error messages in the GUI
3. Verify lasinfo is working: `lasinfo --version` in PowerShell
4. Ensure Python 3.12+ is being used: `python --version`

## License

This tool is provided as-is for analyzing LAS files.
