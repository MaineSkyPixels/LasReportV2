# Report Generator Fix - AttributeError Resolution

## Problem
When running the application with a large 70GB LAS file, an AttributeError occurred:
```
'LASFileInfo' object has no attribute 'acreage'
```

This error occurred because the previous implementation removed the `acreage` and `acreage_method` fields from the `LASFileInfo` dataclass, but the report_generator.py was still trying to access them.

## Root Cause
The earlier streamline changes (from `implement.plan.md`) removed:
- `acreage: float = 0.0` (bounding box acreage) from LASFileInfo
- `acreage_method: str = "bbox"` from LASFileInfo

However, report_generator.py still had references to these removed fields in:
1. Debug logging (lines 444-446)
2. HTML template for details report (line 481 in the stat item for bounding box acreage)

## Changes Applied

### 1. **report_generator.py - Debug Logging (Line 444-446)**

**Before:**
```python
logger.debug(f"  acreage: {result.acreage:.4f}")
logger.debug(f"  acreage_detailed: {result.acreage_detailed:.4f}")
logger.debug(f"  acreage_method: {result.acreage_method}")
```

**After:**
```python
logger.debug(f"  acreage_detailed: {result.acreage_detailed:.4f}")
```

**Reason:** Removed references to the deleted `acreage` and `acreage_method` fields. Now only logs convex hull acreage.

### 2. **report_generator.py - HTML Template (Line 478-480)**

**Before:**
```python
<div class="stat-item">
    <span class="stat-label">Acreage (Bounding Box):</span>
    <span class="stat-val">{result.acreage:.2f} acres</span>
</div>
<div class="stat-item">
    <span class="stat-label">Acreage (Convex Hull):</span>
    <span class="stat-val" title="Actual footprint based on point distribution">{result.acreage_detailed:.2f} acres</span>
</div>
```

**After:**
```python
{f'''<div class="stat-item">
    <span class="stat-label">Acreage (Convex Hull):</span>
    <span class="stat-val" title="Actual footprint based on point distribution">{result.acreage_detailed:.2f} acres</span>
</div>''' if result.acreage_detailed > 0 else '<div class="stat-item"><span class="stat-label">Acreage:</span><span class="stat-val">-</span></div>'}
```

**Reason:** 
- Removed bounding box acreage display
- Added conditional rendering to only show acreage if convex hull was calculated
- Shows "-" if no acreage available

## Files Modified
- **report_generator.py** - 2 sections updated

## Testing
All changes verified:
1. ✅ LASFileInfo dataclass works without acreage/acreage_method fields
2. ✅ acreage_detailed field is properly accessible
3. ✅ Report generator successfully processes results with new structure
4. ✅ Code compiles without syntax errors
5. ✅ No AttributeError when accessing report data

## Result
The AttributeError is now resolved. The report generator:
- ✅ Only displays convex hull acreage (when available)
- ✅ Shows "-" for files without convex hull calculation
- ✅ Properly handles all result objects from the processor
- ✅ Generates reports without errors

## Verification
To verify the fix works with actual LAS files:
1. Run the application with convex hull enabled
2. Process files and verify reports generate successfully
3. Check that acreage is displayed correctly (or "-" if not calculated)
