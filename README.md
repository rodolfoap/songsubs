# Subtitle Creator for Guitar Backing Tracks

A simple Python tkinter application to create .srt subtitle files while playing music videos or audio files. Designed for guitarists who need to mark song sections (parts, solos, etc.) in real-time.

## Purpose

When playing guitar over music videos as backing tracks, subtitles help you know which section is coming next:
- Countdown: "4", "3", "2", "1"
- Song parts: "Part A1", "Part B", "Part C"
- Solos: "Solo 1/6", "Solo 2/6", etc.

This application lets you create these subtitles by pressing buttons while the song plays.

## Features

- Play MP3 audio and MP4 video files
- Customizable buttons loaded from `buttons.list` file
- Create subtitles in real-time by clicking buttons
- Playback controls: play, pause, stop, seek forward/backward, +30s/-30s skip
- Save and reload .srt files for editing
- Edit subtitle text by double-clicking
- Time slider to navigate through the song
- Waveform visualization for visual song navigation

## Installation

### System Requirements

Before installing, make sure you have:
- **VLC media player**: https://www.videolan.org/vlc/
- **ffmpeg** (required for waveform generation):
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Download from https://ffmpeg.org/

### Install from source

1. Clone or download this repository
2. Navigate to the project directory
3. Install the package:

```bash
# Install in development mode (recommended for development)
pip install -e .

# Or install normally
pip install .
```

### Install dependencies only

If you just want to run `main.py` without installing:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `buttons.list` file with one button label per line:

```
4
3
2
1
A
B
C
Solo
Finale
```

Each line creates a button in the application. When clicked during playback, it creates a subtitle starting from the current timestamp.

## Usage

### After installation

If you installed the package with `pip install .`:
```bash
guitar-subs
```

### Without installation

If you're running from source:
```bash
python main.py
```

### Using the application

1. Click "Select Media File" to choose your MP3 or MP4 file

2. Press Play and use the control buttons:
   - Play/Pause
   - Stop
   - << (back 5s), >> (forward 5s)
   - <<< (back 30s), >>> (forward 30s)
   - Time slider for seeking

4. As the song plays, click the part buttons (A, B, C, Solo, etc.) to mark sections

5. Click "Save SRT" to save your subtitle file

6. Click "Load SRT" to reload and edit existing subtitles

## Typical Jazz Song Structure

1. Countdown (4 or 8 measures)
2. Sequence of A, B, C parts (AABA, ABC, etc.)
3. N rounds of solos
4. Final sequence of parts + Finale

## Notes

- All subtitles occupy continuous time (no gaps)
- Each subtitle ends when the next one begins
- The last subtitle extends to the end of the song
- SRT files are saved with the same name as the media file
