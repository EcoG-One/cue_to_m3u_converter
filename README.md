# cue_to_m3u_converter
A Python application that converts CUE sheets to M3U playlists.
## Key Features:
- **Complete CUE parsing:** Handles titles, performers, file references, track numbers, and time indices
- **M3U format support:** Generates both simple and extended M3U formats
- **Duration calculation:** Calculates track durations based on CUE index positions
- **Flexible output options:** Supports relative or absolute file paths
- **Batch processing:** Can convert multiple CUE files at once
- **Error handling:** Handles encoding issues and missing files gracefully
- **GUI mode and Command Line Mode:** Started as CLI, now offers a GUI as default and GLI as alternative  

## GUI Features:
### Main Interface:
- **File Selection:** Add/remove CUE files with a visual list
- **Output Directory:** Browse and select where M3U files will be saved
- **Options Panel:** Checkboxes for extended format and relative paths
- **Progress Bar:** Shows conversion progress in real-time
- **Status Log:** Displays detailed conversion results and errors

## Key GUI Components:

### File Management:
- **"Add Files"** button to select multiple CUE files
- **"Remove Selected"** to remove specific files
- **"Clear All"** to empty the file list
- **Visual listbox** showing selected files

### Output Configuration:
- **Browse** button for output directory selection
- **Text field** showing current output path

### Conversion Options:
- **Extended M3U format toggle (recommended)**
- **Relative vs absolute file paths option**

### Processing Features:
- **Threaded conversion** (won't freeze the GUI)
- **Real-time progress updates**
- **Detailed logging of each conversion**
- **Success/error notifications**

## Usage Options:
### GUI Mode (Default):
```sh
python cue_to_m3u.py          # Launch GUI
python cue_to_m3u.py --gui    # Explicit GUI launch
```

### Command Line Mode:
```sh
# Convert single file
python cue_to_m3u.py album.cue

# Specify output file
python cue_to_m3u.py album.cue -o my_playlist.m3u

# Generate simple M3U format
python cue_to_m3u.py album.cue --simple

# Use absolute paths
python cue_to_m3u.py album.cue --absolute

# Batch convert multiple files
python cue_to_m3u.py *.cue --batch
```

### GUI Workflow:

1. **Add Files:** Click "Add Files" to select CUE files
2. **Set Output:** Browse for output directory
3. **Configure Options:** Choose M3U format and path settings
4. **Convert:** Click "Convert Files" to start processing
5. **Monitor Progress:** Watch the progress bar and status log
6. **Review Results:** Check the log for conversion details

The GUI is built with tkinter and provides a user-friendly alternative to the command-line interface while maintaining the same functionality. 
The interface is responsive, includes proper error handling, and provides clear feedback throughout the conversion process.

### How it works:

- **CueSheet class:** Represents the entire CUE file with metadata and tracks
- **CueTrack class:** Represents individual tracks with their properties
- **Parser:** Extracts information from CUE files using regex patterns
- **Converter:** Transforms parsed data into M3U format
- **CLI interface:** Provides command-line options for different use cases

The application handles common CUE file formats and generates standard M3U playlists that work with most media players. 
It preserves track information like titles and performers while maintaining proper file references.
