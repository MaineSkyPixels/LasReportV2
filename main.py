"""
Main entry point for the LAS File Analysis application.
Orchestrates all components: GUI, scanning, processing, and report generation.
"""

import customtkinter as ctk
import logging
from pathlib import Path
from datetime import datetime
import traceback
import threading

from gui import LASReportGUI
from scanner import find_las_files
from processor import LASProcessor
from report_generator import ReportGenerator
from system_utils import (check_minimum_ram, format_ram_size, 
                         estimate_total_ram_needed, calculate_optimal_threads,
                         format_file_size, estimate_concurrent_ram_needed,
                         calculate_optimal_threads_smart, get_available_ram_gb, DiskIOMonitor)


# Setup logging
def setup_logging(directory: Path) -> tuple[logging.Logger, Path]:
    """
    Setup logging to file and console with FULL DEBUG output.
    
    Args:
        directory: Directory where logs will be saved
        
    Returns:
        Tuple of (configured logger, log file path)
    """
    log_dir = directory / ".las_analysis_logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"scan_{timestamp}.log"
    console_output_file = log_dir / f"console_output_{timestamp}.txt"
    
    logger = logging.getLogger("LASAnalysis")
    logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler - DEBUG level
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    # Console handler - DEBUG level (FULL DEBUG MODE)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # Console output file handler - Captures everything sent to console
    cfh = logging.FileHandler(console_output_file, encoding='utf-8')
    cfh.setLevel(logging.DEBUG)
    
    # Detailed formatter for debugging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    cfh.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.addHandler(cfh)
    
    print(f"\n{'='*80}")
    print(f"FULL DEBUG MODE ENABLED")
    print(f"{'='*80}")
    print(f"Log file: {log_file}")
    print(f"Console output file: {console_output_file}")
    print(f"{'='*80}\n")
    
    return logger, console_output_file


class LASAnalyzerApp:
    """Main application orchestrator."""
    
    def __init__(self, root: ctk.CTk):
        """
        Initialize the application.
        
        Args:
            root: Root CustomTkinter window
        """
        self.root = root
        self.gui = LASReportGUI(root)
        # Use threaded callback to keep GUI responsive
        self.gui.set_scan_callback(self._run_scan_threaded)
        self.logger = None
        self.scan_thread = None # Initialize scan_thread attribute
        self.preflight_optimal_threads = None # Initialize for preflight dialog
    

    def _run_scan_threaded(self, directory: Path, single_file: Path = None, use_detailed_acreage: bool = False):
        """
        Run the scan in a background thread to keep GUI responsive.
        
        Args:
            directory: Directory to scan
            single_file: Optional single file to scan
            use_detailed_acreage: Whether to calculate convex hull
        """
        # Create and start background thread
        self.scan_thread = threading.Thread(
            target=self.run_scan,
            args=(directory, single_file, use_detailed_acreage),
            daemon=False
        )
        self.scan_thread.start()

    def show_preflight_dialog(self, las_files: list, use_detailed_acreage: bool) -> bool:
        """
        Show a preflight dialog summarizing processing details before starting.
        
        Args:
            las_files: List of LAS files to process
            use_detailed_acreage: Whether convex hull calculation is enabled
            
        Returns:
            True if user clicked Proceed, False if user clicked Cancel
        """
        from tkinter import messagebox
        import tkinter.ttk as ttk
        
        # Calculate metrics
        total_size_gb = sum(f.stat().st_size for f in las_files) / (1024 ** 3)
        estimated_total_ram = estimate_total_ram_needed(las_files)
        
        available_ram = get_available_ram_gb()
        optimal_threads = calculate_optimal_threads_smart(las_files, available_ram, use_detailed_acreage)
        
        # Store for later use in run_scan
        self.preflight_optimal_threads = optimal_threads
        
        # Calculate RAM needed for concurrent threads (what actually matters)
        concurrent_ram = estimate_concurrent_ram_needed(las_files, optimal_threads)
        
        # Build dialog message
        message = (
            f"PREFLIGHT CHECK - Processing Summary\n"
            f"{'='*50}\n\n"
            f"Files to process: {len(las_files)}\n"
            f"Total size: {total_size_gb:.1f} GB\n\n"
            f"SYSTEM RESOURCES:\n"
            f"Available RAM: {format_ram_size(available_ram)}\n"
            f"Concurrent RAM usage: {format_ram_size(concurrent_ram)}\n"
            f"({optimal_threads} threads x avg file size)\n\n"
            f"PROCESSING CONFIGURATION:\n"
            f"Convex hull acreage: {'ENABLED (RAM intensive)' if use_detailed_acreage else 'disabled'}\n"
            f"Thread count: {optimal_threads}\n\n"
        )
        
        # Only warn if concurrent thread RAM usage would exceed available RAM
        if concurrent_ram > available_ram:
            message += (
                f"WARNING: Concurrent RAM usage exceeds available RAM!\n"
                f"Processing will use disk paging and be significantly slower.\n"
                f"Consider disabling convex hull or processing fewer files.\n\n"
            )
        
        message += "Do you want to proceed?"
        
        # Show dialog
        response = messagebox.askyesno("Preflight Check", message)
        return response
    
    def run_scan(self, directory: Path, single_file: Path = None, use_detailed_acreage: bool = False):
        """
        Run the complete scanning and reporting process.
        
        Args:
            directory: Directory to scan for LAS files (or parent directory if single_file is provided)
            single_file: Optional single LAS file to process instead of scanning directory
            use_detailed_acreage: If True, calculate convex hull acreage (RAM intensive)
        """
        try:
            # Determine report output directory and log message
            if single_file:
                report_dir = single_file.parent
                scan_target = f"single file: {single_file.name}"
            else:
                report_dir = directory
                scan_target = f"directory: {directory}"
            
            # Setup logging with FULL DEBUG
            self.logger, console_log_file = setup_logging(report_dir)
            self.logger.info(f"Starting LAS file analysis for {scan_target}")
            self.logger.info(f"Console output will be saved to: {console_log_file}")
            self.gui.log_status(f"📝 Debug logging enabled - Console output: {console_log_file.name}")
            
            # Check RAM availability
            meets_requirement, available_ram = check_minimum_ram(8.0)
            low_ram_mode = not meets_requirement
            
            if low_ram_mode:
                warning_msg = (f"⚠️ LOW RAM WARNING: Only {format_ram_size(available_ram)} available.\n"
                              f"Recommended: 8.0 GB or more.\n"
                              f"Convex hull will use maximum decimation (1%) to prevent crashes.")
                self.gui.log_status(warning_msg)
                self.logger.warning(warning_msg)
            else:
                self.logger.info(f"RAM check passed: {format_ram_size(available_ram)} available")
            
            # Determine which files to process
            if single_file:
                self.gui.log_status(f"Processing single file: {single_file.name}")
                las_files = [single_file]
            else:
                # Find LAS files
                self.gui.log_status("Scanning for LAS files...")
                las_files = find_las_files(str(directory))
            
            if not las_files:
                self.gui.log_status("❌ No LAS files found in the selected directory.")
                self.gui.show_error("No LAS files found in the selected directory.")
                self.logger.warning("No LAS files found")
                return
            
            self.gui.log_status(f"✓ Found {len(las_files)} LAS file(s)")
            for f in las_files:
                self.gui.log_status(f"  • {f.name}")
            
            self.logger.info(f"Found {len(las_files)} LAS files")
            
            # Show preflight dialog
            if not self.show_preflight_dialog(las_files, use_detailed_acreage):
                self.gui.log_status("⊘ Processing cancelled by user")
                self.logger.info("User cancelled processing at preflight check")
                return
            
            # Process LAS files
            self.gui.log_status("\nStarting file processing...")
            
            # Adjust thread count: convex hull requires loading entire file into RAM
            # Use fewer threads to avoid memory contention
            max_workers = self.preflight_optimal_threads
            
            processor = LASProcessor(
                max_workers=max_workers, 
                use_detailed_acreage=use_detailed_acreage, 
                low_ram_mode=low_ram_mode
            )
            
            self.logger.info(f"Processor settings: detailed_acreage={use_detailed_acreage}, "
                            f"max_workers={max_workers}, low_ram_mode={low_ram_mode}")
            
            # Initialize disk I/O monitoring
            disk_monitor = DiskIOMonitor()
            
            def progress_callback(completed, total, filename):
                # Handle sub-progress messages from convex hull calculation
                if isinstance(completed, str) and completed == "sub_progress":
                    self.gui.update_sub_progress(filename)  # filename contains the sub-progress message
                    return
                
                # Update disk speed
                disk_monitor.update()
                speed_mbs = disk_monitor.get_speed()
                
                # Update GUI with progress, stats, and disk speed
                self.gui.update_progress(completed, total, filename)
                self.gui.update_disk_speed(speed_mbs)
                self.gui.update_stats_label(completed, total, 
                                           estimate_total_ram_needed(las_files[:completed]) if completed > 0 else 0,
                                           available_ram,
                                           speed_mbs)
                
                # Check for cancellation
                if self.gui.cancel_requested:
                    processor.cancel_processing()
                    raise KeyboardInterrupt("User cancelled operation")
                
                self.logger.info(f"Processed {completed}/{total}: {filename} (Speed: {speed_mbs:.1f} MB/s)")
            
            # Set processing mode
            self.gui.set_processing_mode(True)
            
            try:
                results, aggregate = processor.process_files(las_files, progress_callback)
            finally:
                # Reset processing mode
                self.gui.set_processing_mode(False)
            
            self.gui.log_status("✓ File processing completed")
            self.logger.info("File processing completed")
            
            # Log results
            self.logger.info(f"Total files: {aggregate['total_files']}")
            self.logger.info(f"Valid files: {aggregate['valid_files']}")
            self.logger.info(f"Failed files: {aggregate['failed_files']}")
            self.logger.info(f"Total points: {aggregate['total_points']}")
            self.logger.info(f"Average point density: {aggregate['avg_point_density']:.2f}")
            
            # Debug: Log detailed acreage information for each result
            self.logger.debug("\n" + "="*80)
            self.logger.debug("RESULTS BEFORE REPORT GENERATION:")
            self.logger.debug("="*80)
            for result in results:
                self.logger.debug(f"File: {result.filename}")
                self.logger.debug(f"  acreage_detailed: {result.acreage_detailed:.4f}")
                self.logger.debug(f"  point_density: {result.point_density:.4f}")
                self.logger.debug(f"  error: {result.error}")
            self.logger.debug("="*80 + "\n")
            
            # Generate reports
            self.gui.log_status("\nGenerating HTML reports...")
            generator = ReportGenerator(str(report_dir))
            
            try:
                summary_path = generator.generate_summary_report(results, aggregate)
                self.gui.log_status(f"✓ Summary report: {summary_path.name}")
                self.logger.info(f"Summary report generated: {summary_path}")
            except Exception as e:
                error_msg = f"Failed to generate summary report: {str(e)}"
                self.gui.log_status(f"❌ {error_msg}")
                self.logger.error(error_msg)
                raise
            
            try:
                details_path = generator.generate_details_report(results)
                self.gui.log_status(f"✓ Details report: {details_path.name}")
                self.logger.info(f"Details report generated: {details_path}")
            except Exception as e:
                error_msg = f"Failed to generate details report: {str(e)}"
                self.gui.log_status(f"❌ {error_msg}")
                self.logger.error(error_msg)
                raise
            
            # Verify reports exist before showing completion
            if not summary_path.exists() or not details_path.exists():
                error_msg = "Reports were not properly written to disk"
                self.gui.show_error(error_msg)
                self.logger.error(error_msg)
                return
            
            # Show completion (GUI will calculate processing time from button click)
            self.gui.log_status("\n✓ All reports generated successfully!")
            self.gui.show_completion_dialog(summary_path, details_path, aggregate)
            
            # Log detailed results
            self.logger.info("=" * 80)
            self.logger.info("DETAILED FILE RESULTS:")
            self.logger.info("=" * 80)
            
            for result in results:
                self.logger.info(f"\nFile: {result.filename}")
                self.logger.info(f"  Path: {result.filepath}")
                self.logger.info(f"  File Size: {result.file_size_mb:.2f} MB")
                self.logger.info(f"  Processing Time: {result.processing_time:.2f} sec")
                
                if result.error:
                    self.logger.error(f"  ERROR: {result.error}")
                else:
                    self.logger.info(f"  Point Count: {result.point_count:,}")
                    self.logger.info(f"  Point Density: {result.point_density:.2f} pts/m²")
                    self.logger.info(f"  Bounds X: {result.min_x:.2f} to {result.max_x:.2f}")
                    self.logger.info(f"  Bounds Y: {result.min_y:.2f} to {result.max_y:.2f}")
                    self.logger.info(f"  Bounds Z: {result.min_z:.2f} to {result.max_z:.2f}")
                    
                    if result.raw_output:
                        self.logger.debug(f"  Raw lasinfo output:\n{result.raw_output}")
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info("Analysis completed successfully!")
            self.logger.info("=" * 80)
            
        except KeyboardInterrupt:
            self.gui.log_status("\n⏹ Scan cancelled by user")
            self.logger.info("Scan cancelled by user")
        except FileNotFoundError as e:
            error_msg = f"lasinfo command not found. Make sure it's installed and in PATH.\n{str(e)}"
            self.gui.show_error(error_msg)
            if self.logger:
                self.logger.error(error_msg)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}\n\n{traceback.format_exc()}"
            self.gui.show_error(error_msg)
            if self.logger:
                self.logger.error(error_msg)
    
    def run(self):
        """Start the application."""
        self.gui.run()


def main():
    """Application entry point."""
    root = ctk.CTk()
    app = LASAnalyzerApp(root)
    app.run()


if __name__ == "__main__":
    main()
