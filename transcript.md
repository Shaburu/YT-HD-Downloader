How to use:
Save the script as yt_transcript_downloader.py.
Open command prompt (Windows PowerShell or CMD).
Install dependencies:
pip install requests youtube-transcript-api
Run to get transcript for one video:
python yt_transcript_downloader.py -v https://youtu.be/VIDEO_ID
Run to get transcripts for a channel, all recent videos loaded on the page:
python yt_transcript_downloader.py -c UC_x5XG1OV2P6uZZ5FSM9Ttw
Or by username:
python yt_transcript_downloader.py -c GoogleDevelopers
Limit number of videos (e.g., last 5):
python yt_transcript_downloader.py -c GoogleDevelopers -n 5
Store transcripts in a specific folder (default is transcripts):
python yt_transcript_downloader.py -v VIDEO_ID -o my_transcripts_folder
