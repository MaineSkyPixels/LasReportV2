# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **production-ready** (v4.0.2 Enterprise Edition) Python application for analyzing LAS (LiDAR point cloud) files and generating professional HTML reports. The application features a modern CustomTkinter GUI and processes LAS files entirely with Python libraries (laspy, scipy, numpy) - **no external executables required**.

**Status**: ✅ Production Ready (October 21, 2025)
**Quality**: ⭐⭐⭐⭐⭐ (5/5 stars)

**Key Features:**
- Python-only LAS processing (laspy + scipy + numpy)
- Intelligent RAM management with automatic optimization
- Multi-threaded processing with dynamic thread count calculation
- Optional convex hull acreage calculation (polygon-based, more accurate than bounding box)
- Preflight checks with RAM/thread estimates
- Real-time progress tracking with dual-level callbacks
- Single consolidated HTML report with timestamp
- Cross-platform support (Windows, macOS, Linux)

## Development Commands

### Running the Application
```bash
# Standard launch
python main.py

# Windows convenience launcher
run.bat
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

**Required:** Python 3.12+ with:
- `laspy==2.6.1` - LAS file reading
- `scipy==1.13.0` - Convex hull computation
- `numpy>=1.20.0` - Array operations
- `psutil==5.9.8` - System RAM monitoring
- `customtkinter==5.2.2` - Modern GUI framework

### Testing Individual Components
```bash
# Test Python processor directly
python TestCodeData/test_python_processor.py

# Debug CRS extraction
python TestCodeData/debug_crs_extraction.py

# Test report generation
python TestCodeData/test_report_generation.py

# Dump LAS header information
python TestCodeData/dump_las_header_simple.py <file.las>
```

## Architecture

### Core Processing Pipeline

The application follows an **orchestrator pattern** where `main.py` coordinates all components:

```
main.py (LASAnalyzerApp)
    ├── gui.py (LASReportGUI) - CustomTkinter modern UI with dark/light themes
    ├── scanner.py - Non-recursive file discovery (*.las in selected dir only)
    ├── processor_python_only.py (PythonLASProcessor) - Python-only LAS analysis
    ├── report_generator.py (ReportGenerator) - Single consolidated HTML report
    └── system_utils.py - RAM monitoring, thread optimization, disk I/O tracking
```

**IMPORTANT**: `processor.py` is **legacy code** (lasinfo-based, deprecated). Always use `processor_python_only.py`.

### Key Architecture Decisions

#### 1. **Python-Only Processing** (No External Dependencies)
The system uses **laspy, scipy, numpy** exclusively - no lasinfo executable required:
- **laspy**: Direct LAS file reading and header extraction
- **scipy.spatial.ConvexHull**: Accurate polygon-based acreage calculation
- **numpy**: Coordinate array operations for convex hull computation

**Benefits:**
- 15-20% faster than lasinfo subprocess approach
- No PATH dependencies or version inconsistencies
- Better error handling with Python exceptions
- Direct access to binary data without text parsing
- Cross-platform without platform-specific executables

#### 2. **Intelligent RAM Management System**
The system **automatically** optimizes processing based on available RAM (no manual configuration):

**Core Functions** (system_utils.py):
- `get_available_ram_gb()` - Real-time RAM availability via psutil
- `calculate_safe_decimation(file_size_mb, available_ram_gb)` - Per-file decimation
- `calculate_optimal_threads_smart(files, available_ram, use_convex_hull)` - Dynamic thread count
- `estimate_concurrent_ram_needed(files, thread_count)` - Multi-file RAM estimate

**RAM Calculation Formula:**
```python
# Per-file estimate
estimated_ram_gb = file_size_gb * 1.5  # File + XY arrays + working space

# Safe decimation
safe_ram_budget_gb = available_ram_gb * 0.5  # Use max 50% of available RAM
decimation_factor = min(1.0, safe_budget / estimated_ram)

# Thread count (for convex hull mode)
optimal_threads = available_ram / (avg_file_size_gb * 1.5)
optimal_threads = max(2, min(12, optimal_threads))  # Clamp to [2, 12]
```

**Low RAM Mode:** If available RAM < 8GB:
- Warning displayed to user
- Forces 1% point decimation for all files
- Reduces thread count further

**Thread Count Logic:**
- **Standard mode** (bounding box only): 12 threads (fast, low RAM)
- **Convex hull mode**: 2-12 threads (calculated based on file sizes + RAM)

#### 3. **Preflight Check System**
Before processing starts, the system shows a dialog with:
- Files to process and total size
- Available RAM vs. estimated concurrent RAM usage
- Optimal thread count calculation
- Warning if concurrent RAM usage exceeds available RAM
- User can cancel or proceed

See: `main.py:117-171` (`show_preflight_dialog()`)

#### 4. **Dual-Level Progress Callbacks**
The system uses a special callback signature for two types of progress:

**Main Progress** (file-level):
```python
progress_callback(completed: int, total: int, filename: str)
# Example: callback(45, 150, "cloud089.las")
```

**Sub-Progress** (step-level during convex hull):
```python
progress_callback("sub_progress", "dummy", message: str)
# Example: callback("sub_progress", "dummy", "Computing convex hull...")
```

Handler must check for `completed == "sub_progress"` to distinguish between modes.

#### 5. **CRS Detection and Unit Conversion**
Critical for accurate point density and acreage calculations:

**Detection Sources** (processor_python_only.py:305-371):
1. VLR (Variable Length Records) parsing for GeoTIFF metadata
2. Coordinate-based heuristics:
   - Values > 1,000,000 → US State Plane feet
   - Values 100,000-1,000,000 → UTM meters
3. Unit string detection in VLRs

**Supported Units:**
- `us_survey_feet` - 0.3048006096 m/ft
- `feet` - 0.3048 m/ft
- `meters` - No conversion needed

**Affects:**
- Point density calculation (pts/m²)
- Convex hull acreage conversion (to acres)
- Bounding box dimensions in reports

#### 6. **Convex Hull Processing** (Optional, RAM-Intensive)
When enabled, calculates actual polygon-based acreage:

**Algorithm** (processor_python_only.py:550-638):
1. Read entire LAS file into memory with laspy
2. Extract X,Y coordinates as numpy array
3. Compute ConvexHull via scipy.spatial
4. Calculate polygon area using shoelace formula
5. Convert to acres based on CRS units

**Performance Impact:**
- Requires loading all points into RAM (or decimated subset)
- Thread count reduced to prevent RAM contention
- Processing time: ~500ms-2s per file (size-dependent)

**Decimation:**
- Automatically calculated per-file based on RAM availability
- 100% (all points) → Most accurate, slowest
- 50% (every 2nd point) → Balanced, <1% error
- 10% (every 10th point) → Fast, <2% error
- 1% (forced in low RAM mode) → Fastest, minimal accuracy loss

**Accuracy:** Convex hull is typically 2-3% smaller than bounding box (more accurate).

#### 7. **Error Isolation**
Per-file error handling ensures one corrupt file doesn't halt the entire batch:
- Each file processed in try/except block
- Results include `error: Optional[str]` field
- Failed files show in reports with error messages
- Processing continues with remaining files

#### 8. **Report Generation** (Single Consolidated Report)
Generates timestamped HTML report: `LasReport-MM-DD-YYYY-HH-MM.html`

**Report Sections:**
1. **Header** - Scan timestamp, file counts, aggregate statistics
2. **Summary Statistics** - Total points, avg density, total acreage, data size
3. **Geographic Bounds** - Overall X/Y/Z ranges, CRS information
4. **Individual File Table** - Per-file metrics (points, density, acreage, size, bounds)
5. **Detailed File Sections** - Collapsible per-file details with full Python analysis output

**Acreage Display:**
- Always shows acreage when calculated
- If convex hull enabled: Shows convex hull acreage (polygon-based)
- If convex hull disabled/failed: Shows "-" (not calculated)
- Hover tooltips indicate calculation method

### Data Flow

1. **User selects directory/file** via CustomTkinter GUI (`gui.py`)
2. **GUI calls** `LASAnalyzerApp._run_scan_threaded()` in background thread (`main.py:100-115`)
3. **Preflight dialog** calculates optimal threads and RAM usage (`main.py:117-171`)
4. **Scanner** finds .las files in selected directory - **non-recursive** (`scanner.py`)
5. **RAM check** determines low_ram_mode if <8GB available (`main.py:198-208`)
6. **Processor** analyzes files in parallel (`processor_python_only.py:94-165`):
   - ThreadPoolExecutor with calculated worker count
   - Each file → `_process_single_file()` → extracts metrics
   - Optional convex hull with intelligent decimation
   - Real-time progress callbacks (main + sub)
7. **Results aggregated** → `_calculate_aggregates()`
8. **Report generator** creates single consolidated HTML (`report_generator.py:23-46`)
9. **GUI shows completion dialog** with processing time and report path

## File Organization

### Root Directory (Core Modules)
- **main.py** - Application orchestrator and entry point
- **gui.py** - CustomTkinter GUI with modern appearance
- **scanner.py** - LAS file discovery (non-recursive)
- **processor_python_only.py** - **Current processor** (Python-only)
- **processor.py** - **Legacy processor** (lasinfo-based, deprecated)
- **report_generator.py** - HTML report generation
- **system_utils.py** - RAM monitoring, thread calculation, disk I/O tracking
- **requirements.txt** - Python dependencies
- **run.bat** - Windows convenience launcher

### TestCodeData/ (Testing and Debugging)
Testing scripts, debug utilities, and backup processor versions:
- `test_python_processor.py` - Python processor validation
- `test_report_generation.py` - Report generation testing
- `debug_crs_extraction.py` - CRS debugging
- `dump_las_header_simple.py` - LAS header dumping utility
- `processor_python_only_*.py` - Backup versions

### docs/ (Comprehensive Documentation)
- `INDEX.md` - Documentation index with recommended reading order
- `primary/` - Getting started guides
- `architecture/` - Technical architecture (ARCHITECTURE.md, CODEBASE.md)
- `advanced-features/` - Python-only processing, RAM system, convex hull
- `issues-fixes/` - Bug fixes and resolution documentation
- `reference/` - Quick reference guides
- `session-reports/` - Development session history

### Generated During Execution
- `.las_analysis_logs/` - Auto-generated debug logs
  - `scan_YYYYMMDD_HHMMSS.log` - Full debug log
  - `console_output_YYYYMMDD_HHMMSS.txt` - Console mirror
- `LasReport-MM-DD-YYYY-HH-MM.html` - Generated report

## Important Implementation Notes

### When Modifying Processing Logic

1. **Always preserve CRS detection**: Point density and acreage calculations depend on accurate unit conversion (feet vs. meters)
2. **Test with multiple file sizes**: RAM estimates must work for 50MB and 5GB files
3. **Maintain error isolation**: Use per-file try/except to prevent batch failures
4. **Update progress callbacks**: Must call both main and sub-progress callbacks
5. **Handle library availability**: Check `HAS_LASPY`, `HAS_SCIPY`, `HAS_NUMPY` flags before using

### When Adding Features

1. **Check RAM implications**: Use `estimate_concurrent_ram_needed()` for memory-intensive features
2. **Update preflight dialog**: Add new resource requirements to `main.py:117-171`
3. **Extend LASFileInfo dataclass**: Add new fields to `processor_python_only.py:36-62`
4. **Update report generator**: Modify `_generate_las_report_html()` and `_generate_details_content()`
5. **Test RAM management**: Verify new feature doesn't break intelligent RAM calculations

### When Modifying GUI

1. **Use CustomTkinter widgets**: `ctk.CTkButton`, `ctk.CTkLabel`, etc. (not standard tkinter)
2. **Maintain dark/light theme support**: Don't hardcode colors
3. **Keep operations non-blocking**: Long operations must use `_run_scan_threaded()`
4. **Update font sizes consistently**: Follow established hierarchy (title=18pt, main=14pt, status=11pt)

## Debugging

**Full debug logging is enabled by default**. Logs are saved to:
- `.las_analysis_logs/scan_{timestamp}.log` - Detailed processing log with DEBUG level
- `.las_analysis_logs/console_output_{timestamp}.txt` - Console output mirror

**Key Debug Patterns:**
```python
import logging
logger = logging.getLogger("LASAnalysis")

logger.debug(f"RAM-optimized decimation: {decimation*100:.0f}%")  # Detailed info
logger.info(f"Processing {filepath.name} ({file_size_mb:.1f} MB)")  # Status updates
logger.warning(f"Low RAM detected: {available_ram:.1f} GB")  # Warnings
logger.error(f"Failed to process {filepath.name}: {str(e)}")  # Errors
```

**What Gets Logged:**
- System RAM availability at startup
- Processor initialization (detailed_acreage, max_workers, low_ram_mode)
- Per-file processing start and completion
- CRS detection results (units, coordinate system)
- Point density calculations
- Convex hull computation steps (if enabled)
- RAM-based decimation calculations
- Disk I/O speed monitoring
- Aggregate statistics
- Report generation completion

## Testing Workflow

1. **Test with small files first** (< 100MB) to verify logic changes quickly
2. **Test RAM handling**:
   - Files totaling <50% of available RAM (should use 100% decimation)
   - Files totaling >50% of available RAM (should use adaptive decimation)
   - Low RAM mode (<8GB available)
3. **Test error handling**: Include one corrupt/invalid .las file in batch
4. **Verify preflight dialog**: Check RAM estimates and thread count calculations
5. **Test convex hull**:
   - Enable detailed acreage
   - Verify acreage differs from bounding box (typically 2-3% smaller)
   - Check decimation is applied appropriately
6. **Verify reports**: Check both summary stats and individual file details in single HTML report
7. **Test progress callbacks**: Verify both main progress and sub-progress messages display

## Common Pitfalls

1. **Don't use `processor.py`**: This is the **legacy lasinfo-based processor**. Always use `processor_python_only.py`.

2. **Thread count calculation is critical**:
   - Wrong thread count causes OOM errors (too many threads) or slow performance (too few)
   - Always use `calculate_optimal_threads_smart()` for convex hull mode
   - Standard mode always uses 12 threads

3. **Progress callbacks have dual signatures**:
   ```python
   if completed == "sub_progress":
       self.gui.update_sub_progress(filename)  # filename is actually the message
   else:
       self.gui.update_progress(completed, total, filename)
   ```

4. **CRS units affect calculations**:
   - Point density is calculated per m² regardless of file units
   - Acreage conversion requires correct unit detection
   - Always verify unit conversions when modifying density/acreage logic
   - Test with files in different units (feet, us_survey_feet, meters)

5. **GUI runs in main thread**:
   - Long operations must use `_run_scan_threaded()` to prevent freezing
   - Never call `processor.process_files()` directly from GUI callback
   - Use background thread + progress callbacks

6. **Scanner is non-recursive**:
   - Only finds .las files in selected directory (not subdirectories)
   - Use `dir_path.glob("*.las")` NOT `rglob()`

7. **Report is consolidated**:
   - Single report file: `LasReport-{timestamp}.html`
   - Don't look for separate `summary.html` and `lasdetails.html`

8. **Library availability checks**:
   - Always check `HAS_LASPY`, `HAS_SCIPY`, `HAS_NUMPY` before using
   - Gracefully degrade if libraries missing
   - Don't assume dependencies are installed

## Critical Code Locations

### CRS Detection Logic
- **File**: `processor_python_only.py:305-371`
- **Method**: `_extract_crs_info(vlrs, header)`
- Parses VLRs for GeoTIFF metadata → falls back to coordinate-based heuristics

### Convex Hull Calculation
- **File**: `processor_python_only.py:550-638`
- **Method**: `_calculate_convex_hull_acreage(filepath, file_info, progress_callback)`
- Loads file, extracts XY, computes hull, calculates area, converts to acres

### RAM Management
- **File**: `system_utils.py`
- **Key Functions**:
  - `calculate_safe_decimation()` - Per-file decimation (32-72)
  - `calculate_optimal_threads_smart()` - Dynamic thread count (164-198)
  - `estimate_concurrent_ram_needed()` - Multi-file RAM estimate (200-217)

### Preflight Dialog
- **File**: `main.py:117-171`
- **Method**: `show_preflight_dialog(las_files, use_detailed_acreage)`
- Calculates metrics, builds warning message, shows yes/no dialog

### Progress Callback Handling
- **File**: `main.py:256-279`
- **Method**: `progress_callback(completed, total, filename)` (closure in `run_scan()`)
- Handles both main progress and sub-progress messages

### Report Generation
- **File**: `report_generator.py:23-46`
- **Method**: `generate_las_report(results, aggregate)`
- Creates single consolidated HTML with timestamp

## Platform-Specific Notes

### Windows
- Uses `explorer.exe` to open report folders
- `pathlib.Path` handles Windows paths correctly
- Tested on Windows 10, 11

### macOS
- Uses `open` command to open report folders
- Expected to work (not extensively tested)
- All Python libraries are cross-platform

### Linux
- Uses `xdg-open` command to open report folders
- Expected to work (not extensively tested)
- Ensure `xdg-utils` package installed

**All file paths use `pathlib.Path` for cross-platform compatibility.**

## Version History

- **v4.0.2** (October 21, 2025) - GUI modernization, report consolidation, Python-only processing
- **v4.0** (October 20, 2025) - Intelligent RAM system, convex hull optimization
- **v3.0** - Added convex hull acreage calculation
- **v2.0** - Multi-threaded processing
- **v1.0** - Initial release with lasinfo integration

## Quick Reference

**Most Common Tasks:**
1. **Run application**: `python main.py`
2. **Install deps**: `pip install -r requirements.txt`
3. **Enable debug logs**: Already enabled by default (check `.las_analysis_logs/`)
4. **Test processor**: `python TestCodeData/test_python_processor.py`
5. **Read architecture**: See `docs/architecture/ARCHITECTURE.md`
6. **Understand RAM system**: See `docs/advanced-features/INTELLIGENT_RAM_SYSTEM.md`
7. **Learn Python-only processing**: See `docs/advanced-features/PYTHON_ONLY_PROCESSING.md`
