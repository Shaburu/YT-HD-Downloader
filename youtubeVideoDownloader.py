import os
import youtube_dl

def download_youtube_video(video_url, output_path='.'):
    # Set options for youtube-dl
    ydl_opts = {
        'format': 'best',  # Download the best quality video available
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),  # Output filename format
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print(f'Downloading: {video_url}')
            ydl.download([video_url])
            print('Video downloaded successfully.')
    except Exception as e:
        print(f'An error occurred: {e}')

if __name__ == '__main__':
    video_url = input("Please enter the YouTube video URL: ")
    output_path = input("Please enter the output directory (leave blank for current directory): ") or '.'
    
    download_youtube_video(video_url, output_path)