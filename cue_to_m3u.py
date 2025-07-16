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


def main():
    """Main function to handle command-line interface."""
    parser = argparse.ArgumentParser(
        description="Convert CUE sheet files to M3U playlists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cue_to_m3u.py album.cue
  python cue_to_m3u.py album.cue -o playlist.m3u
  python cue_to_m3u.py album.cue --simple --absolute
  python cue_to_m3u.py *.cue --batch
        """
    )
    
    parser.add_argument('input', nargs='+', help='CUE file(s) to convert')
    parser.add_argument('-o', '--output', help='Output M3U file path')
    parser.add_argument('--simple', action='store_true', 
                       help='Generate simple M3U format (no extended info)')
    parser.add_argument('--absolute', action='store_true',
                       help='Use absolute paths instead of relative paths')
    parser.add_argument('--batch', action='store_true',
                       help='Process multiple files in batch mode')
    
    args = parser.parse_args()
    
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
    
    return 0


if __name__ == "__main__":
    exit(main())