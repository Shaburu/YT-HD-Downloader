import os
import re
import sys
import json
import argparse
from urllib.parse import urlparse, parse_qs
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def extract_video_ids_from_html(html):
    # Video IDs are in "href=/watch?v=VIDEO_ID" in the HTML but need regex to extract all unique ones
    video_ids = set(re.findall(r'/watch\?v=([\w-]{11})', html))
    return list(video_ids)

def get_videos_from_channel(channel_identifier):
    """
    Accepts channel URL, channel ID, username, or custom URL.
    Returns list of video IDs from the channel's /videos page.
    """
    # Normalize channel URL
    possible_prefixes = [
        'https://www.youtube.com/channel/',
        'https://www.youtube.com/user/',
        'https://www.youtube.com/c/',
        'https://www.youtube.com/'
    ]

    url = None
    if channel_identifier.startswith('http'):
        url = channel_identifier
    else:
        # try channel ID format first
        if channel_identifier.startswith('UC'):
            url = f'https://www.youtube.com/channel/{channel_identifier}/videos'
        else:
            # else default to user
            url = f'https://www.youtube.com/user/{channel_identifier}/videos'

    # If URL doesn't end with /videos, set it
    if '/videos' not in url:
        if url.endswith('/'):
            url += 'videos'
        else:
            url += '/videos'

    print(f"Fetching videos from: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Failed to fetch channel videos page (Status code: {r.status_code})")
        return []

    html = r.text

    ids = extract_video_ids_from_html(html)
    print(f"Found {len(ids)} videos on the channel page.")
    return ids

def download_transcript(video_id):
    try:
        # fetch only manually created transcripts (exclude generated = False)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        # Try to get manually created transcript first
        if transcript_list.find_manually_created_transcript(['en']):
            transcript = transcript_list.find_manually_created_transcript(['en'])
        else:
            # If no 'en' transcript manually created, try without language filter but manual only
            for t in transcript_list:
                if not t.is_generated:
                    transcript = t
                    break
        if transcript is None:
            print(f"No manually created transcript found for video {video_id}")
            return None

        # fetch the transcript
        return transcript.fetch()
    except TranscriptsDisabled:
        print(f"Transcripts are disabled for video {video_id}.")
    except NoTranscriptFound:
        print(f"No transcript found for video {video_id}.")
    except Exception as e:
        print(f"Error fetching transcript for video {video_id}: {str(e)}")
    return None

# def save_transcript(video_id, transcript, output_dir):
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#     # Save JSON
#     json_path = os.path.join(output_dir, f'{video_id}.json')
#     with open(json_path, 'w', encoding='utf-8') as f:
#         json.dump(transcript, f, indent=2, ensure_ascii=False)
#     # Save plain text
#     text_path = os.path.join(output_dir, f'{video_id}.txt')
#     with open(text_path, 'w', encoding='utf-8') as f:
#         for entry in transcript:
#             f.write(entry['text'] + '\n')
#     print(f"Saved transcript for {video_id} as JSON and TXT.")

def save_transcript(video_id, transcript, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # convert transcript object to list
    transcript_list = list(transcript)
    # Save JSON
    json_path = os.path.join(output_dir, f'{video_id}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_list, f, indent=2, ensure_ascii=False)
    # Save plain text
    text_path = os.path.join(output_dir, f'{video_id}.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        for entry in transcript_list:
            f.write(entry['text'] + '\n')
    print(f"Saved transcript for {video_id} as JSON and TXT.")

def extract_video_id_from_url(url):
    """
    Extract video ID from full YouTube video URL or string.
    """
    # Example URL formats:
    # https://www.youtube.com/watch?v=VIDEOID12345
    # https://youtu.be/VIDEOID12345
    # Just a raw video ID (11 chars)
    if len(url) == 11 and re.match(r'^[\w-]{11}$', url):
        return url
    parsed = urlparse(url)
    if 'youtu.be' in parsed.netloc:
        return parsed.path[1:]  # remove leading '/'
    if 'youtube.com' in parsed.netloc:
        qs = parse_qs(parsed.query)
        if 'v' in qs:
            return qs['v'][0]
    return None

def main():
    parser = argparse.ArgumentParser(description="Download manual transcripts from a YouTube channel or a single video.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--channel', help='YouTube channel URL, channel ID or username or custom URL')
    group.add_argument('-v', '--video', help='YouTube video URL or video ID')

    parser.add_argument('-n', '--number', type=int, default=0,
                        help='Number of latest videos to process from the channel (0 for all found)')
    parser.add_argument('-o', '--output', default='transcripts',
                        help='Output folder for transcripts')

    args = parser.parse_args()

    if args.video:
        video_id = extract_video_id_from_url(args.video)
        if not video_id:
            print("Invalid video URL or ID.")
            sys.exit(1)
        print(f"Processing single video: {video_id}")
        transcript = download_transcript(video_id)
        if transcript:
            save_transcript(video_id, transcript, args.output)
        else:
            print("No transcript available.")

    elif args.channel:
        video_ids = get_videos_from_channel(args.channel)
        if not video_ids:
            print("No videos found.")
            sys.exit(1)
        if args.number > 0:
            video_ids = video_ids[:args.number]
        print(f"Processing {len(video_ids)} videos...")

        for vid in video_ids:
            print(f"Downloading transcript for video {vid} ...")
            transcript = download_transcript(vid)
            if transcript:
                save_transcript(vid, transcript, args.output)
            else:
                print(f"No transcript for video {vid}. Skipping.")

if __name__ == '__main__':
    main()