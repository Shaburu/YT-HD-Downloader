import os
import threading
from queue import Queue, Empty
from flask import Flask, render_template_string, request, Response, redirect, url_for
from jinja2 import DictLoader, ChoiceLoader
import yt_dlp
import tkinter as tk
from tkinter import filedialog
import webbrowser
import logging

# --- Configure Logging ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DEFAULT_DOWNLOAD_FOLDER, exist_ok=True)

# --- Flask App Setup ---
app = Flask(__name__)
message_queue = Queue()
folder_queue = Queue()  # Queue to communicate folder path from Tkinter to Flask

# --- Templates ---
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{ title|default("Video Downloader") }}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      --bg-color: #f9fafb;
      --primary-color: #6366f1;
      --text-color: #1f2937;
      --border-color: #e5e7eb;
      --radius: 6px;
      --padding: 0.75rem;
      --font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    body {
      margin: 0;
      font-family: var(--font-family);
      background-color: var(--bg-color);
      color: var(--text-color);
      display: flex;
      justify-content: center;
      padding: 2rem;
    }
    .container {
      background: #fff;
      padding: 2rem;
      border: 1px solid var(--border-color);
      border-radius: var(--radius);
      max-width: 800px;
      width: 100%;
      box-shadow: 0 10px 15px rgba(0,0,0,0.1);
    }
    h1 {
      margin-top: 0;
      font-size: 1.75rem;
    }
    textarea, input[type="text"] {
      width: 100%;
      padding: var(--padding);
      border: 1px solid var(--border-color);
      border-radius: var(--radius);
      margin-bottom: 1rem;
      font-size: 1rem;
    }
    label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 600;
    }
    .checkbox-group {
      margin-bottom: 1rem;
    }
    button {
      padding: var(--padding) 1.5rem;
      background-color: var(--primary-color);
      color: white;
      border: none;
      border-radius: var(--radius);
      cursor: pointer;
      font-size: 1rem;
    }
    button:hover {
      opacity: 0.9;
    }
    .log {
      background: #f3f4f6;
      border: 1px solid var(--border-color);
      padding: var(--padding);
      border-radius: var(--radius);
      height: 300px;
      overflow-y: auto;
      white-space: pre-wrap;
      font-family: monospace;
      font-size: 0.9rem;
    }
  </style>
  {% block head %}{% endblock %}
</head>
<body>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
</body>
</html>
"""

INDEX_HTML = """
{% extends "base.html" %}
{% block head %}
<script>
function openFolderPicker() {
  console.log("Opening folder picker...");
  fetch('/pick_folder', { method: 'POST' })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok: ' + response.statusText);
      }
      return response.text();
    })
    .then(path => {
      console.log("Received path:", path);
      if (path) {
        document.getElementById('folder').value = path;
      } else {
        console.log("No path returned");
      }
    })
    .catch(error => {
      console.error("Error fetching folder path:", error);
      alert("Failed to select folder: " + error.message);
    });
}
</script>
{% endblock %}
{% block content %}
  <h1>Multiple Video Downloader</h1>
  <form action="{{ url_for('start_download') }}" method="POST">
    <label for="folder">Download Folder:</label>
    <input type="text" id="folder" name="folder" value="{{ default_folder }}" required readonly>
    <button type="button" onclick="openFolderPicker()">Select Folder</button>
    
    <label for="urls">Video URLs (one per line):</label>
    <textarea id="urls" name="urls" rows="8" placeholder="Enter one URL per line" required></textarea>
    
    <div class="checkbox-group">
      <input type="checkbox" id="download_audio" name="download_audio">
      <label for="download_audio" style="display:inline;">Download Audio Only (MP3)</label>
    </div>
    
    <button type="submit">Download Videos</button>
  </form>
{% endblock %}
"""

PROGRESS_HTML = """
{% extends "base.html" %}
{% block head %}
<script>
document.addEventListener("DOMContentLoaded", function(){
  var logArea = document.getElementById("log");
  var evtSource = new EventSource("{{ url_for('stream') }}");
  evtSource.onmessage = function(e) {
    if(e.data === "###EOF###") {
      evtSource.close();
    } else {
      logArea.textContent += e.data + "\\n";
      logArea.scrollTop = logArea.scrollHeight;
    }
  };
});
</script>
{% endblock %}
{% block content %}
  <h1>Download Progress</h1>
  <div id="log" class="log"></div>
  <p><a href="{{ url_for('index') }}">Back to Home</a></p>
{% endblock %}
"""

# --- Configure Jinja2 Loader ---
app.jinja_loader = ChoiceLoader([
    DictLoader({"base.html": BASE_HTML}),
    app.jinja_loader,
])

# --- Video Downloading Logic ---
def log_message(message):
    message_queue.put(message)

def yt_dlp_hook(d):
    if d.get("status") == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0)
        if total:
            percent = downloaded / total * 100
            log_message("Downloading: {:.2f}%".format(percent))
    elif d.get("status") == "finished":
        log_message("Download finished, post-processing...")

class QueueLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        log_message("WARNING: " + msg)
    def error(self, msg):
        log_message("ERROR: " + msg)

def download_videos(urls, download_audio, folder):
    os.makedirs(folder, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'progress_hooks': [yt_dlp_hook],
        'logger': QueueLogger()
    }
    if download_audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                log_message("Starting download: " + url)
                ydl.download([url])
                log_message("Finished download: " + url)
            except Exception as e:
                log_message("Error downloading " + url + ": " + str(e))
    log_message("###EOF###")

def start_download_thread(urls, download_audio, folder):
    threading.Thread(target=download_videos, args=(urls, download_audio, folder), daemon=True).start()

# --- Flask Routes ---
@app.route("/")
def index():
    logging.debug("Rendering index page")
    return render_template_string(INDEX_HTML, default_folder=DEFAULT_DOWNLOAD_FOLDER)

@app.route("/pick_folder", methods=["POST"])
def pick_folder():
    logging.debug("Received request to pick folder")
    # Clear the queue to ensure we get the latest selection
    with folder_queue.mutex:
        folder_queue.queue.clear()
    # Signal Tkinter to pick a folder
    root.event_generate("<<PickFolder>>")
    try:
        folder_path = folder_queue.get(timeout=5)  # Wait up to 5 seconds
        logging.debug(f"Returning folder path: {folder_path}")
        return folder_path
    except Empty:
        logging.error("Timeout waiting for folder selection")
        return ""

@app.route("/start", methods=["POST"])
def start_download():
    folder = request.form.get("folder", "").strip()
    urls_raw = request.form.get("urls", "")
    urls = [line.strip() for line in urls_raw.splitlines() if line.strip()]
    
    if not folder:
        return "Error: No folder path provided. Please select a folder."
    if not urls:
        return "Error: No URLs provided. Please enter at least one URL."
    if not os.path.exists(folder):
        return "Error: Invalid folder path. Please select a valid folder."
    
    download_audio = (request.form.get("download_audio") == "on")
    with message_queue.mutex:
        message_queue.queue.clear()
    start_download_thread(urls, download_audio, folder)
    return render_template_string(PROGRESS_HTML)

@app.route("/stream")
def stream():
    def event_stream():
        while True:
            try:
                message = message_queue.get(timeout=1.0)
                yield f"data: {message}\n\n"
                if message == "###EOF###":
                    break
            except Empty:
                continue
    return Response(event_stream(), mimetype="text/event-stream")

# --- Tkinter and Flask Integration ---
def run_flask():
    app.run(debug=True, use_reloader=False, threaded=True, host="127.0.0.1", port=5000)

def pick_folder_handler(event):
    folder_path = filedialog.askdirectory(initialdir=DEFAULT_DOWNLOAD_FOLDER, title="Select Download Folder")
    logging.debug(f"Folder selected: {folder_path}")
    folder_queue.put(folder_path if folder_path else "")

def main():
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Open browser
    threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    # Set up Tkinter in the main thread
    global root
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.bind("<<PickFolder>>", pick_folder_handler)
    
    # Run Tkinter event loop
    logging.debug("Starting Tkinter main loop")
    root.mainloop()

if __name__ == "__main__":
    main()