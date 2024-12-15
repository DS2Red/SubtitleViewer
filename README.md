# Subtitle Viewer

A simple and efficient subtitle viewer application built with PyQt6.

## Features

- Supports multiple subtitle formats (.srt, .vtt, .ass, .ssa)
- Fullscreen mode
- Customizable fonts and colors
- Drag and drop subtitle files
- Subtitle list view with double-click to jump
- Auto-loops playback

## Installation

### Option 1: Download the Executable
1. Go to the [Releases](../../releases) page
2. Download the latest `SubtitleViewer.exe`
3. Run the executable directly - no installation needed

### Option 2: Run from Source
1. Clone this repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python subtitle_reader.py
   ```

## Usage

1. Open a subtitle file using the "Open Subtitle File" button or drag and drop
2. Click "Play Subtitles" to start playback
3. Use the customization options to adjust appearance
4. Toggle fullscreen mode with the "Fullscreen Subtitles" button

## Building from Source

To create your own executable:

1. Install requirements:
   ```
   pip install -r requirements.txt
   ```
2. Run the build script:
   ```
   python build_exe.py
   ```
3. Find the executable in the `dist` folder

## License

[MIT License](LICENSE) 