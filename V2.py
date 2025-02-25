import os

### ONLY WHILE I FIX THE FFMPEG PATH ISSUE
# ffmpeg_path = '/opt/homebrew/bin/ffmpeg'
# os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_path
# os.environ['FFMPEG_BINARY'] = ffmpeg_path
# from moviepy.config import change_settings
# change_settings({"IMAGEMAGICK_BINARY": "/opt/homebrew/bin/convert"})  # Update this 


import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import yt_dlp

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multiple Video Downloader")
        self.download_folder = ""
        self.create_widgets()

    def create_widgets(self):
        # Label for the URL text box
        tk.Label(self.root, text="Video URLs (one per line):").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        # Multi-line text box for URLs
        self.urls_text = scrolledtext.ScrolledText(self.root, wrap='word', width=60, height=10)
        self.urls_text.grid(row=1, column=0, columnspan=3, padx=10, pady=5)

        # Button to select destination folder
        tk.Button(self.root, text="Select Download Folder", command=self.select_folder).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.folder_label = tk.Label(self.root, text="No folder selected", fg="red")
        self.folder_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Checkbox for downloading audio only
        self.download_audio = tk.IntVar()
        tk.Checkbutton(self.root, text="Download Audio Only (MP3)", variable=self.download_audio).grid(row=3, column=0, padx=10, pady=5, sticky="w")

        # Button to start download
        tk.Button(self.root, text="Download Videos", command=self.start_download).grid(row=4, column=0, padx=10, pady=10, sticky="w")

        # Log area to display progress information
        tk.Label(self.root, text="Progress Log:").grid(row=5, column=0, sticky="w", padx=10)
        self.log_text = scrolledtext.ScrolledText(self.root, wrap='word', width=60, height=10, state='disabled')
        self.log_text.grid(row=6, column=0, columnspan=3, padx=10, pady=5)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.download_folder = folder
            self.folder_label.config(text=folder, fg="green")

    def start_download(self):
        # Get URLs, split on newlines and strip extra spaces
        urls = self.urls_text.get("1.0", tk.END).strip().splitlines()
        urls = [url.strip() for url in urls if url.strip()]
        if not urls:
            messagebox.showwarning("No URLs", "Please enter at least one video URL.")
            return
        if not self.download_folder:
            messagebox.showwarning("No Folder Selected", "Please select a download folder.")
            return

        # Start the download in a separate thread so the GUI remains responsive
        threading.Thread(target=self.download_videos, args=(urls,), daemon=True).start()

    def log(self, message):
        # Append message to the log text widget
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def download_videos(self, urls):
        # Setup yt_dlp options
        ydl_opts = {
            'outtmpl': self.download_folder + '/%(title)s.%(ext)s',
            'progress_hooks': [self.my_hook],
            'logger': MyLogger(self)
        }
        if self.download_audio.get():
            # If audio-only, get the best audio and convert to mp3 (requires ffmpeg)
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in urls:
                try:
                    self.log("Starting download: " + url)
                    ydl.download([url])
                    self.log("Finished download: " + url)
                except Exception as e:
                    self.log("Error downloading " + url + ": " + str(e))

    def my_hook(self, d):
        # This hook is called with status updates from yt_dlp
        if d.get('status') == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            if total:
                percent = downloaded / total * 100
                self.log("Downloading: {:.2f}%".format(percent))
        elif d.get('status') == 'finished':
            self.log("Download finished, post-processing...")

# Optional: Custom logger to log messages from yt_dlp
class MyLogger(object):
    def __init__(self, app):
        self.app = app

    def debug(self, msg):
        pass  # Uncomment the next line if you want debug messages in the log.
        self.app.log("DEBUG: " + msg)

    def warning(self, msg):
        self.app.log("WARNING: " + msg)

    def error(self, msg):
        self.app.log("ERROR: " + msg)

if __name__ == '__main__':
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()