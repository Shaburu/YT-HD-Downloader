# 🎥 YT HD Downloader 🚀

A simple and elegant local YouTube high-definition downloader! 🎬  
Tired of unreliable online downloaders getting taken down? This tool puts you in full control, running on your own machine. Download single or multiple videos effortlessly with a clean and friendly interface.

---

## 🌟 Live Demo  
**[COMING SOON]**

---

## 🖥️ UI Preview

### Batch Download, Get only MP3, Fully HD, Select folder
![image](https://github.com/user-attachments/assets/df4d4439-af26-454f-92a0-9d2366834d37)

### Get detailed Logs
![image](https://github.com/user-attachments/assets/54c696fc-fbe6-40cd-9a82-2cf894e8f769)


---

## ⚙️ Features

- 🎯 Download videos in high definition (HD)  
- 🎵 Option to download only audio as MP3  
- 📥 Batch download multiple videos by pasting URLs (one per line)  
- 📂 Easily select your download folder using a folder picker  
- 📊 Real-time download progress displayed in the browser  
- 💻 Runs locally with a lightweight Flask web server and Tkinter for folder selection  
- 🔄 Automatically opens your default web browser for a seamless experience  
- 📦 Saves downloaded files cleanly, named by video title  

---

## 🛠️ Technology Used

- **Python** 🐍 – Backend scripting  
- **Flask** – Lightweight web framework powering the local web UI  
- **yt-dlp** – Powerful YouTube and video downloader library  
- **Tkinter** – Native GUI toolkit for folder selection dialog  
- **HTML + CSS + JavaScript** – For the responsive and clean frontend interface  

---

## 🚀 How to Setup & Run

### Prerequisites

- Python 3.7 or higher installed on your system  
- `pip` package manager to install dependencies  

### Installation Steps

1. **Clone or download this repository:**

   ```bash
   git clone https://github.com/yourusername/yt-hd-downloader.git
   cd yt-hd-downloader
   ```
2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate

3. **Install required Python packages:**
```bash
pip install flask yt-dlp
```

### Running the Downloader

Run the Python script:
```bash
python your_script_name.py
```

> This starts a local web server on http://127.0.0.1:5000
> Your default web browser will open automatically with the downloader UI.
> Use the Select Folder button to choose where to save videos.
> Paste one or more YouTube video URLs (each on a new line).
> Choose if you want to download audio only (MP3) or full videos.
> Click Download Videos to begin.
> Monitor real-time progress in the web interface.

📝 Notes
Downloads are saved by default to the downloads folder inside your current working directory. You may change it before downloading.
The app handles download errors gracefully and shows messages in the UI log.
Since this is a local app, your videos and data never leave your machine!
🙌 Contributing
Feel free to fork, suggest features, or report bugs!
Pull requests are warmly welcomed. 💙

