# Timestamped Report Filenames

**Date:** October 21, 2025  
**Status:** ✅ Implemented

## Overview

Report filenames now include timestamps to prevent overwriting existing reports and make it easy to see when each report was generated.

## Filename Format

**Format:** `reportname-MM-DD-YYYY-HH-MM.html`

**Components:**
- `MM` - Month (01-12)
- `DD` - Day (01-31)
- `YYYY` - Year (4 digits)
- `HH` - Hour (00-23, 24-hour format)
- `MM` - Minute (00-59)

**Examples:**

| Date/Time | Summary Report | Details Report |
|-----------|---------------|----------------|
| October 20, 2025 at 9:08 PM | `summary-10-20-2025-21-08.html` | `lasdetails-10-20-2025-21-08.html` |
| January 5, 2025 at 3:45 AM | `summary-01-05-2025-03-45.html` | `lasdetails-01-05-2025-03-45.html` |
| December 31, 2025 at 11:59 PM | `summary-12-31-2025-23-59.html` | `lasdetails-12-31-2025-23-59.html` |

## Benefits

### 1. No Overwriting
**Before:** Each scan overwrote previous reports
```
summary.html          ← Gets replaced every scan
lasdetails.html       ← Gets replaced every scan
```

**After:** Each scan creates new timestamped files
```
summary-10-20-2025-21-08.html      ← Preserved
summary-10-20-2025-21-15.html      ← New scan
summary-10-21-2025-09-30.html      ← Next day
lasdetails-10-20-2025-21-08.html
lasdetails-10-20-2025-21-15.html
lasdetails-10-21-2025-09-30.html
```

### 2. Easy to Identify
- Filename tells you exactly when the report was generated
- Sort by filename = sort by date/time
- No need to check file properties

### 3. Historical Tracking
- Keep multiple versions of reports
- Compare results from different times
- Track changes in your data over time

### 4. Clear Organization
Files naturally sort chronologically in file explorer:
```
lasdetails-10-15-2025-14-30.html
lasdetails-10-20-2025-09-15.html
lasdetails-10-20-2025-21-08.html
lasdetails-10-21-2025-10-45.html
summary-10-15-2025-14-30.html
summary-10-20-2025-09-15.html
summary-10-20-2025-21-08.html
summary-10-21-2025-10-45.html
```

## Implementation

### Code Changes

**File:** `report_generator.py`

```python
def generate_summary_report(self, results, aggregate):
    # Generate timestamp: MM-DD-YYYY-HH-MM format
    timestamp = datetime.now().strftime("%m-%d-%Y-%H-%M")
    report_filename = f"summary-{timestamp}.html"
    report_path = self.output_directory / report_filename
    # ... generate and write report
    
def generate_details_report(self, results):
    # Generate timestamp: MM-DD-YYYY-HH-MM format  
    timestamp = datetime.now().strftime("%m-%d-%Y-%H-%M")
    report_filename = f"lasdetails-{timestamp}.html"
    report_path = self.output_directory / report_filename
    # ... generate and write report
```

### Footer Updates

**Updated footer text to be generic:**
- Before: "see **summary.html**"
- After: "see the **summary** report"

This is because the exact filename changes with each run.

## User Experience

### When You Run a Scan

**Console Output:**
```
Generating HTML reports...
✓ Summary report: summary-10-20-2025-21-08.html
✓ Details report: lasdetails-10-20-2025-21-08.html
```

**GUI Status:**
```
✓ Summary report: summary-10-20-2025-21-08.html
✓ Details report: lasdetails-10-20-2025-21-08.html
✓ All reports generated successfully!
```

**In File Explorer:**
Your scan directory will show:
```
📁 YourLASFiles/
  📄 cloud0.las
  📄 cloud1.las
  📄 summary-10-20-2025-21-08.html     ← Today's reports
  📄 lasdetails-10-20-2025-21-08.html
  📄 summary-10-19-2025-15-30.html     ← Yesterday's reports
  📄 lasdetails-10-19-2025-15-30.html
```

### File Management

**Viewing Reports:**
- Double-click any report to open in browser
- Filename shows when it was created
- Both summary and details have matching timestamps

**Cleaning Up Old Reports:**
- Delete old reports manually when no longer needed
- Or keep them for historical comparison
- Easy to identify by date in filename

**Finding Latest Report:**
- Sort by filename (descending) = newest first
- Or sort by "Date Modified" in file explorer

## Timestamp Format Details

**Why MM-DD-YYYY-HH-MM?**
- ✅ American date format (common in US)
- ✅ Dashes separate each component clearly
- ✅ Sorts correctly alphabetically
- ✅ Easy to read and understand
- ✅ No spaces (filesystem friendly)
- ✅ No colons (Windows friendly)

**Time is 24-hour format:**
- 00:00 = Midnight
- 12:00 = Noon
- 21:08 = 9:08 PM
- 23:59 = 11:59 PM

## Sorting Behavior

Files will sort alphabetically, which may not be perfect chronological order:

```
summary-01-15-2025-10-30.html  (Jan 15)
summary-10-20-2025-21-08.html  (Oct 20)
summary-12-01-2025-09-15.html  (Dec 1)
```

This is a trade-off for human readability. If you need perfect sorting, use "Date Modified" in file explorer.

## Backward Compatibility

**Old reports (if they exist):**
```
summary.html
lasdetails.html
```

**New reports:**
```
summary-10-20-2025-21-08.html
lasdetails-10-20-2025-21-08.html
```

Both can coexist. Old reports won't be automatically deleted.

## Testing

Generate a report and verify:
1. ✅ Filename includes timestamp
2. ✅ Format is `reportname-MM-DD-YYYY-HH-MM.html`
3. ✅ Multiple runs create different files
4. ✅ No files are overwritten
5. ✅ Reports open correctly in browser

## Future Enhancements

Possible improvements:
1. **Auto-cleanup:** Option to delete reports older than X days
2. **Report naming:** User-defined prefix or suffix
3. **ISO format:** Option for YYYY-MM-DD format (better sorting)
4. **Seconds:** Include seconds for very frequent scans
5. **Report indexer:** Generate an index.html listing all reports

## Files Modified

- `report_generator.py` - Added timestamp to filenames in both report methods

## Summary

✅ Reports no longer overwrite each other  
✅ Easy to see when each report was created  
✅ Historical tracking possible  
✅ Clear, readable format  
✅ Filesystem friendly  

**Example for today (Oct 20, 2025 at 9:08 PM):**
- `summary-10-20-2025-21-08.html`
- `lasdetails-10-20-2025-21-08.html`

Perfect!

