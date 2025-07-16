#!/usr/bin/env python3
"""
CUE to M3U Playlist Converter

This application converts CUE sheet files to M3U playlist format.
It parses CUE files and extracts track information to create standard M3U playlists.
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading


class CueTrack:
    """Represents a single track from a CUE sheet."""
    
    def __init__(self):
        self.number: int = 0
        self.title: str = ""
        self.performer: str = ""
        self.index: str = ""
        self.file: str = ""
        self.file_type: str = ""
        self.duration: int = 0  # in seconds


class CueSheet:
    """Represents a CUE sheet with all its tracks and metadata."""
    
    def __init__(self):
        self.title: str = ""
        self.performer: str = ""
        self.file: str = ""
        self.file_type: str = ""
        self.tracks: List[CueTrack] = []


class CueToM3uConverter:
    """Main converter class that handles CUE to M3U conversion."""
    
    def __init__(self):
        self.cue_sheet = CueSheet()
    
    def parse_cue_file(self, cue_file_path: str) -> CueSheet:
        """Parse a CUE file and return a CueSheet object."""
        cue_sheet = CueSheet()
        current_track = None
        
        try:
            with open(cue_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(cue_file_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Parse global metadata
            if line.startswith('TITLE'):
                title = self._extract_quoted_value(line)
                if current_track:
                    current_track.title = title
                else:
                    cue_sheet.title = title
            
            elif line.startswith('PERFORMER'):
                performer = self._extract_quoted_value(line)
                if current_track:
                    current_track.performer = performer
                else:
                    cue_sheet.performer = performer
            
            elif line.startswith('FILE'):
                file_match = re.match(r'FILE\s+"(.+)"\s+(\w+)', line)
                if file_match:
                    file_name, file_type = file_match.groups()
                    if current_track:
                        current_track.file = file_name
                        current_track.file_type = file_type
                    else:
                        cue_sheet.file = file_name
                        cue_sheet.file_type = file_type
            
            elif line.startswith('TRACK'):
                # Save previous track if exists
                if current_track:
                    cue_sheet.tracks.append(current_track)
                
                # Start new track
                current_track = CueTrack()
                track_match = re.match(r'TRACK\s+(\d+)\s+(\w+)', line)
                if track_match:
                    current_track.number = int(track_match.group(1))
                    # Inherit file info from global or set default
                    current_track.file = cue_sheet.file
                    current_track.file_type = cue_sheet.file_type
            
            elif line.startswith('INDEX') and current_track:
                index_match = re.match(r'INDEX\s+(\d+)\s+(\d+):(\d+):(\d+)', line)
                if index_match and index_match.group(1) == '01':
                    minutes = int(index_match.group(2))
                    seconds = int(index_match.group(3))
                    frames = int(index_match.group(4))
                    current_track.index = f"{minutes:02d}:{seconds:02d}:{frames:02d}"
        
        # Add the last track
        if current_track:
            cue_sheet.tracks.append(current_track)
        
        # Calculate durations
        self._calculate_durations(cue_sheet)
        
        return cue_sheet
    
    def _extract_quoted_value(self, line: str) -> str:
        """Extract value from quoted string in CUE file line."""
        match = re.search(r'"([^"]*)"', line)
        return match.group(1) if match else ""
    
    def _calculate_durations(self, cue_sheet: CueSheet):
        """Calculate track durations based on INDEX positions."""
        for i, track in enumerate(cue_sheet.tracks):
            if track.index:
                start_time = self._index_to_seconds(track.index)
                
                # Calculate duration using next track's start time
                if i + 1 < len(cue_sheet.tracks):
                    next_track = cue_sheet.tracks[i + 1]
                    if next_track.index:
                        end_time = self._index_to_seconds(next_track.index)
                        track.duration = end_time - start_time
                else:
                    # For the last track, we can't calculate duration without file info
                    track.duration = 0
    
    def _index_to_seconds(self, index: str) -> int:
        """Convert CUE index format (MM:SS:FF) to seconds."""
        parts = index.split(':')
        if len(parts) == 3:
            minutes = int(parts[0])
            seconds = int(parts[1])
            frames = int(parts[2])
            # 75 frames per second in CD audio
            return minutes * 60 + seconds + frames // 75
        return 0
    
    def convert_to_m3u(self, cue_sheet: CueSheet, output_path: str, 
                       extended: bool = True, relative_paths: bool = True):
        """Convert CueSheet to M3U format and save to file."""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if extended:
                f.write("#EXTM3U\n")
            
            for track in cue_sheet.tracks:
                # Use track performer if available, otherwise use album performer
                performer = track.performer or cue_sheet.performer
                
                # Create display title
                if performer and track.title:
                    display_title = f"{performer} - {track.title}"
                elif track.title:
                    display_title = track.title
                else:
                    display_title = f"Track {track.number:02d}"
                
                if extended:
                    # Write extended info
                    f.write(f"#EXTINF:{track.duration},{display_title}\n")
                
                # Write file path
                file_path = track.file
                if relative_paths and file_path:
                    # Keep relative path as-is
                    f.write(f"{file_path}\n")
                else:
                    # Use absolute path
                    f.write(f"{os.path.abspath(file_path)}\n")
    
    def convert_file(self, cue_file_path: str, output_path: Optional[str] = None,
                     extended: bool = True, relative_paths: bool = True):
        """Convert a single CUE file to M3U format."""
        
        if not os.path.exists(cue_file_path):
            raise FileNotFoundError(f"CUE file not found: {cue_file_path}")
        
        # Parse CUE file
        cue_sheet = self.parse_cue_file(cue_file_path)
        
        # Generate output path if not provided
        if output_path is None:
            base_name = os.path.splitext(cue_file_path)[0]
            output_path = f"{base_name}.m3u"
        
        # Convert to M3U
        self.convert_to_m3u(cue_sheet, output_path, extended, relative_paths)
        
        return output_path, len(cue_sheet.tracks)


class CueToM3uGUI:
    """Graphical User Interface for CUE to M3U converter."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("CUE to M3U Converter")
        self.root.geometry("800x600")
        
        # Initialize converter
        self.converter = CueToM3uConverter()
        
        # Variables for form data
        self.input_files = []
        self.output_directory = tk.StringVar()
        self.extended_format = tk.BooleanVar(value=True)
        self.relative_paths = tk.BooleanVar(value=True)
        
        self.create_widgets()
        
        # Center the window
        self.center_window()
    
    def center_window(self):
        """Center the main window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="CUE to M3U Converter", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input files section
        ttk.Label(main_frame, text="Input CUE Files:").grid(row=1, column=0, sticky=tk.W)
        
        # File list frame
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 10))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)
        
        # Listbox for files
        self.file_listbox = tk.Listbox(file_frame, height=8)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # File buttons frame
        file_buttons_frame = ttk.Frame(main_frame)
        file_buttons_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Button(file_buttons_frame, text="Add Files", 
                  command=self.add_files).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="Remove Selected", 
                  command=self.remove_selected).grid(row=0, column=1, padx=5)
        ttk.Button(file_buttons_frame, text="Clear All", 
                  command=self.clear_all).grid(row=0, column=2, padx=(5, 0))
        
        # Output directory section
        ttk.Label(main_frame, text="Output Directory:").grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_directory)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(output_frame, text="Browse", 
                  command=self.browse_output).grid(row=0, column=1)
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Checkbutton(options_frame, text="Extended M3U format (recommended)", 
                       variable=self.extended_format).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Use relative file paths", 
                       variable=self.relative_paths).grid(row=1, column=0, sticky=tk.W)
        
        # Convert button
        self.convert_button = ttk.Button(main_frame, text="Convert Files", 
                                        command=self.convert_files)
        self.convert_button.grid(row=7, column=0, columnspan=3, pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status/Log area
        ttk.Label(main_frame, text="Status:").grid(row=9, column=0, sticky=tk.W)
        
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(10, weight=1)
        
        # Initial log message
        self.log_message("Ready to convert CUE files to M3U playlists.")
    
    def add_files(self):
        """Add CUE files to the conversion list."""
        files = filedialog.askopenfilenames(
            title="Select CUE Files",
            filetypes=[("CUE files", "*.cue"), ("All files", "*.*")]
        )
        
        for file in files:
            if file not in self.input_files:
                self.input_files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
        
        self.log_message(f"Added {len(files)} file(s) to conversion list.")
    
    def remove_selected(self):
        """Remove selected files from the conversion list."""
        selected = self.file_listbox.curselection()
        if not selected:
            return
        
        # Remove from back to front to maintain indices
        for index in reversed(selected):
            self.file_listbox.delete(index)
            del self.input_files[index]
        
        self.log_message(f"Removed {len(selected)} file(s) from conversion list.")
    
    def clear_all(self):
        """Clear all files from the conversion list."""
        self.file_listbox.delete(0, tk.END)
        self.input_files.clear()
        self.log_message("Cleared all files from conversion list.")
    
    def browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory.set(directory)
            self.log_message(f"Output directory set to: {directory}")
    
    def log_message(self, message):
        """Add a message to the log area."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def convert_files(self):
        """Convert all selected CUE files to M3U format."""
        if not self.input_files:
            messagebox.showwarning("Warning", "Please select at least one CUE file.")
            return
        
        output_dir = self.output_directory.get()
        if not output_dir:
            messagebox.showwarning("Warning", "Please select an output directory.")
            return
        
        if not os.path.exists(output_dir):
            messagebox.showerror("Error", f"Output directory does not exist: {output_dir}")
            return
        
        # Disable convert button during processing
        self.convert_button.config(state='disabled')
        
        # Start conversion in a separate thread
        threading.Thread(target=self.convert_worker, daemon=True).start()
    
    def convert_worker(self):
        """Worker thread for file conversion."""
        try:
            total_files = len(self.input_files)
            total_tracks = 0
            successful_conversions = 0
            
            self.log_message(f"Starting conversion of {total_files} files...")
            
            for i, cue_file in enumerate(self.input_files):
                try:
                    # Update progress
                    progress = (i / total_files) * 100
                    self.progress_var.set(progress)
                    
                    # Generate output path
                    base_name = os.path.splitext(os.path.basename(cue_file))[0]
                    output_path = os.path.join(self.output_directory.get(), f"{base_name}.m3u")
                    
                    # Convert file
                    _, track_count = self.converter.convert_file(
                        cue_file,
                        output_path,
                        extended=self.extended_format.get(),
                        relative_paths=self.relative_paths.get()
                    )
                    
                    self.log_message(f"✓ Converted {os.path.basename(cue_file)} -> {os.path.basename(output_path)} ({track_count} tracks)")
                    successful_conversions += 1
                    total_tracks += track_count
                    
                except Exception as e:
                    self.log_message(f"✗ Error converting {os.path.basename(cue_file)}: {str(e)}")
            
            # Final progress update
            self.progress_var.set(100)
            
            # Summary message
            self.log_message(f"\nConversion complete! Successfully converted {successful_conversions}/{total_files} files ({total_tracks} tracks total)")
            
            if successful_conversions == total_files:
                messagebox.showinfo("Success", f"All {total_files} files converted successfully!")
            else:
                messagebox.showwarning("Partial Success", 
                                     f"Converted {successful_conversions}/{total_files} files. Check the log for details.")
        
        except Exception as e:
            self.log_message(f"✗ Unexpected error: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        
        finally:
            # Re-enable convert button
            self.convert_button.config(state='normal')
            # Reset progress bar after a short delay
            self.root.after(2000, lambda: self.progress_var.set(0))


def main():
    """Main function to handle both CLI and GUI modes."""
    import sys
    
    if len(sys.argv) > 1:
        # Command-line mode
        parser = argparse.ArgumentParser(
            description="Convert CUE sheet files to M3U playlists",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python cue_to_m3u.py album.cue
  python cue_to_m3u.py album.cue -o playlist.m3u
  python cue_to_m3u.py album.cue --simple --absolute
  python cue_to_m3u.py *.cue --batch
  python cue_to_m3u.py --gui  # Launch GUI mode
            """
        )
        
        parser.add_argument('input', nargs='*', help='CUE file(s) to convert')
        parser.add_argument('-o', '--output', help='Output M3U file path')
        parser.add_argument('--simple', action='store_true', 
                           help='Generate simple M3U format (no extended info)')
        parser.add_argument('--absolute', action='store_true',
                           help='Use absolute paths instead of relative paths')
        parser.add_argument('--batch', action='store_true',
                           help='Process multiple files in batch mode')
        parser.add_argument('--gui', action='store_true',
                           help='Launch graphical user interface')
        
        args = parser.parse_args()
        
        if args.gui or not args.input:
            # Launch GUI mode
            root = tk.Tk()
            app = CueToM3uGUI(root)
            root.mainloop()
            return 0
        
        # Command-line processing
        converter = CueToM3uConverter()
        
        # Handle batch processing
        if args.batch or len(args.input) > 1:
            if args.output:
                print("Warning: --output ignored in batch mode")
            
            total_files = 0
            total_tracks = 0
            
            for cue_file in args.input:
                try:
                    output_path, track_count = converter.convert_file(
                        cue_file,
                        extended=not args.simple,
                        relative_paths=not args.absolute
                    )
                    print(f"✓ Converted {cue_file} -> {output_path} ({track_count} tracks)")
                    total_files += 1
                    total_tracks += track_count
                except Exception as e:
                    print(f"✗ Error converting {cue_file}: {e}")
            
            print(f"\nProcessed {total_files} files, {total_tracks} tracks total")
        
        else:
            # Single file processing
            try:
                output_path, track_count = converter.convert_file(
                    args.input[0],
                    args.output,
                    extended=not args.simple,
                    relative_paths=not args.absolute
                )
                print(f"✓ Converted {args.input[0]} -> {output_path} ({track_count} tracks)")
            except Exception as e:
                print(f"✗ Error: {e}")
                return 1
    
    else:
        # No arguments - launch GUI by default
        root = tk.Tk()
        app = CueToM3uGUI(root)
        root.mainloop()
    
    return 0


if __name__ == "__main__":
    exit(main())