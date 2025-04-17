from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
import re

# ==== CONFIGURE THIS ====
API_KEY = 'YOUR_API_KEY_HERE'  # Replace with your YouTube Data API v3 key

def extract_channel_id(channel_url):
    # Handles URLs like:
    # - https://www.youtube.com/channel/UCxxxxx
    # - https://www.youtube.com/@username
    # - https://www.youtube.com/user/username
    parsed = urlparse(channel_url)
    path_parts = parsed.path.strip("/").split("/")
    
    if "channel" in path_parts:
        return path_parts[-1], "id"
    elif "user" in path_parts:
        return path_parts[-1], "forUsername"
    elif parsed.path.startswith("/@"):
        return parsed.path[2:], "forHandle"
    else:
        raise ValueError("Unsupported YouTube URL format.")

def get_channel_stats(channel_url, api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    identifier, id_type = extract_channel_id(channel_url)
    
    if id_type == "id":
        request = youtube.channels().list(part="snippet,contentDetails,statistics", id=identifier)
    elif id_type == "forUsername":
        request = youtube.channels().list(part="snippet,contentDetails,statistics", forUsername=identifier)
    elif id_type == "forHandle":
        # Handles (e.g., @username) are not directly supported—need to search instead
        request = youtube.search().list(part="snippet", q=identifier, type="channel", maxResults=1)
        response = request.execute()
        if not response['items']:
            return "Channel not found with handle."
        channel_id = response['items'][0]['snippet']['channelId']
        request = youtube.channels().list(part="snippet,contentDetails,statistics", id=channel_id)
    else:
        return "Invalid channel identifier."

    response = request.execute()
    if not response['items']:
        return "No channel data found."

    data = response['items'][0]
    stats = data['statistics']
    snippet = data['snippet']

    return {
        "Title": snippet.get('title'),
        "Description": snippet.get('description'),
        "Published At": snippet.get('publishedAt'),
        "Subscribers": stats.get('subscriberCount'),
        "Total Views": stats.get('viewCount'),
        "Video Count": stats.get('videoCount'),
        "Channel ID": data.get('id'),
    }

# === USAGE EXAMPLE ===
if __name__ == "__main__":
    channel_url = input("Enter YouTube channel URL: ")
    try:
        stats = get_channel_stats(channel_url, API_KEY)
        print("\nChannel Statistics:")
        for k, v in stats.items():
            print(f"{k}: {v}")
    except Exception as e:
        print("Error:", str(e))
