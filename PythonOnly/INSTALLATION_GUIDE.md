# Installation Guide - LAS File Analysis Tool v5.0

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install customtkinter==5.2.2
pip install laspy==2.6.1
pip install scipy==1.13.0
pip install psutil==5.9.8
```

### 2. Run the Application
```bash
python main.py
```

Or on Windows:
```bash
run.bat
```

## What's New in v5.0

### 🎨 **Modern Professional Interface**
- **CustomTkinter**: Modern, professional appearance
- **Dark/Light Theme**: Toggle between themes
- **Professional Styling**: Rounded corners, smooth animations
- **Better Visual Hierarchy**: Clean, organized layout

### ⚡ **Enhanced Real-time Updates**
- **Fixed Threading**: Status updates every ~500ms during convex hull processing
- **Sub-progress Messages**: "Loading LAS file...", "Computing convex hull...", etc.
- **Better Feedback**: Real-time disk I/O speed and RAM usage

### 📊 **Improved Completion Dialog**
- **Statistics Display**: Comprehensive scan summary
- **Browser Integration**: One-click report opening
- **Processing Time**: Total scan duration
- **Professional Layout**: Clean statistics grid

### 🔍 **Non-Recursive Scanning**
- **Current Directory Only**: No longer scans subdirectories
- **Cleaner Results**: Only processes intended files

## System Requirements

- **Python**: 3.12+ (tested with 3.12.10)
- **RAM**: 8GB+ recommended (4GB minimum)
- **Storage**: 100MB for application + space for reports
- **OS**: Windows, macOS, Linux

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| customtkinter | 5.2.2 | Modern GUI framework |
| laspy | 2.6.1 | LAS file reading for convex hull |
| scipy | 1.13.0 | Convex hull computation |
| psutil | 5.9.8 | System monitoring (RAM, disk I/O) |

## Troubleshooting

### "ModuleNotFoundError: No module named 'customtkinter'"
```bash
pip install customtkinter==5.2.2
```

### "lasinfo command not found"
- Install LAStools from: https://rapidlasso.com/lastools/
- Ensure `lasinfo` is in your system PATH
- For large files (>2GB), install 64-bit version with `lasinfo64`

### GUI Not Appearing
- Check Python version: `python --version` (should be 3.12+)
- Try running: `python -c "import customtkinter; print('OK')"`

### Performance Issues
- Ensure 8GB+ RAM available
- Close other memory-intensive applications
- Use non-convex hull mode for faster processing

## Features Overview

### Core Functionality
- ✅ LAS file scanning and analysis
- ✅ Multithreaded processing (12 threads normal, 4 for convex hull)
- ✅ HTML report generation (summary + details)
- ✅ Real-time progress tracking
- ✅ Error handling and recovery

### Advanced Features
- ✅ Convex hull acreage calculation (optional)
- ✅ Intelligent RAM management
- ✅ 64-bit lasinfo support for large files
- ✅ CRS/EPSG detection
- ✅ Point density calculation
- ✅ Geographic bounds extraction

### User Interface
- ✅ Modern CustomTkinter interface
- ✅ Dark/light theme toggle
- ✅ Real-time status updates
- ✅ Professional completion dialog
- ✅ Browser integration
- ✅ File explorer integration

## Getting Started

1. **Select Directory**: Click "📁 Browse Directory" to select a folder with LAS files
2. **Choose Options**: Enable "Calculate detailed acreage" for convex hull processing
3. **Start Scan**: Click "▶️ Start Scan" to begin processing
4. **Monitor Progress**: Watch real-time updates and statistics
5. **View Results**: Click "🌐 Open Report in Browser" when complete

## Support

For issues or questions:
1. Check this installation guide
2. Review the documentation in `docs/` folder
3. Check debug logs in `.las_analysis_logs/` folder
4. Ensure all dependencies are installed correctly

---

**Version**: 5.0 - Modern Professional Edition  
**Last Updated**: December 19, 2024  
**Status**: ✅ Production Ready
