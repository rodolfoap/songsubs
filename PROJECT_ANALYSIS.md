# Project Analysis: songsubs

## Overview
`songsubs` is a Python/Tkinter application for creating `.srt` subtitles in real-time while playing audio/video. It leverages `python-vlc` for playback and `pysrt` for subtitle management.

## Code Structure
- **`main.py`**: Contains the entire application logic, including UI setup (`SubtitleCreatorApp`), media handling, waveform generation, and subtitle management.
- **`buttons.list`**: Configuration file for UI buttons.
- **`requirements.txt`**: Project dependencies.

## Key Findings & Issues

### 1. Performance & Responsiveness
- **Blocking Waveform Generation**: The `generate_waveform` method runs `ffmpeg` and processes audio data synchronously on the main UI thread. For large files, this will freeze the application ("Not Responding") until processing is complete.
- **Waveform Drawing**: Drawing thousands of lines on a `tk.Canvas` can be slow.

### 2. Dependencies
- **System Dependencies**: Requires `ffmpeg` and `VLC` installed on the system. The application might crash or fail silently if these are missing, though there are some checks.
- **VLC Integration**: Embedding VLC windows can be tricky across different OSs (Windows/Linux/macOS). Currently handles embedding for MP4/AVI/MKV but might have platform-specific quirks (e.g. macOS Tkinter/VLC interaction).

### 3. Code Organization
- **Monolithic Class**: `SubtitleCreatorApp` handles everything: UI, logic, file I/O, audio processing. Splitting this into `Player`, `WaveformGenerator`, and `SubtitleManager` classes would improve maintainability.
- **Hardcoded Values**: Waveform sample rate (22050Hz), target points (2000), and color schemes are hardcoded.

### 4. User Experience
- **Error Feedback**: Basic error messages.
- **Undo/Redo**: No undo functionality for adding/deleting subtitles, other than "Delete Selected".

## Proposed Improvements
1.  **Async Waveform Generation**: Move `ffmpeg` and data processing to a background thread to keep the UI responsive.
2.  **Refactoring**: Extract `WaveformGenerator` and `VideoPlayer` logic into separate classes/files.
3.  **Configuration**: Move hardcoded colors and settings to a configuration dictionary or file.
4.  **Better Error Handling**: Check for `ffmpeg` availability on startup and provide clear instructions if missing.
