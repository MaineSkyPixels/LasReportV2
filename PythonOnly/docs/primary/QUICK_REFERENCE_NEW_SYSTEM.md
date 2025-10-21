# Quick Reference - New Intelligent RAM System

## What Changed?

### Old System ❌
- Manual decimation controls (10%, 50%, 100% radio buttons)
- Hard-coded 2GB file size limits
- User had to understand technical details
- Could crash on large files with insufficient RAM

### New System ✅
- **Fully automatic** RAM-based optimization
- **No file size limits** - works with any size
- **Intelligent** per-file calculation
- **Safe** - never exceeds available RAM
- **Simple** - just one checkbox + info button

## How to Use

1. **Check your RAM:** Minimum 8GB available recommended
2. **Check the checkbox:** "Calculate detailed acreage using convex hull (RAM intensive)"
3. **Click Info button** (optional): Read about how it works
4. **Start scan:** System handles everything automatically!

## What the System Does Automatically

- ✅ Checks available RAM at startup
- ✅ Warns if RAM < 8GB
- ✅ Calculates optimal decimation per-file
- ✅ Adjusts thread count (4 vs 12)
- ✅ Prevents crashes
- ✅ Maximizes accuracy

## RAM Examples (with 24GB available)

| Your File Size | Points Used | Why |
|---------------|-------------|-----|
| 500 MB | 100% | Plenty of RAM |
| 2 GB | 100% | Still fits comfortably |
| 5 GB | 100% | Within safe limit |
| 10 GB | 84% | Optimized for safety |
| 15 GB | 56% | Large file, scaled down |

## What You'll See

### Good RAM (≥8GB):
```
System RAM: 24.5 GB available
RAM check passed
Processor settings: max_workers=4, low_ram_mode=False
```

### Low RAM (<8GB):
```
⚠️ LOW RAM WARNING: Only 6.5 GB available.
Recommended: 8.0 GB or more.
Convex hull will use maximum decimation (1%) to prevent crashes.
```

### During Processing:
```
cloud_large.las: RAM-optimized decimation: 75% (3500MB file, 12.5GB RAM)
```

## Threading Behavior

| Mode | Threads | Why |
|------|---------|-----|
| Standard (bbox only) | 12 | Fast, low RAM |
| Convex Hull | 4 | Prevents RAM overload |

## The Info Button

Click "ℹ️ Info" to see:
- What convex hull is
- Why it needs RAM
- How automatic optimization works
- Why threads are reduced
- Accuracy information
- Best practices

## Files Modified

- `gui.py` - Simplified UI, added info dialog
- `main.py` - RAM checking, thread management
- `processor.py` - Intelligent decimation
- `system_utils.py` - NEW - RAM detection
- `requirements.txt` - Added psutil

## Installation

If you get an error about psutil:
```bash
pip install psutil==5.9.8
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## Testing

Quick RAM test:
```bash
python test_ram_system.py
```

Should show:
- Your system RAM
- Whether you meet 8GB minimum
- Decimation examples for different file sizes

## FAQ

**Q: Do I still need to choose decimation?**  
A: No! System does it automatically.

**Q: Will it work with my 10GB files?**  
A: Yes! No more file size limits.

**Q: What if I have 6GB RAM?**  
A: You'll get a warning. System will use 1% decimation (still works, just less accurate).

**Q: Why only 4 threads for convex hull?**  
A: Each file loads entirely into RAM. 4 at a time prevents crashes.

**Q: Is it still accurate with decimation?**  
A: Yes! Even 10% decimation is very accurate for convex hull (it's a boundary operation).

**Q: Can I override the automatic settings?**  
A: No, but the system is designed to make optimal choices. Trust it!

## Troubleshooting

**"Low RAM warning appears"**
- Close other applications to free up RAM
- System will still work with 1% decimation
- Consider upgrading RAM for best results

**"psutil not found" error**
- Run: `pip install psutil==5.9.8`
- Or: `pip install -r requirements.txt`

**Processing seems slow**
- Large files (>5GB) take longer
- Only 4 threads when convex hull is on (by design)
- Check RAM - might be using aggressive decimation

## Summary

✅ No more manual settings  
✅ No more file size limits  
✅ No more crashes  
✅ Maximum accuracy for your hardware  
✅ Just works!

**Enjoy your new intelligent system!** 🚀

