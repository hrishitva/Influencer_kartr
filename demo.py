import os
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import google.generativeai as genai
import time
import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ========== CONFIGURATION ==========

# Enter your API key here
API_KEY = "AIzaSyBeLDwohTIA2c0UrXYTHesGLEWqHSnqRNM"
YOUTUBE_API_KEY = "AIzaSyCats7k8Ss6BaZMOufj1xL767vO-MFh264"
MODEL_NAME = "models/gemini-2.0-flash"
CSV_FILENAME = os.path.join(os.getcwd(), 'data/ANALYSIS.CSV')  # Save analysis data in ANALYSIS.CSV
BATCH_SIZE = 10

DELAY = 2

# ===================================

def initialize_csv(filename=CSV_FILENAME):
    """Create the CSV with headers using pandas if it doesn't exist."""
    print(f"Checking for file at: {os.path.abspath(filename)}")  # Print the absolute path for debugging
    CSV_COLUMNS = ['youtube video link', 'transcript', 'Sponsor Name', 'Sponsor Industry', 
                   'Video Creator Name', 'Video Creator Industry', 'Sponsor Website Link']
    if not os.path.isfile(filename):
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"{filename} created with headers.")
    else:
        print(f"{filename} already exists.")  # Added explicit message when file exists

def extract_video_id(yt_url):
    """Extracts the video ID from a YouTube URL."""
    try:
        parsed_url = urlparse(yt_url)
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]
            elif parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
            elif parsed_url.path.startswith('/shorts/'):  # Handle YouTube shorts
                return parsed_url.path.split('/')[2]
        elif parsed_url.hostname == 'youtu.be':  # Handle youtu.be
            return parsed_url.path[1:]

        raise ValueError("Invalid YouTube URL format.")
    except Exception as e:
        raise ValueError(f"Error parsing URL: {e}")

def get_transcript(video_id):
    """Retrieves the transcript from a YouTube video."""
    try:
        # First try to get available transcript languages
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to find English transcript first
        try:
            # Look for English transcript
            transcript = transcript_list.find_transcript(['en'])
            transcript_data = transcript.fetch()
            print("Found English transcript")
        except:
            # If English not available, get auto-generated or fall back to any available transcript
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                transcript_data = transcript.fetch()
                print("Found auto-generated English transcript")
            except:
                # Fall back to default transcript and translate if needed
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
                if transcript.language_code != 'en':
                    print(f"Translating transcript from {transcript.language_code} to English")
                    transcript = transcript.translate('en')
                transcript_data = transcript.fetch()
                print(f"Using translated transcript")
        
        transcript_text = " ".join([t['text'] for t in transcript_data])
        return transcript_text
    except Exception as e:
        print(f"Error getting transcript for video ID {video_id}: {e}")
        # Fall back to original method if the above fails
        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([t['text'] for t in transcript_data])
            print("Using default transcript")
            return transcript_text
        except Exception as e:
            print(f"All transcript retrieval methods failed: {e}")
            return ""

def analyze_transcript(transcript, model_name=MODEL_NAME):
    """Analyzes the transcript using the Gemini AI model."""
    if not transcript:
        return "No transcript to analyze."

    prompt = f"""
You are a YouTube analysis AI. Given the following video transcript, extract:
1. Sponsor name(s) -mandatory
2. Sponsor’s industry -mandatory
3. Video creator name -mandatory
4. Video creator's industry -mandatory
5. Sponsor website or link if mentioned -mandatory

Transcript:
{transcript[:4000]}

Return your answer in this exact format:
Sponsor Name: <...>
Sponsor Industry: <...>
Video Creator Name: <...>
Video Creator Industry: <...>
Sponsor Video Link (if any): <...>
    """

    try:
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "No response from Gemini."
    except Exception as e:
        return f"Error analyzing with Gemini: {e}"

def save_to_csv(video_link, transcript, gemini_output, filename=CSV_FILENAME):
    """Saves the data to a CSV file."""
    # Extracting fields from gemini_output and organizing them into individual components
    sponsor_name = ""
    sponsor_industry = ""
    video_creator_name = ""
    video_creator_industry = ""
    sponsor_website = ""

    # Assuming the gemini output follows the format:
    if gemini_output:
        lines = gemini_output.split("\n")
        for line in lines:
            if line.startswith("Sponsor Name:"):
                sponsor_name = line.replace("Sponsor Name:", "").strip()
            elif line.startswith("Sponsor Industry:"):
                sponsor_industry = line.replace("Sponsor Industry:", "").strip()
            elif line.startswith("Video Creator Name:"):
                video_creator_name = line.replace("Video Creator Name:", "").strip()
            elif line.startswith("Video Creator Industry:"):
                video_creator_industry = line.replace("Video Creator Industry:", "").strip()
            elif line.startswith("Sponsor Video Link (if any):"):
                sponsor_website = line.replace("Sponsor Video Link (if any):", "").strip()

    # Prepare the data, making sure empty values are explicitly set to empty strings
    data = {
        'youtube video link': [video_link],
        'transcript': [transcript],
        'Sponsor Name': [sponsor_name if sponsor_name else ''],
        'Sponsor Industry': [sponsor_industry if sponsor_industry else ''],
        'Video Creator Name': [video_creator_name if video_creator_name else ''],
        'Video Creator Industry': [video_creator_industry if video_creator_industry else ''],
        'Sponsor Website Link': [sponsor_website if sponsor_website else '']
    }

    try:
        df = pd.DataFrame(data)
        file_exists = os.path.isfile(filename)
        df.to_csv(filename, mode='a', header=not file_exists, index=False, encoding='utf-8')
        print("Saved to ANALYSIS.CSV successfully!")
    except Exception as e:
        print(f"Failed to save to CSV: {e}")

def get_channel_id_by_name(channel_name):
    """Get channel ID from a channel name using YouTube API."""
    if not YOUTUBE_API_KEY:
        print("Error: YouTube API key is missing. Please add it to the configuration.")
        return None
        
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        # Search for the channel
        search_response = youtube.search().list(
            q=channel_name,
            type='channel',
            part='id,snippet',
            maxResults=1
        ).execute()
        
        if not search_response.get('items'):
            print(f"No channel found with name: {channel_name}")
            return None
            
        channel_id = search_response['items'][0]['id']['channelId']
        channel_title = search_response['items'][0]['snippet']['title']
        print(f"Found channel: {channel_title} (ID: {channel_id})")
        return channel_id
        
    except HttpError as e:
        print(f"Error accessing YouTube API: {e}")
        return None

def get_channel_videos(channel_id, max_results=50):
    """Get videos from a YouTube channel."""
    if not YOUTUBE_API_KEY:
        print("Error: YouTube API key is missing. Please add it to the configuration.")
        return []
        
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        # Get uploads playlist ID
        channels_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if not channels_response['items']:
            print(f"No channel found with ID: {channel_id}")
            return []
            
        uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from uploads playlist
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            playlist_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - len(videos)),
                pageToken=next_page_token
            ).execute()
            
            for item in playlist_response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append(video_url)
                
            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token or len(videos) >= max_results:
                break
                
            time.sleep(DELAY)  # Avoid rate limiting
            
        return videos
    except HttpError as e:
        print(f"Error accessing YouTube API: {e}")
        return []

def process_video_batch(video_urls):
    """Process a batch of videos."""
    success_count = 0
    fail_count = 0
    
    for i, url in enumerate(video_urls):
        print(f"\nProcessing video {i+1}/{len(video_urls)}: {url}")
        try:
            video_id = extract_video_id(url)
            print(f"Video ID: {video_id}")
            transcript = get_transcript(video_id)
            
            if not transcript:
                print("No transcript available, but saving anyway.")
                
            gemini_output = analyze_transcript(transcript)
            print("\nGemini Output Summary:", gemini_output.split('\n')[0] if gemini_output else "No output")
            save_to_csv(url, transcript, gemini_output)
            success_count += 1
            
        except Exception as e:
            print(f"Error processing video: {e}")
            fail_count += 1
            
        # Add delay to avoid rate limiting
        if i < len(video_urls) - 1:
            print(f"Waiting {DELAY} seconds before next video...")
            time.sleep(DELAY)
    
    print(f"\nBatch processing complete. Success: {success_count}, Failed: {fail_count}")
    return success_count, fail_count

def channel_search_mode():
    """Search for a channel by name and process its videos."""
    print("\n=== YouTube Channel Video Processor ===\n")
    
    # Get YouTube API key if not set
    global YOUTUBE_API_KEY
    
    # Get channel name from user
    channel_name = input("Enter YouTube channel name: ").strip()
    if not channel_name:
        print("Channel name is required.")
        return
        
    # Get channel ID
    channel_id = get_channel_id_by_name(channel_name)
    if not channel_id:
        return
        
    # Ask for max videos to process
    try:
        max_videos = input("Maximum number of videos to process (default 50): ").strip()
        max_videos = int(max_videos) if max_videos else 50
    except ValueError:
        print("Invalid number, using default of 50.")
        max_videos = 50
        
    # Get videos from channel
    print(f"Fetching up to {max_videos} videos from channel...")
    video_urls = get_channel_videos(channel_id, max_videos)
    
    if not video_urls:
        print("No videos found or error occurred.")
        return
        
    print(f"Found {len(video_urls)} videos.")
    
    # Confirm processing
    confirm = input(f"Process {len(video_urls)} videos? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
        
    # Process videos
    genai.configure(api_key=API_KEY)
    initialize_csv()
    process_video_batch(video_urls)

def search_videos_by_industry(industry_keyword, max_results=50):
    """Search for videos related to a specific industry that might have sponsors."""
    if not YOUTUBE_API_KEY:
        print("Error: YouTube API key is missing. Please add it to the configuration.")
        return []
        
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        # Search for videos with industry keyword + "sponsor" to increase chances of finding sponsored content
        search_query = f"{industry_keyword} sponsor"
        print(f"Searching for videos with query: '{search_query}'")
        
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            search_response = youtube.search().list(
                q=search_query,
                type='video',
                part='id,snippet',
                maxResults=min(50, max_results - len(videos)),
                pageToken=next_page_token,
                videoDuration='medium',  # Focus on medium-length videos (more likely to have sponsors)
                relevanceLanguage='en'   # English videos for better transcript availability
            ).execute()
            
            for item in search_response['items']:
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                channel_title = item['snippet']['channelTitle']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append({
                    'url': video_url,
                    'title': video_title,
                    'channel': channel_title
                })
                print(f"Found: {video_title} by {channel_title}")
                
            next_page_token = search_response.get('nextPageToken')
            if not next_page_token or len(videos) >= max_results:
                break
                
            time.sleep(DELAY)  # Avoid rate limiting
            
        return videos
    except HttpError as e:
        print(f"Error accessing YouTube API: {e}")
        return []

def industry_search_mode():
    """Search for videos in a specific industry with sponsors."""
    print("\n=== Industry-Specific Sponsor Search ===\n")
    
    # Get industry keyword from user
    industry = input("Enter industry to search for (e.g., tech, beauty, fitness): ").strip()
    if not industry:
        print("Industry keyword is required.")
        return
        
    # Ask for max videos to search
    try:
        max_videos = input("Maximum number of videos to search for (default 20): ").strip()
        max_videos = int(max_videos) if max_videos else 20
    except ValueError:
        print("Invalid number, using default of 20.")
        max_videos = 20
        
    # Search for videos
    print(f"Searching for up to {max_videos} videos related to '{industry}' with potential sponsors...")
    video_results = search_videos_by_industry(industry, max_videos)
    
    if not video_results:
        print("No videos found or error occurred.")
        return
        
    print(f"\nFound {len(video_results)} potential videos with sponsors in the {industry} industry.")
    
    # Display found videos with numbers
    for i, video in enumerate(video_results):
        print(f"{i+1}. {video['title']} (by {video['channel']})")
    
    # Ask user which videos to process
    process_option = input("\nProcess videos? (all/numbers/none): ").strip().lower()
    
    videos_to_process = []
    
    if process_option == 'all':
        videos_to_process = [video['url'] for video in video_results]
    elif process_option == 'none':
        print("Operation cancelled.")
        return
    else:
        try:
            # Parse numbers like "1,3,5-7"
            selections = process_option.split(',')
            for selection in selections:
                if '-' in selection:
                    start, end = map(int, selection.split('-'))
                    for num in range(start, end + 1):
                        if 1 <= num <= len(video_results):
                            videos_to_process.append(video_results[num-1]['url'])
                else:
                    num = int(selection)
                    if 1 <= num <= len(video_results):
                        videos_to_process.append(video_results[num-1]['url'])
        except ValueError:
            print("Invalid selection format. Processing all videos.")
            videos_to_process = [video['url'] for video in video_results]
    
    if not videos_to_process:
        print("No videos selected for processing.")
        return
        
    print(f"Processing {len(videos_to_process)} videos...")
    
    # Process selected videos
    genai.configure(api_key=API_KEY)
    initialize_csv()
    process_video_batch(videos_to_process)

# Update the main function to include the new industry search option
def main():
    """Main function to run the script."""
    print("\n=== YouTube Sponsorship Data Collection Tool ===\n")
    print("1. Process a single video")
    print("2. Process videos from a channel")
    print("3. Search for sponsored videos by industry")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        # Original single video processing
        genai.configure(api_key=API_KEY)
        initialize_csv()
        yt_url = input("Enter YouTube video link: ").strip()
        try:
            video_id = extract_video_id(yt_url)
            print(f"Video ID: {video_id}")
            transcript = get_transcript(video_id)
            if not transcript:
                print("No transcript available, but saving anyway.")
            gemini_output = analyze_transcript(transcript)
            print("\nGemini Output:\n", gemini_output)
            save_to_csv(yt_url, transcript, gemini_output)
        except Exception as e:
            print(f"Error: {e}")
    
    elif choice == '2':
        channel_search_mode()
    
    elif choice == '3':
        industry_search_mode()
    
    elif choice == '4':
        print("Exiting program.")
        sys.exit(0)
    
    else:
        print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
