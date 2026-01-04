#!.venv/bin/python3
"""
Subtitle Creator for Backing Tracks
A tkinter application to create SRT subtitles while playing media files.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import vlc
import pysrt
import os
from pathlib import Path
import time
import numpy as np
import subprocess
import wave
import struct


class SubtitleCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Subtitle Creator for Backing Tracks")
        self.root.geometry("900x700")

        # VLC player setup
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

        # Application state
        self.media_file = None
        self.srt_file = None
        self.subtitles = []  # List of (start_time_ms, label) tuples
        self.is_playing = False
        self.buttons_config = []
        self.user_seeking = False  # Flag to indicate user is dragging slider
        self.waveform_data = None  # Waveform data for visualization
        self.position_line = None  # Canvas line for current position indicator

        # Load button configuration
        self.load_buttons_config()

        # Create UI
        self.create_ui()

        # Update timer
        self.update_time()

    def load_buttons_config(self):
        """Load button labels from buttons.list file"""
        buttons_file = Path("buttons.list")
        if buttons_file.exists():
            with open(buttons_file, 'r') as f:
                self.buttons_config = [line.strip() for line in f if line.strip()]
        else:
            # Default buttons
            self.buttons_config = ["4", "3", "2", "1", "A", "B", "C", "Solo", "Finale"]

    def create_ui(self):
        """Create the user interface"""
        # Top frame - File selection
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Select Media File", command=self.select_media).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(top_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=5)

        # Video/Media frame (placeholder for video or album art)
        self.media_frame = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=2)
        self.media_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        media_label = ttk.Label(self.media_frame, text="Media Player\n(Video will play here)",
                               anchor=tk.CENTER, font=('Arial', 14))
        media_label.pack(expand=True)

        # Time slider and waveform container
        slider_container = ttk.Frame(self.root, padding="5")
        slider_container.pack(fill=tk.X, padx=10)

        # Time label on the left
        self.time_label = ttk.Label(slider_container, text="00:00 / 00:00")
        self.time_label.pack(side=tk.LEFT, padx=5)

        # Right side container for slider and waveform (same width)
        slider_waveform_container = ttk.Frame(slider_container)
        slider_waveform_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Slider on top
        self.time_slider = ttk.Scale(slider_waveform_container, from_=0, to=100, orient=tk.HORIZONTAL)
        self.time_slider.pack(fill=tk.X, expand=True)
        self.time_slider.bind("<Button-1>", self.on_slider_press)
        self.time_slider.bind("<ButtonRelease-1>", self.on_slider_release)

        # Waveform canvas directly below slider (same width)
        self.waveform_canvas = tk.Canvas(slider_waveform_container, height=80, bg='#2b2b2b', highlightthickness=0)
        self.waveform_canvas.pack(fill=tk.X, expand=True, pady=(2, 0))
        self.waveform_canvas.bind("<Button-1>", self.on_waveform_click)

        # Playback controls
        control_frame = ttk.Frame(self.root, padding="5")
        control_frame.pack(fill=tk.X, padx=10)

        ttk.Button(control_frame, text="<<<", command=lambda: self.seek(-30000),
                  width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="<<", command=lambda: self.seek(-5000),
                  width=5).pack(side=tk.LEFT, padx=2)
        self.play_button = ttk.Button(control_frame, text="Play", command=self.play_pause,
                                     width=8)
        self.play_button.pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Stop", command=self.stop,
                  width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text=">>", command=lambda: self.seek(5000),
                  width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text=">>>", command=lambda: self.seek(30000),
                  width=5).pack(side=tk.LEFT, padx=2)
        
        # Speed control
        self.speed_button = ttk.Button(control_frame, text="1x", command=self.toggle_speed, width=4)
        self.speed_button.pack(side=tk.LEFT, padx=5)

        # Subtitle buttons frame
        button_frame = ttk.LabelFrame(self.root, text="Subtitle Buttons", padding="10")
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create subtitle buttons from config
        row_frame = None
        for i, label in enumerate(self.buttons_config):
            if i % 9 == 0:  # 9 buttons per row
                row_frame = ttk.Frame(button_frame)
                row_frame.pack(fill=tk.X, pady=2)

            btn = ttk.Button(row_frame, text=label,
                           command=lambda l=label: self.add_subtitle(l),
                           width=8)
            btn.pack(side=tk.LEFT, padx=2)

        # Subtitle list frame
        list_frame = ttk.LabelFrame(self.root, text="Subtitles", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox for subtitles
        self.subtitle_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                          font=('Courier', 10))
        self.subtitle_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.subtitle_listbox.yview)

        # Bind double-click to edit subtitle
        self.subtitle_listbox.bind("<Double-Button-1>", self.edit_subtitle)

        # Bottom frame - Save/Load buttons
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="Save SRT", command=self.save_srt).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Load SRT", command=self.load_srt).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Clear All", command=self.clear_subtitles).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)

    def select_media(self):
        """Open file dialog to select media file"""
        filename = filedialog.askopenfilename(
            title="Select Media File",
            filetypes=[
                ("Media files", "*.mp3 *.mp4 *.wav *.avi *.mkv"),
                ("MP3 files", "*.mp3"),
                ("MP4 files", "*.mp4"),
                ("All files", "*.*")
            ]
        )

        if filename:
            self.media_file = filename
            self.file_label.config(text=os.path.basename(filename))

            # Set up SRT filename
            base_name = os.path.splitext(filename)[0]
            self.srt_file = base_name + ".srt"

            # Load media
            media = self.vlc_instance.media_new(filename)
            self.player.set_media(media)

            # Try to embed video in the frame
            if filename.lower().endswith(('.mp4', '.avi', '.mkv')):
                # Get the window ID for video embedding
                win_id = self.media_frame.winfo_id()
                self.player.set_xwindow(win_id)

            # Generate waveform
            self.generate_waveform(filename)

            # Auto-load SRT if exists
            if os.path.exists(self.srt_file):
                self.load_srt()

    def play_pause(self):
        """Toggle play/pause"""
        if not self.media_file:
            messagebox.showwarning("No Media", "Please select a media file first")
            return

        if self.is_playing:
            self.player.pause()
            self.play_button.config(text="Play")
            self.is_playing = False
        else:
            self.player.play()
            self.play_button.config(text="Pause")
            self.is_playing = True

    def stop(self):
        """Stop playback"""
        self.player.stop()
        self.play_button.config(text="Play")
        self.is_playing = False

    def toggle_speed(self):
        """Toggle playback speed between 1x and 2x"""
        if not self.player:
            return
            
        current_rate = self.player.get_rate()
        # Allow some float tolerance
        if abs(current_rate - 1.0) < 0.1:
            new_rate = 2.0
            text = "2x"
        else:
            new_rate = 1.0
            text = "1x"
            
        self.player.set_rate(new_rate)
        self.speed_button.config(text=text)

    def seek(self, ms):
        """Seek forward or backward by milliseconds"""
        current_time = self.player.get_time()
        if current_time >= 0:
            new_time = max(0, current_time + ms)
            self.player.set_time(int(new_time))

    def on_slider_press(self, event):
        """Handle slider press (jump to exact click position)"""
        self.user_seeking = True

        # Calculate exact position based on click coordinates
        slider_width = self.time_slider.winfo_width()
        click_x = event.x

        # Calculate percentage (0-100)
        if slider_width > 0:
            percentage = (click_x / slider_width) * 100
            percentage = max(0, min(100, percentage))  # Clamp to 0-100

            # Set slider to clicked position
            self.time_slider.set(percentage)

            # Seek immediately
            if self.player and self.player.get_length() > 0:
                position = percentage / 100.0
                self.player.set_position(position)

    def on_slider_release(self, event):
        """Handle slider release (seek to position)"""
        if self.player and self.player.get_length() > 0:
            value = self.time_slider.get()
            position = float(value) / 100.0
            self.player.set_position(position)
        self.user_seeking = False

    def update_time(self):
        """Update time display and slider"""
        if self.player:
            current_time = self.player.get_time()
            total_time = self.player.get_length()

            if current_time >= 0 and total_time > 0:
                # Update label
                current_str = self.ms_to_time_str(current_time)
                total_str = self.ms_to_time_str(total_time)
                self.time_label.config(text=f"{current_str} / {total_str}")

                # Update slider only if user is not interacting with it
                if not self.user_seeking:
                    position = (current_time / total_time) * 100
                    self.time_slider.set(position)

                # Update position line on waveform
                if self.position_line and self.waveform_data is not None:
                    canvas_width = self.waveform_canvas.winfo_width()
                    canvas_height = self.waveform_canvas.winfo_height()

                    if canvas_width > 1 and canvas_height > 1:
                        # Calculate x position based on current time
                        x_pos = (current_time / total_time) * canvas_width

                        # Update the line coordinates
                        self.waveform_canvas.coords(
                            self.position_line,
                            x_pos, 0,
                            x_pos, canvas_height
                        )

        # Schedule next update
        self.root.after(100, self.update_time)

    def ms_to_time_str(self, ms):
        """Convert milliseconds to MM:SS format"""
        seconds = int(ms / 1000)
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def add_subtitle(self, label):
        """Add a subtitle at the current playback position"""
        if not self.media_file:
            messagebox.showwarning("No Media", "Please select a media file first")
            return

        current_time = self.player.get_time()
        if current_time < 0:
            current_time = 0

        # Add to subtitles list
        self.subtitles.append((current_time, label))
        self.subtitles.sort(key=lambda x: x[0])

        # Update listbox
        self.update_subtitle_listbox()

    def update_subtitle_listbox(self):
        """Update the subtitle listbox display"""
        self.subtitle_listbox.delete(0, tk.END)

        for i, (time_ms, label) in enumerate(self.subtitles):
            time_str = self.ms_to_srt_time(time_ms)
            self.subtitle_listbox.insert(tk.END, f"{i+1:3d}  {time_str}  ->  {label}")

    def ms_to_srt_time(self, ms):
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)"""
        seconds = int(ms / 1000)
        millis = int(ms % 1000)
        mins = seconds // 60
        secs = seconds % 60
        hours = mins // 60
        mins = mins % 60
        return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def srt_time_to_ms(self, srt_time):
        """Convert SRT time to milliseconds"""
        # Format: HH:MM:SS,mmm
        time_part, millis = srt_time.split(',')
        h, m, s = map(int, time_part.split(':'))
        return (h * 3600 + m * 60 + s) * 1000 + int(millis)

    def save_srt(self):
        """Save subtitles to SRT file"""
        if not self.subtitles:
            messagebox.showwarning("No Subtitles", "No subtitles to save")
            return

        if not self.srt_file:
            filename = filedialog.asksaveasfilename(
                defaultextension=".srt",
                filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
            )
            if not filename:
                return
            self.srt_file = filename

        # Create SRT file
        subs = pysrt.SubRipFile()

        # Get total duration
        total_time = self.player.get_length()
        if total_time <= 0:
            total_time = 300000  # Default 5 minutes if can't determine

        for i, (start_time, label) in enumerate(self.subtitles):
            # End time is the start of next subtitle, or end of media
            if i < len(self.subtitles) - 1:
                end_time = self.subtitles[i + 1][0]
            else:
                end_time = total_time

            # Create subtitle item
            item = pysrt.SubRipItem(
                index=i + 1,
                start=self.ms_to_srt_time(start_time),
                end=self.ms_to_srt_time(end_time),
                text=label
            )
            subs.append(item)

        # Save file
        subs.save(self.srt_file, encoding='utf-8')
        messagebox.showinfo("Success", f"Subtitles saved to {os.path.basename(self.srt_file)}")

    def load_srt(self):
        """Load subtitles from SRT file"""
        if not self.srt_file or not os.path.exists(self.srt_file):
            filename = filedialog.askopenfilename(
                title="Select SRT File",
                filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
            )
            if not filename:
                return
            self.srt_file = filename

        try:
            subs = pysrt.open(self.srt_file, encoding='utf-8')

            # Clear current subtitles
            self.subtitles = []

            # Load subtitles
            for item in subs:
                start_time = self.srt_time_to_ms(str(item.start))
                label = item.text.strip()
                self.subtitles.append((start_time, label))

            self.subtitles.sort(key=lambda x: x[0])
            self.update_subtitle_listbox()

            messagebox.showinfo("Success", f"Loaded {len(self.subtitles)} subtitles")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load SRT file: {str(e)}")

    def clear_subtitles(self):
        """Clear all subtitles"""
        if messagebox.askyesno("Confirm", "Clear all subtitles?"):
            self.subtitles = []
            self.update_subtitle_listbox()

    def delete_selected(self):
        """Delete selected subtitle"""
        selection = self.subtitle_listbox.curselection()
        if selection:
            idx = selection[0]
            del self.subtitles[idx]
            self.update_subtitle_listbox()

    def edit_subtitle(self, event):
        """Edit selected subtitle text"""
        selection = self.subtitle_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        time_ms, old_label = self.subtitles[idx]

        # Create a simple dialog to edit the text
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Subtitle")
        dialog.geometry("400x150")
        dialog.transient(self.root)

        # Wait for dialog to be visible before grabbing
        dialog.update_idletasks()
        dialog.grab_set()

        ttk.Label(dialog, text=f"Time: {self.ms_to_srt_time(time_ms)}",
                 font=('Arial', 10)).pack(pady=10)

        ttk.Label(dialog, text="Subtitle Text:").pack(pady=5)

        text_var = tk.StringVar(value=old_label)
        entry = ttk.Entry(dialog, textvariable=text_var, width=40, font=('Arial', 12))
        entry.pack(pady=5)
        entry.focus()
        entry.select_range(0, tk.END)

        def save_edit():
            new_label = text_var.get().strip()
            if new_label:
                self.subtitles[idx] = (time_ms, new_label)
                self.update_subtitle_listbox()
                dialog.destroy()

        def cancel_edit():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=save_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel_edit).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to save
        entry.bind("<Return>", lambda e: save_edit())
        entry.bind("<Escape>", lambda e: cancel_edit())

    def generate_waveform(self, filename):
        """Generate waveform data from audio file"""
        try:
            # Show loading message
            self.waveform_canvas.delete("all")
            canvas_width = self.waveform_canvas.winfo_width()
            if canvas_width <= 1:
                canvas_width = 800  # Default width

            self.waveform_canvas.create_text(
                canvas_width // 2, 40,
                text="Generating waveform...",
                fill="white",
                font=('Arial', 10)
            )
            self.root.update()

            # Use ffmpeg to extract audio as WAV
            import tempfile
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav_path = temp_wav.name
            temp_wav.close()

            # Convert to mono WAV using ffmpeg
            cmd = [
                'ffmpeg', '-i', filename,
                '-ac', '1',  # mono
                '-ar', '22050',  # 22kHz sample rate (good enough for visualization)
                '-y',  # overwrite
                temp_wav_path
            ]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                raise Exception(f"ffmpeg conversion failed: {error_msg}")

            # Read WAV file
            with wave.open(temp_wav_path, 'rb') as wav_file:
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()

                # Read all frames
                frames = wav_file.readframes(n_frames)

                # Convert to numpy array based on sample width
                if sample_width == 1:
                    dtype = np.uint8
                    samples = np.frombuffer(frames, dtype=dtype).astype(float)
                    samples = (samples - 128) / 128.0
                elif sample_width == 2:
                    dtype = np.int16
                    samples = np.frombuffer(frames, dtype=dtype).astype(float)
                    samples = samples / 32768.0
                elif sample_width == 4:
                    dtype = np.int32
                    samples = np.frombuffer(frames, dtype=dtype).astype(float)
                    samples = samples / 2147483648.0
                else:
                    raise Exception(f"Unsupported sample width: {sample_width}")

            # Clean up temp file
            os.unlink(temp_wav_path)

            # Downsample for visualization (2000 points)
            target_points = 2000
            if len(samples) > target_points:
                chunk_size = len(samples) // target_points
                waveform = []
                for i in range(0, len(samples), chunk_size):
                    chunk = samples[i:i + chunk_size]
                    if len(chunk) > 0:
                        rms = np.sqrt(np.mean(chunk ** 2))
                        waveform.append(rms)
                self.waveform_data = np.array(waveform[:target_points])
            else:
                self.waveform_data = samples

            # Normalize waveform to use full vertical space
            if len(self.waveform_data) > 0:
                max_amplitude = np.max(np.abs(self.waveform_data))
                if max_amplitude > 0:
                    # Normalize to 0.9 to use 90% of available space
                    self.waveform_data = (self.waveform_data / max_amplitude) * 0.9

            # Draw waveform
            self.draw_waveform()

        except Exception as e:
            print(f"Error generating waveform: {e}")
            import traceback
            traceback.print_exc()
            self.waveform_canvas.delete("all")
            canvas_width = self.waveform_canvas.winfo_width()
            if canvas_width <= 1:
                canvas_width = 800
            self.waveform_canvas.create_text(
                canvas_width // 2, 40,
                text="Could not generate waveform",
                fill="gray",
                font=('Arial', 10)
            )

    def draw_waveform(self):
        """Draw waveform on canvas"""
        self.waveform_canvas.delete("all")

        if self.waveform_data is None or len(self.waveform_data) == 0:
            return

        canvas_width = self.waveform_canvas.winfo_width()
        canvas_height = self.waveform_canvas.winfo_height()

        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 80

        center_y = canvas_height / 2

        # Draw waveform
        num_points = len(self.waveform_data)
        for i in range(num_points):
            x = (i / num_points) * canvas_width
            amplitude = self.waveform_data[i]
            # Use full height (already normalized to 0.9 in generate_waveform)
            height = amplitude * (canvas_height / 2)

            # Draw line from center
            self.waveform_canvas.create_line(
                x, center_y - height,
                x, center_y + height,
                #fill='#4CAF50',
                fill='#00FF00',
                width=1
            )

        # Draw center line
        self.waveform_canvas.create_line(
            0, center_y,
            canvas_width, center_y,
            fill='#555555',
            width=1
        )

        # Create position indicator line (white vertical line)
        self.position_line = self.waveform_canvas.create_line(
            0, 0,
            0, canvas_height,
            fill='white',
            width=2
        )

    def on_waveform_click(self, event):
        """Handle click on waveform to seek"""
        if not self.media_file or not self.player:
            return

        canvas_width = self.waveform_canvas.winfo_width()
        click_x = event.x

        if canvas_width > 0:
            percentage = (click_x / canvas_width) * 100
            percentage = max(0, min(100, percentage))

            # Update slider
            self.time_slider.set(percentage)

            # Seek
            if self.player.get_length() > 0:
                position = percentage / 100.0
                self.player.set_position(position)


def main():
    root = tk.Tk()
    app = SubtitleCreatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
