import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pytube import YouTube
import threading
import os

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("600x400")
        
        # Variables
        self.urls = []
        self.download_path = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        
        # UI Components
        self.create_widgets()
        
    def create_widgets(self):
        # URL Input Frame
        url_frame = ttk.Frame(self.root, padding="10")
        url_frame.pack(fill="x")
        
        ttk.Label(url_frame, text="YouTube URLs (one per line):").pack(anchor="w")
        self.url_text = tk.Text(url_frame, height=5, width=50)
        self.url_text.pack(fill="x", pady=5)
        
        # Download Path Frame
        path_frame = ttk.Frame(self.root, padding="10")
        path_frame.pack(fill="x")
        
        ttk.Label(path_frame, text="Download Path:").pack(anchor="w")
        ttk.Entry(path_frame, textvariable=self.download_path, width=50).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame, text="Browse", command=self.browse_path).pack(side="right", padx=5)
        
        # Progress Frame
        progress_frame = ttk.Frame(self.root, padding="10")
        progress_frame.pack(fill="x")
        
        self.progress = ttk.Progressbar(progress_frame, length=400, mode="determinate")
        self.progress.pack(fill="x")
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(pady=5)
        
        # Buttons Frame
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Add URLs", command=self.add_urls).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Download", command=self.start_download).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_urls).pack(side="left", padx=5)
        
        # Log Frame
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill="both", expand=True)
        
        ttk.Label(log_frame, text="Log:").pack(anchor="w")
        self.log_text = tk.Text(log_frame, height=10, width=50)
        self.log_text.pack(fill="both", expand=True)
        
    def browse_path(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
            
    def add_urls(self):
        urls = self.url_text.get("1.0", tk.END).strip().split("\n")
        for url in urls:
            if url.strip() and url not in self.urls:
                self.urls.append(url.strip())
                self.log(f"Added URL: {url}")
        self.url_text.delete("1.0", tk.END)
        
    def clear_urls(self):
        self.urls.clear()
        self.log_text.delete("1.0", tk.END)
        self.status_label.config(text="Ready")
        self.progress["value"] = 0
        
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        
    def download_video(self, url, index, total):
        try:
            yt = YouTube(url)
            stream = yt.streams.get_highest_resolution()
            self.log(f"Downloading: {yt.title}")
            stream.download(output_path=self.download_path.get())
            self.progress["value"] = ((index + 1) / total) * 100
            self.status_label.config(text=f"Completed {index + 1}/{total}")
            self.log(f"Finished: {yt.title}")
        except Exception as e:
            self.log(f"Error downloading {url}: {str(e)}")
            
    def start_download(self):
        if not self.urls:
            messagebox.showwarning("Warning", "Please add some URLs first!")
            return
            
        self.progress["value"] = 0
        self.status_label.config(text="Downloading...")
        self.log_text.delete("1.0", tk.END)
        
        def download_thread():
            total = len(self.urls)
            for i, url in enumerate(self.urls):
                self.download_video(url, i, total)
            self.status_label.config(text="Download Complete!")
            messagebox.showinfo("Success", "All downloads completed!")
            
        threading.Thread(target=download_thread, daemon=True).start()

def main():
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        import pytube
    except ImportError:
        print("pytube is not installed. Installing now...")
        import subprocess
        subprocess.check_call(["pip", "install", "pytube"])
    main()