# Acreage Display Improvements

**Date:** October 21, 2025  
**Status:** ✅ Implemented

## Changes Made

### 1. Summary Statistics - Added Total Acreage Cards

**New stat cards at the top of summary report:**

- **Total Acreage (Bounding Box)** - Always displayed
  - Shows sum of all bounding box acreages
  - Labeled clearly as "Bounding Box"
  
- **Total Acreage (Convex Hull)** - Displayed when available
  - Shows sum of all convex hull acreages
  - Labeled clearly as "Convex Hull" with subtitle "(actual footprint)"
  - Only appears if convex hull calculation was used

### 2. Individual File Table - Clearer Labels

**Updated acreage column in file table:**

**Before:**
```
Acreage: 18.57 / 18.06
```

**After:**
```
Bbox: 18.57
Convex Hull: 18.06
```

- Each method now has a clear label
- Values are on separate lines for better readability
- Tooltip shows full explanation: "Bounding Box / Convex Hull (Actual Footprint)"

### 3. Details Report - Separate Stat Items

**Updated file statistics section:**

**Before:**
```
Acreage: 18.57 acres / 18.06
```

**After:**
- **Acreage (Bounding Box):** 18.57 acres
- **Acreage (Convex Hull):** 18.06 acres *(with tooltip: "Actual footprint based on point distribution")*

Each acreage type now has its own stat card for maximum clarity.

## Visual Layout

### Summary Report Statistics Grid

```
┌─────────────────┬─────────────────┬─────────────────┐
│  Total Files    │  Total Points   │ Avg Point Density│
│      1          │   18,712,360    │    248.99        │
└─────────────────┴─────────────────┴─────────────────┘

┌─────────────────┬─────────────────┬─────────────────┐
│ Total Data Size │Total Acreage    │Total Acreage    │
│   606.75 MB     │  (Bbox)         │(Convex Hull)    │
│                 │  18.57 acres    │18.06 acres      │
│                 │                 │(actual footprint)│
└─────────────────┴─────────────────┴─────────────────┘
```

### File Table

```
┌──────────┬───────┬─────────┬──────────────┐
│ Filename │ Points│ Density │   Acreage    │
├──────────┼───────┼─────────┼──────────────┤
│cloud5.las│18.7M  │ 248.99  │ Bbox: 18.57  │
│          │       │         │ Hull: 18.06  │
└──────────┴───────┴─────────┴──────────────┘
```

## Benefits

1. **Immediate Visibility** - Total acreage prominently displayed at top
2. **Clear Distinction** - No confusion between bounding box and convex hull
3. **Conditional Display** - Convex hull only shown when actually calculated
4. **Tooltips** - Hover for additional explanation
5. **Professional** - Clean, organized, easy to read

## Technical Implementation

### Calculation Logic
```python
# Calculate totals for both methods
total_bbox_acreage = sum(r.acreage for r in results if not r.error)
total_convex_hull_acreage = sum(
    r.acreage_detailed if r.acreage_detailed > 0 else r.acreage 
    for r in results if not r.error
)
has_convex_hull_data = any(r.acreage_detailed > 0 for r in results)
```

### Display Logic
- If convex hull data exists: Show both stat cards
- If no convex hull data: Show only bounding box card
- Fallback: If a file has no convex hull, its bbox is added to convex hull total

## Testing

Run a scan with the convex hull checkbox:
- ✅ **Checked:** Both acreage types displayed
- ✅ **Unchecked:** Only bounding box displayed

## Files Modified

- `report_generator.py` - Updated both `_generate_summary_html()` and `_generate_details_html()`

## Next Steps

1. Test with multiple LAS files to verify totals are calculated correctly
2. Test with convex hull disabled to verify only bbox shows
3. Verify HTML rendering in browser

