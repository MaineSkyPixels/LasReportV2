# TestCodeData Folder

This folder contains testing, debugging, and utility scripts used during development and testing of the LAS Report Tool.

## 📁 Contents

### 🧪 Testing Scripts
- **`test_python_processor.py`** - Tests the Python-only LAS processor functionality
- **`test_report_generation.py`** - Tests HTML report generation with coordinate system information
- **`test_crs_collection.py`** - Tests CRS information collection and parsing logic

### 🐛 Debugging Scripts
- **`debug_crs_extraction.py`** - Debugs CRS extraction from LAS file VLRs
- **`debug_crs.py`** - General CRS debugging utilities

### 🔧 Utility Scripts
- **`dump_las_header_simple.py`** - Dumps all LAS header information to text files
- **`dump_las_header.py`** - Alternative LAS header dumping utility

### 📦 Backup Files
- **`processor_python_only_broken.py`** - Backup of processor with syntax errors (for reference)
- **`processor_python_only_fixed.py`** - Backup of fixed processor version

### 📄 Generated Files
- **`cloud5_las_header_dump_*.txt`** - Generated LAS header dump files with timestamps

## 🚀 Usage

These scripts are primarily for development and testing purposes. To run them:

```bash
# From the PythonOnly directory
cd TestCodeData
python test_python_processor.py
python debug_crs_extraction.py
python dump_las_header_simple.py
```

## 📝 Notes

- These files are not part of the main application
- They were used during development to test and debug functionality
- The header dump files show the complete LAS file metadata structure
- Test scripts validate the Python-only processing approach

## 🔄 Maintenance

When adding new test/debug scripts:
1. Place them in this folder
2. Update this README.md file
3. Update the main project documentation if needed

---

**Last Updated:** October 21, 2025  
**Purpose:** Development testing and debugging utilities
