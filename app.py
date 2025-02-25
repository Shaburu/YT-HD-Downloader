import os
import threading
import time
from queue import Queue, Empty

from flask import Flask, render_template_string, request, Response, redirect, url_for

import yt_dlp

# --- Configuration ---
# Define a download folder on the server (it will be created if missing)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Optionally set FFMPEG/IMAGEMAGICK environment variables if needed:
# ffmpeg_path = '/opt/homebrew/bin/ffmpeg'
# os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_path
# os.environ['FFMPEG_BINARY'] = ffmpeg_path
# from moviepy.config import change_settings
# change_settings({"IMAGEMAGICK_BINARY": "/opt/homebrew/bin/convert"})

# --- Flask App Setup ---
app = Flask(__name__)
# A global message queue to stream log messages to the client.
message_queue = Queue()

# --- Templates (inline for minimal external usage) ---

BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{ title|default("Video Downloader") }}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    /* Minimal CSS inspired by shadcn-ui aesthetics */
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
{% block content %}
  <h1>Multiple Video Downloader</h1>
  <form action="{{ url_for('start_download') }}" method="POST">
    <label for="urls">Video URLs (one per line):</label>
    <textarea id="urls" name="urls" rows="8" placeholder="Enter one URL per line"></textarea>
    
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
// Connect to server-sent events for real-time log streaming.
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

# --- Video Downloading Logic ---
#
# Instead of Tkinter updates, all logs are written to a message_queue.
#
def log_message(message):
    """Push a log message to the global queue."""
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
    """Custom logger to pass yt_dlp logs to our queue."""
    def debug(self, msg):
        # Uncomment the next line to show debug messages.
        # log_message("DEBUG: " + msg)
        pass

    def warning(self, msg):
        log_message("WARNING: " + msg)

    def error(self, msg):
        log_message("ERROR: " + msg)

def download_videos(urls, download_audio):
    """Download multiple videos using yt_dlp and write progress logs."""
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
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
    # Signal to the client streaming endpoint that processing is complete.
    log_message("###EOF###")

def start_download_thread(urls, download_audio):
    threading.Thread(target=download_videos, args=(urls, download_audio), daemon=True).start()

# --- Flask Routes ---
@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/start", methods=["POST"])
def start_download():
    urls_raw = request.form.get("urls", "")
    urls = [line.strip() for line in urls_raw.splitlines() if line.strip()]
    if not urls:
        # If no URLs were provided, redirect back with a message (for simplicity, using plain text)
        return "Error: No URLs provided. Please go back and enter at least one URL."
    download_audio = (request.form.get("download_audio") == "on")
    # Clear the message queue before starting the download.
    with message_queue.mutex:
        message_queue.queue.clear()
    # Start the background download thread.
    start_download_thread(urls, download_audio)
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
                # No message yet; loop and wait.
                continue
    return Response(event_stream(), mimetype="text/event-stream")

# Provide base template so that render_template_string can extend it.
@app.context_processor
def base():
    return dict()

@app.before_first_request
def setup_templates():
    # Register our base template.
    app.jinja_loader.mapping = {"base.html": BASE_HTML}

if __name__ == '__main__':
    app.run(debug=True)
