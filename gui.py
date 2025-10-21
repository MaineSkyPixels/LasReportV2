"""
GUI module for LAS file scanning application using CustomTkinter.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, Callable
import subprocess
import platform
import webbrowser


class LASReportGUI:
    """CustomTkinter GUI for the LAS file scanning application."""
    
    def __init__(self, root: ctk.CTk):
        """
        Initialize the GUI.
        
        Args:
            root: Root CustomTkinter window
        """
        self.root = root
        self.root.title("LAS File Analysis Tool")
        self.root.geometry("800x875")
        self.root.minsize(700, 815)
        self.root.resizable(True, True)
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # Start with dark mode
        ctk.set_default_color_theme("blue")
        
        self.selected_directory: Optional[Path] = None
        self.selected_single_file: Optional[Path] = None
        self.last_report_directory: Optional[Path] = None
        self.scan_callback: Optional[Callable] = None
        self.cancel_requested = False
        self.detailed_acreage = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout GUI widgets."""
        
        # Main container with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title section
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="📊 LAS File Analysis Tool",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=10)
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Professional LiDAR point cloud analysis and reporting",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        subtitle.pack(pady=(0, 10))
        
        # Directory selection frame
        dir_frame = ctk.CTkFrame(main_frame)
        dir_frame.pack(fill="x", pady=(0, 10))
        
        dir_title = ctk.CTkLabel(
            dir_frame,
            text="📁 Select Directory or File",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        dir_title.pack(pady=(10, 5))
        
        self.dir_label = ctk.CTkLabel(
            dir_frame,
            text="No directory or file selected",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        self.dir_label.pack(pady=(0, 8))
        
        button_frame = ctk.CTkFrame(dir_frame)
        button_frame.pack(pady=(0, 10))
        
        browse_btn = ctk.CTkButton(
            button_frame,
            text="📁 Browse Directory",
            command=self._browse_directory,
            width=150,
            height=35
        )
        browse_btn.pack(side="left", padx=(20, 10), pady=15)
        
        single_las_btn = ctk.CTkButton(
            button_frame,
            text="📄 Single LAS File",
            command=self._browse_single_las,
            width=150,
            height=35
        )
        single_las_btn.pack(side="left", padx=10, pady=15)
        
        clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Clear",
            command=self._clear_directory,
            width=100,
            height=35,
            fg_color="gray60",
            hover_color="gray50"
        )
        clear_btn.pack(side="left", padx=(10, 20), pady=15)
        
        # Options frame
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=(0, 10))
        
        options_title = ctk.CTkLabel(
            options_frame,
            text="⚙️ Processing Options",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        options_title.pack(pady=(10, 5))
        
        # Convex hull option with info button
        hull_frame = ctk.CTkFrame(options_frame)
        hull_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.detailed_acreage_var = ctk.BooleanVar(value=False)
        acreage_check = ctk.CTkCheckBox(
            hull_frame,
            text="Calculate detailed acreage using convex hull (RAM intensive)",
            variable=self.detailed_acreage_var,
            command=self._update_acreage_setting,
            font=ctk.CTkFont(size=12)
        )
        acreage_check.pack(side="left", padx=(20, 10), pady=15)
        
        # Info button for RAM/threading information
        info_btn = ctk.CTkButton(
            hull_frame,
            text="ℹ️ Info",
            command=self._show_processing_info,
            width=80,
            height=30,
            fg_color="gray60",
            hover_color="gray50"
        )
        info_btn.pack(side="left", padx=(10, 20), pady=15)
        
        # Status and progress frame
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        progress_title = ctk.CTkLabel(
            progress_frame,
            text="📈 Processing Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        progress_title.pack(pady=(10, 5))
        
        # Progress bar
        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            variable=self.progress_var,
            width=400,
            height=20
        )
        self.progress_bar.pack(pady=(0, 5))
        self.progress_bar.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready",
            font=ctk.CTkFont(size=15)
        )
        self.progress_label.pack(pady=(0, 5))
        
        # Sub-progress label for convex hull operations
        self.sub_progress_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="gray60"
        )
        self.sub_progress_label.pack(pady=(0, 5))
        
        # Horizontal frame for disk I/O and stats
        bottom_frame = ctk.CTkFrame(progress_frame)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        # Left side - Disk I/O speed
        disk_speed_frame = ctk.CTkFrame(bottom_frame)
        disk_speed_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        disk_speed_title = ctk.CTkLabel(
            disk_speed_frame,
            text="💾 Disk I/O Speed",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        disk_speed_title.pack(pady=(5, 3))
        
        self.disk_speed_var = ctk.DoubleVar()
        self.disk_speed_bar = ctk.CTkProgressBar(
            disk_speed_frame,
            variable=self.disk_speed_var,
            width=200,
            height=15
        )
        self.disk_speed_bar.pack(pady=(0, 3))
        self.disk_speed_bar.set(0)
        
        # Disk speed text label
        self.disk_speed_label = ctk.CTkLabel(
            disk_speed_frame,
            text="-- MB/s",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.disk_speed_label.pack(pady=(0, 5))
        
        # Right side - Real-time statistics
        stats_frame = ctk.CTkFrame(bottom_frame)
        stats_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📈 Statistics",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        stats_title.pack(pady=(5, 3))
        
        # Real-time statistics label
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        self.stats_label.pack(pady=(0, 5))
        
        # Status text area with fixed height
        status_frame = ctk.CTkFrame(progress_frame)
        status_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        status_title = ctk.CTkLabel(
            status_frame,
            text="📝 Status Log",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        status_title.pack(pady=(5, 3))
        
        self.status_text = ctk.CTkTextbox(
            status_frame,
            height=90,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.status_text.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Control buttons frame
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        self.start_btn = ctk.CTkButton(
            control_frame,
            text="▶️ Start Scan",
            command=self._start_scan,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f538d",
            hover_color="#1a4a7a"
        )
        self.start_btn.pack(side="left", padx=(20, 10), pady=15)
        
        self.cancel_btn = ctk.CTkButton(
            control_frame,
            text="⏹️ Cancel",
            command=self._cancel_scan,
            width=120,
            height=40,
            state="disabled",
            fg_color="gray60",
            hover_color="gray50"
        )
        self.cancel_btn.pack(side="left", padx=10, pady=15)
        
        self.open_folder_btn = ctk.CTkButton(
            control_frame,
            text="📂 Open Reports",
            command=self._open_reports_folder,
            width=120,
            height=40,
            state="disabled",
            fg_color="gray60",
            hover_color="gray50"
        )
        self.open_folder_btn.pack(side="left", padx=10, pady=15)
        
        # Theme toggle button
        self.theme_btn = ctk.CTkButton(
            control_frame,
            text="🌙 Dark/Light",
            command=self._toggle_theme,
            width=120,
            height=40,
            fg_color="gray60",
            hover_color="gray50"
        )
        self.theme_btn.pack(side="right", padx=(10, 20), pady=15)
        
        exit_btn = ctk.CTkButton(
            control_frame,
            text="❌ Exit",
            command=self.root.quit,
            width=100,
            height=40,
            fg_color="#d32f2f",
            hover_color="#b71c1c"
        )
        exit_btn.pack(side="right", padx=(10, 20), pady=15)
    
    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        current_mode = ctk.get_appearance_mode()
        new_mode = "light" if current_mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        
        # Update button text to reflect new mode
        new_text = "☀️ Light/Dark" if new_mode == "light" else "🌙 Dark/Light"
        self.theme_btn.configure(text=new_text)
    
    def _browse_directory(self):
        """Open directory selection dialog."""
        try:
            directory = filedialog.askdirectory(
                title="Select Directory to Scan for LAS Files"
            )
            
            if directory:
                dir_path = Path(directory)
                if not dir_path.exists():
                    messagebox.showerror(
                        "Invalid Directory",
                        f"Directory does not exist: {directory}"
                    )
                    return
                
                if not dir_path.is_dir():
                    messagebox.showerror(
                        "Invalid Path",
                        f"Path is not a directory: {directory}"
                    )
                    return
                
                self.selected_directory = dir_path
                self.selected_single_file = None
                self.dir_label.configure(
                    text=str(self.selected_directory),
                    text_color=("gray10", "gray90")
                )
                self.log_status(f"✓ Selected directory: {self.selected_directory}")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to select directory: {str(e)}"
            )
    
    def _browse_single_las(self):
        """Open file selection dialog for a single LAS file."""
        try:
            file_path = filedialog.askopenfilename(
                title="Select a Single LAS File",
                filetypes=[("LAS Files", "*.las"), ("All Files", "*.*")]
            )
            
            if file_path:
                las_path = Path(file_path)
                if not las_path.exists():
                    messagebox.showerror(
                        "Invalid File",
                        f"File does not exist: {file_path}"
                    )
                    return
                
                if not las_path.is_file():
                    messagebox.showerror(
                        "Invalid Path",
                        f"Path is not a file: {file_path}"
                    )
                    return
                
                if las_path.suffix.lower() != ".las":
                    messagebox.showwarning(
                        "Warning",
                        f"File may not be a LAS file: {file_path}"
                    )
                
                self.selected_single_file = las_path
                self.selected_directory = las_path.parent
                self.dir_label.configure(
                    text=f"📄 {las_path.name}",
                    text_color=("gray10", "gray90")
                )
                self.log_status(f"✓ Selected file: {las_path.name}")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to select file: {str(e)}"
            )
    
    def _clear_directory(self):
        """Clear the selected directory or file."""
        self.selected_directory = None
        self.selected_single_file = None
        self.dir_label.configure(
            text="No directory or file selected",
            text_color="gray60"
        )
        self.log_status("Directory/file selection cleared")
    
    def _update_acreage_setting(self):
        """Update the detailed acreage flag."""
        self.detailed_acreage = self.detailed_acreage_var.get()
        if self.detailed_acreage:
            self.log_status("✓ Detailed acreage calculation enabled (RAM intensive)")
        else:
            self.log_status("Detailed acreage calculation disabled")
    
    def _show_processing_info(self):
        """Show information dialog about RAM usage and processing."""
        info_window = ctk.CTkToplevel(self.root)
        info_window.title("Processing Information")
        info_window.geometry("700x550")
        info_window.resizable(False, False)
        
        # Make it modal
        info_window.transient(self.root)
        info_window.grab_set()
        
        # Main frame with padding
        main_frame = ctk.CTkFrame(info_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Convex Hull Processing & RAM Usage",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create scrollable text widget
        info_text = ctk.CTkTextbox(
            main_frame,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        info_text.pack(fill="both", expand=True, pady=(0, 20))
        
        # Info content
        info_content = """CONVEX HULL ACREAGE CALCULATION

What is it?
Calculates actual footprint area by analyzing the boundary of point cloud data, rather than using a simple rectangular bounding box.

WHY IT'S RAM INTENSIVE

When convex hull is enabled, the entire LAS file must be loaded into system RAM:

1. File Loading: The complete LAS file loads into memory
2. Coordinate Extraction: X,Y coordinates are extracted for all points
3. Hull Calculation: Mathematical analysis finds the outer boundary
4. Area Calculation: The enclosed area is calculated in acres

For a 5GB LAS file with 200 million points:
• File in RAM: ~5 GB
• Coordinate arrays: ~1.6 GB
• Total RAM needed: ~6.6 GB

INTELLIGENT RAM MANAGEMENT

The system automatically optimizes based on available RAM:

• Minimum 8GB Required: System checks at startup
• Low RAM Mode: If <8GB available, uses 1% point sampling
• Smart Decimation: Automatically samples points to fit available RAM
• No Manual Settings: System handles optimization automatically

Examples:
• 2GB file + 16GB RAM available = 100% of points used
• 5GB file + 10GB RAM available = 50% of points used
• 8GB file + 8GB RAM available = 10% of points used

MULTITHREADING BEHAVIOR

Standard Processing (no convex hull):
• 12 concurrent threads
• Fast processing for lasinfo extraction
• Minimal RAM usage per file

Convex Hull Processing:
• 4 concurrent threads (automatic)
• Prevents RAM contention
• Each file needs full memory allocation
• Safer for large files

WHY REDUCED THREADS?

With 12 threads and convex hull:
• 12 files loading simultaneously into RAM
• Potential RAM exhaustion and crashes
• System slowdown from memory swapping

With 4 threads and convex hull:
• Only 4 files in RAM at once
• Stable memory usage
• Reliable processing of large files
• Still faster than single-threaded

ACCURACY WITH POINT SAMPLING

Even at 1% sampling, accuracy remains excellent:
• 100M points → 1M points still analyzed
• Convex hull is a boundary operation
• Sampling doesn't affect boundary accuracy significantly
• Typically within 0.1% of full calculation

RECOMMENDATIONS

✓ Ensure 8GB+ RAM available before enabling
✓ Close other memory-intensive applications
✓ Monitor processing for first few files
✓ Larger files process slower but safely
✓ Trust the automatic optimization

The system is designed to maximize accuracy while keeping your system stable and responsive."""
        
        info_text.insert("1.0", info_content)
        info_text.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=info_window.destroy,
            width=120,
            height=35
        )
        close_btn.pack(pady=(10, 0))
        
        # Center the window
        info_window.update_idletasks()
        x = (info_window.winfo_screenwidth() // 2) - (info_window.winfo_width() // 2)
        y = (info_window.winfo_screenheight() // 2) - (info_window.winfo_height() // 2)
        info_window.geometry(f"+{x}+{y}")
    
    def _start_scan(self):
        """Start the scanning process."""
        if not self.selected_directory and not self.selected_single_file:
            messagebox.showwarning(
                "No Directory or File Selected",
                "Please select a directory or a single LAS file to scan."
            )
            return
        
        # Check if directory still exists
        dir_path = Path(self.selected_directory) if self.selected_directory else self.selected_single_file.parent
        if not dir_path.exists():
            messagebox.showerror(
                "Invalid Directory",
                f"Directory no longer exists: {self.selected_directory if self.selected_directory else self.selected_single_file}"
            )
            self._clear_directory()
            return
        
        if not dir_path.is_dir():
            messagebox.showerror(
                "Invalid Path",
                f"Path is no longer a directory: {self.selected_directory if self.selected_directory else self.selected_single_file}"
            )
            self._clear_directory()
            return
        
        # Update detailed acreage flag
        self.detailed_acreage = self.detailed_acreage_var.get()
        
        # Update UI state
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.open_folder_btn.configure(state="disabled")
        self.progress_var.set(0)
        self.cancel_requested = False
        
        # Start scan
        try:
            if self.scan_callback:
                # Record start time when user clicks the button
                from datetime import datetime
                self.scan_start_time = datetime.now()
                self.scan_callback(self.selected_directory, self.selected_single_file, self.detailed_acreage)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to start scan: {str(e)}"
            )
        finally:
            self.start_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
    
    def _cancel_scan(self):
        """Request cancellation of the scan."""
        self.cancel_requested = True
        self.cancel_btn.configure(state="disabled")
        self.log_status("\n⏹️ Cancellation requested...")
    
    def _open_reports_folder(self):
        """Open the reports folder in the system file explorer."""
        if not self.last_report_directory:
            messagebox.showwarning(
                "No Reports",
                "No reports folder available. Please run a scan first."
            )
            self.open_folder_btn.configure(state="disabled")
            return
        
        if not self.last_report_directory.exists():
            messagebox.showerror(
                "Folder Not Found",
                f"Reports folder no longer exists: {self.last_report_directory}"
            )
            self.open_folder_btn.configure(state="disabled")
            self.last_report_directory = None
            return
        
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(f'explorer "{self.last_report_directory}"')
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', str(self.last_report_directory)])
            else:  # Linux
                subprocess.Popen(['xdg-open', str(self.last_report_directory)])
            
            self.log_status(f"✓ Opened reports folder")
        except FileNotFoundError as e:
            messagebox.showerror(
                "Error",
                f"File explorer command not found. The reports are located at:\n{self.last_report_directory}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not open folder: {str(e)}\n\nThe reports are located at:\n{self.last_report_directory}"
            )
    
    def log_status(self, message: str):
        """
        Log a status message to the status text area.
        
        Args:
            message: Message to log
        """
        self.status_text.insert("end", message + '\n')
        self.status_text.see("end")
        self.root.update_idletasks()
    
    def update_progress(self, current: int, total: int, current_file: str = ""):
        """
        Update progress bar and label.
        
        Args:
            current: Current file number
            total: Total number of files
            current_file: Name of current file being processed
        """
        if total > 0:
            progress_pct = current / total
            self.progress_var.set(progress_pct)
            
            label_text = f"Processing: {current}/{total} files"
            if current_file:
                label_text += f" - {current_file}"
            
            self.progress_label.configure(text=label_text)
            self.root.update_idletasks()
    
    def update_sub_progress(self, message: str):
        """
        Update the sub-progress label for detailed operations.
        
        Args:
            message: Sub-operation message
        """
        self.sub_progress_label.configure(text=message)
        self.root.update_idletasks()
    
    def update_disk_speed(self, speed_mbs: float, max_expected_speed: float = 200.0):
        """
        Update the disk I/O speed display.
        
        Args:
            speed_mbs: Current disk speed in MB/s
            max_expected_speed: Maximum expected speed for progress bar scaling
        """
        # Update speed label
        self.disk_speed_label.configure(text=f"{speed_mbs:.1f} MB/s")
        
        # Update progress bar (scaled to max expected speed)
        bar_value = min(1.0, speed_mbs / max_expected_speed)
        self.disk_speed_var.set(bar_value)
        
        # Update display
        self.root.update_idletasks()
    
    def update_stats_label(self, file_num: int, total_files: int, 
                          estimated_ram_gb: float, available_ram_gb: float,
                          speed_mbs: float):
        """
        Update the real-time statistics label.
        
        Args:
            file_num: Current file number
            total_files: Total number of files
            estimated_ram_gb: Estimated RAM being used
            available_ram_gb: Total available RAM
            speed_mbs: Current disk I/O speed in MB/s
        """
        stats_text = (
            f"File {file_num}/{total_files} • "
            f"RAM: {estimated_ram_gb:.1f}GB/{available_ram_gb:.1f}GB • "
            f"Speed: {speed_mbs:.1f} MB/s"
        )
        self.stats_label.configure(text=stats_text)
    
    def set_processing_mode(self, active: bool):
        """
        Enable/disable buttons for processing mode.
        
        Args:
            active: True to enable processing controls, False to disable
        """
        if active:
            self.start_btn.configure(state="disabled")
            self.cancel_btn.configure(state="normal")
            self.cancel_requested = False
        else:
            self.start_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
    
    def show_completion_dialog(self, summary_path: Path, details_path: Path, aggregate: dict, processing_time: float = None):
        """
        Show enhanced completion dialog with statistics and browser integration.
        
        Args:
            summary_path: Path to summary report
            details_path: Path to details report
            aggregate: Dictionary with aggregate statistics
            processing_time: Total processing time in seconds (if None, calculate from GUI start time)
        """
        # Calculate processing time from GUI start time if not provided
        if processing_time is None and hasattr(self, 'scan_start_time'):
            from datetime import datetime
            processing_time = (datetime.now() - self.scan_start_time).total_seconds()
        elif processing_time is None:
            # Fallback if no start time available
            processing_time = 0.0
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        
        # Store the report directory and enable the open folder button
        self.last_report_directory = summary_path.parent
        self.open_folder_btn.configure(state="normal")
        
        # Create completion dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Scan Complete")
        dialog.geometry("600x450")  # Reduced height for compact display
        dialog.resizable(False, False)
        
        # Make it modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame with minimal padding
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="✅ Scan Completed Successfully!",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Statistics frame
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.pack(fill="x", pady=(0, 10))
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 Summary Statistics",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        stats_title.pack(pady=(10, 5))
        
        # Create statistics grid
        stats_grid = ctk.CTkFrame(stats_frame)
        stats_grid.pack(fill="x", padx=5, pady=(0, 5))
        
        # Format numbers
        def format_number(num):
            if isinstance(num, int):
                return f"{num:,}"
            return f"{num:,.2f}"
        
        # Statistics rows
        stats_data = [
            ("Total Files", f"{aggregate['total_files']}"),
            ("Valid Files", f"{aggregate['valid_files']}"),
            ("Failed Files", f"{aggregate['failed_files']}"),
            ("Total Points", format_number(aggregate['total_points'])),
            ("Avg Density", f"{aggregate['avg_point_density']:.2f} pts/m²"),
            ("Total Size", f"{aggregate['total_file_size_mb']:.2f} MB"),
            ("Processing Time", f"{processing_time:.1f} seconds")
        ]
        
        for i, (label, value) in enumerate(stats_data):
            row_frame = ctk.CTkFrame(stats_grid)
            row_frame.pack(fill="x", pady=1)
            
            label_widget = ctk.CTkLabel(
                row_frame,
                text=f"{label}:",
                font=ctk.CTkFont(size=14, weight="bold"),
                width=120,
                anchor="w"
            )
            label_widget.pack(side="left", padx=(5, 3), pady=3)
            
            value_widget = ctk.CTkLabel(
                row_frame,
                text=value,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            value_widget.pack(side="left", padx=(3, 5), pady=3)
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(0, 5))
        
        def open_in_browser():
            webbrowser.open(str(summary_path))
            dialog.destroy()
        
        def open_folder():
            self._open_reports_folder()
            dialog.destroy()
        
        # Buttons
        browser_btn = ctk.CTkButton(
            button_frame,
            text="🌐 Open Report in Browser",
            command=open_in_browser,
            width=180,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1f538d",
            hover_color="#1a4a7a"
        )
        browser_btn.pack(side="left", padx=(10, 5), pady=8)
        
        folder_btn = ctk.CTkButton(
            button_frame,
            text="📂 Open Folder",
            command=open_folder,
            width=130,
            height=35
        )
        folder_btn.pack(side="left", padx=5, pady=8)
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=dialog.destroy,
            width=80,
            height=35,
            fg_color="gray60",
            hover_color="gray50"
        )
        close_btn.pack(side="right", padx=(5, 10), pady=8)
        
        # Center the window
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Log completion
        self.log_status(f"\n✅ Scan completed successfully!")
        self.log_status(f"📊 Processed {aggregate['valid_files']}/{aggregate['total_files']} files")
        self.log_status(f"📈 Total points: {format_number(aggregate['total_points'])}")
        self.log_status(f"⏱️ Processing time: {processing_time:.1f} seconds")
    
    def show_error(self, error_message: str):
        """
        Show error message.
        
        Args:
            error_message: Error message to display
        """
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        
        self.log_status(f"\n❌ Error: {error_message}")
        messagebox.showerror("Error", error_message)
    
    def set_scan_callback(self, callback: Callable):
        """
        Set the callback function to execute when scan starts.
        
        Args:
            callback: Function that takes a directory Path as argument
        """
        self.scan_callback = callback
    
    def run(self):
        """Start the GUI event loop."""
        self.root.mainloop()