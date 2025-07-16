# cue_to_m3u_converter
A Python application that converts CUE sheets to M3U playlists.
## Key Features:
- **Complete CUE parsing:** Handles titles, performers, file references, track numbers, and time indices
- **M3U format support:** Generates both simple and extended M3U formats
- **Duration calculation:** Calculates track durations based on CUE index positions
- **Flexible output options:** Supports relative or absolute file paths
- **Batch processing:** Can convert multiple CUE files at once
- **Error handling:** Handles encoding issues and missing files gracefully

Usage Examples:
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
How it works:

- **CueSheet class:** Represents the entire CUE file with metadata and tracks
- **CueTrack class:** Represents individual tracks with their properties
- **Parser:** Extracts information from CUE files using regex patterns
- **Converter:** Transforms parsed data into M3U format
- **CLI interface:** Provides command-line options for different use cases

The application handles common CUE file formats and generates standard M3U playlists that work with most media players. 
It preserves track information like titles and performers while maintaining proper file references.
