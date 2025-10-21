# Getting Started with LAS File Analysis Tool

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [First Run](#first-run)
4. [Using the Application](#using-the-application)
5. [Understanding Reports](#understanding-reports)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Prerequisites

Before you begin, ensure you have:

### 1. Python 3.12 or Later
```powershell
# Check Python version
python --version

# Should output: Python 3.12.x or later
```

If Python is not installed:
- Download from: https://www.python.org/downloads/
- During installation, CHECK "Add Python to PATH"

### 2. lasinfo Command-Line Tool
lasinfo is part of LAStools and must be installed separately.

```powershell
# Check if lasinfo is available
lasinfo
```

**Installation Options:**

**Option A: Install Full LAStools (Recommended)**
1. Download from: https://rapidlasso.com/lastools/
2. Extract to a location (e.g., `C:\LAStools`)
3. Add to Windows PATH:
   - Open Settings → System → About → Advanced system settings
   - Click "Environment Variables"
   - Under System variables, edit "Path"
   - Add: `C:\LAStools\bin` (or your installation path)
   - Restart PowerShell/Command Prompt

**Option B: GitHub Installation**
1. Clone: `git clone https://github.com/LAStools/LAStools.git`
2. Build and install (requires build tools)
3. Add to PATH

**Verify Installation:**
```powershell
# After installation, should display usage information
lasinfo
```

---

## Installation

### Step 1: Download/Clone the Tool

Option A: Download ZIP
- Download the repository as ZIP
- Extract to desired location

Option B: Clone with Git
```powershell
git clone <repository-url>
cd LasReport
```

### Step 2: Verify Project Files

You should see these files:
```
LasReport/
├── main.py
├── gui.py
├── scanner.py
├── processor.py
├── report_generator.py
├── requirements.txt
├── run.bat                (Windows convenience script)
├── README.md
├── QUICKSTART.md
├── ARCHITECTURE.md
└── SampleLAS/            (Test files)
```

### Step 3: No Additional Dependencies!

This tool uses only Python's standard library. No `pip install` needed!

---

## First Run

### Windows Users - Easy Method

Simply double-click:
```
run.bat
```

A window will open with the LAS File Analysis Tool GUI.

### Command Line Method

```powershell
cd C:\path\to\LasReport
python main.py
```

### What You Should See

✓ A window titled "LAS File Analysis Tool"
✓ Directory selection section with Browse button
✓ Progress bar and status area
✓ Start Scan, Cancel, and Exit buttons

---

## Using the Application

### Basic Workflow

#### Step 1: Select a Directory
```
1. Click "📁 Browse" button
2. Navigate to folder containing .las files
3. Click "Select Folder"
4. Folder path appears in the window
```

You can select:
- Directory with LAS files directly
- Parent directory (will scan recursively)
- Empty directory (displays "No LAS files found")

#### Step 2: Start Scanning
```
1. Click "▶ Start Scan"
2. Watch progress bar fill (0% → 100%)
3. Status text shows:
   - Found X LAS file(s)
   - Processing: 1/X, 2/X, etc.
   - ✓ File processing completed
   - ✓ Reports generated
```

#### Step 3: View Reports

When scan completes, two reports appear in your LAS directory:

**summary.html** (Overview)
- Open in your web browser
- Shows total statistics
- Lists all files with metrics

**lasdetails.html** (Technical Details)
- Open in your web browser
- Individual file information
- Complete lasinfo output
- Click "Show Details" to expand each file

### Example: Test with Sample Files

The project includes sample LAS files for testing:

```
1. Click "📁 Browse"
2. Select: LasReport\SampleLAS
3. Click "▶ Start Scan"
4. Watch it process 9 test files
5. Open generated reports:
   - SampleLAS\summary.html
   - SampleLAS\lasdetails.html
```

---

## Understanding Reports

### summary.html

**Header Section**
- Title: "LAS File Analysis Report"
- Subtitle: "Comprehensive LiDAR Point Cloud Analysis"

**Scan Information**
- Scan Date/Time (when report was generated)
- Output Directory (where reports are saved)
- Files Analyzed (successful count)
- Failed Files (if any)

**Summary Statistics (Colorful Cards)**
```
Total Files      →  Number of LAS files scanned
Total Points     →  All points across all files
Avg Density      →  Average points per square meter
Total Data Size  →  Combined file size in MB
```

**Geographic Bounds**
```
X: min to max
Y: min to max
Z: min to max
```

**Individual File Details (Table)**
```
| Filename | Point Count | Density | File Size | Bounds Info |
├──────────┼─────────────┼─────────┼───────────┼─────────────┤
| file1.las | 1,234,567   | 8.5     | 12.34 MB  | ...bounds...|
| file2.las | 2,345,678   | 7.2     | 23.45 MB  | ...bounds...|
```

### lasdetails.html

**File Sections**
- One section per LAS file
- Click "Show Details" to expand
- Displays:
  - Point count
  - Point density
  - File size
  - Processing time
  - Geographic bounds
  - Raw lasinfo output

**Raw lasinfo Output**
- Complete technical information from lasinfo
- Shows in code/monospace font
- Includes all LAS metadata

**Error Handling**
- Failed files shown with red badge
- Error message displayed
- Doesn't interrupt report viewing

---

## Troubleshooting

### Issue: "lasinfo command not found"

**Error Message:**
```
lasinfo command not found - ensure it's in PATH
```

**Solutions:**
1. Verify lasinfo is installed
2. Check PATH setting:
   ```powershell
   Get-Command lasinfo
   ```
3. If not found, add LAStools to PATH:
   - System Settings → Environment Variables
   - Add LAStools `bin` directory to PATH
   - Restart PowerShell

### Issue: "No LAS files found"

**Possible Causes:**
- Folder contains no .las files
- Files are in subdirectories (need to select parent)
- Files have different extension

**Solutions:**
1. Verify file extensions: `.las` or `.LAS`
2. Check file is actually LAS format: `lasinfo filename.las`
3. Select parent directory for recursive search
4. Copy files to test directory

### Issue: Processing Takes Very Long

**Normal Behavior:**
- Small files: 1-5 seconds
- Medium files: 5-15 seconds
- Large files: 15-60+ seconds

**To Speed Up:**
1. Edit `main.py` line 86:
   ```python
   processor = LASProcessor(max_workers=8)  # Increase from 4
   ```
2. Increase depends on CPU cores

### Issue: HTML Reports Don't Open

**Solutions:**
1. Double-click the HTML file
2. Right-click → Open With → Choose browser
3. Drag file into browser window
4. Check file exists in scan directory

### Issue: Application Crashes

**Steps to Debug:**
1. Check logs in `.las_analysis_logs/` directory
2. Review error message in GUI
3. Try sample files first: `SampleLAS` folder
4. Verify Python 3.12+ installed

---

## FAQ

### Q: Can I cancel a scan?
**A:** Yes! Click the "⏹ Cancel" button during processing. Reports won't be generated.

### Q: Do I need to install any Python packages?
**A:** No! The tool uses only Python's standard library.

### Q: Can I modify the HTML reports?
**A:** Yes! Edit the CSS in `report_generator.py` for styling changes.

### Q: How many files can it process?
**A:** Theoretically unlimited. Practical limit depends on:
- Available disk space for LAS files
- System memory (minimal usage)
- Processing time tolerance

### Q: Can I run without the GUI?
**A:** Currently no, but it could be added. See `ARCHITECTURE.md` for enhancement ideas.

### Q: Where are the logs saved?
**A:** In `.las_analysis_logs/` subfolder of scanned directory.
- Hidden folder (starts with dot)
- File format: `scan_YYYYMMDD_HHMMSS.log`

### Q: What's the difference between summary and details reports?
**A:** 
- **summary.html**: Overview, aggregate stats, table view
- **lasdetails.html**: Per-file details, complete technical info

### Q: Can I open reports on Mac/Linux?
**A:** Yes! Reports are standard HTML5, work in any browser.

### Q: How do I increase processing speed?
**A:** 
1. Increase thread count (edit `main.py`)
2. Use faster storage (SSD vs HDD)
3. Ensure lasinfo is accessible (not over network)

### Q: Can I customize report appearance?
**A:** Yes! Edit CSS in `report_generator.py`:
- Colors: Search for `#667eea` or `#764ba2`
- Fonts: Look for `Segoe UI` declarations
- Spacing: Modify padding/margin values

### Q: Is my data safe?
**A:** Yes!
- No data sent anywhere
- Logs stored locally
- HTML reports are static files
- No network access required

### Q: Can I process multiple directories?
**A:** Currently one at a time. See `ARCHITECTURE.md` for future enhancements.

### Q: What happens if a file is corrupted?
**A:** Error is shown in reports. Processing continues for other files.

---

## Tips & Tricks

### Batch Processing Multiple Directories
Run the tool separately for each directory:
```powershell
python main.py
# Scan directory 1
# Then run again
python main.py
# Scan directory 2
```

### Accessing Logs
```powershell
# View latest log
Get-Content .las_analysis_logs\scan_*.log | tail -50

# Open in text editor
notepad .las_analysis_logs\scan_*.log
```

### Customizing Thread Count
For systems with many cores:
```python
# Edit main.py line 86
processor = LASProcessor(max_workers=16)  # Match your CPU cores
```

### Creating Shortcuts
**Windows:**
1. Right-click `run.bat`
2. Send To → Desktop (create shortcut)
3. Double-click shortcut to run

---

## Next Steps

1. **Test with Sample Files**
   - Run `python main.py`
   - Select `SampleLAS` folder
   - Review generated reports

2. **Process Your Files**
   - Select directory with your LAS files
   - Review generated reports
   - Check logs if needed

3. **Customize (Optional)**
   - Edit report styling
   - Adjust thread count
   - Modify logging

4. **Refer to Documentation**
   - `README.md` - Full overview
   - `QUICKSTART.md` - Detailed guide
   - `ARCHITECTURE.md` - Technical details

---

## Support & Issues

For problems:
1. Check this guide's Troubleshooting section
2. Review logs in `.las_analysis_logs/`
3. Read `README.md` and `QUICKSTART.md`
4. Verify prerequisites installed correctly

---

**Ready to get started? Run `python main.py` now!** 🚀
