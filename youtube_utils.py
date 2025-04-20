import re
import csv
import os
import logging
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_video_id(url):
    """
    Extract the YouTube video ID from a URL
    
    Args:
        url (str): YouTube URL
        
    Returns:
        str: YouTube video ID or None if not found
    """
    try:
        # Regular expression patterns for different YouTube URL formats
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)',  # Standard and shortened URLs
            r'(?:youtube\.com\/embed\/)([^&\n?]+)',                # Embedded URLs
            r'(?:youtube\.com\/v\/)([^&\n?]+)',                    # Old embed URLs
            r'(?:youtube\.com\/user\/\w+\/\w+\/\w+\/)([^&\n?]+)'   # User page URLs
        ]
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        logger.warning(f"Could not extract video ID from URL: {url}")
        return None
    except Exception as e:
        logger.error(f"Error extracting video ID: {str(e)}")
        return None

def analyze_video_content(video_id):
    """
    Comprehensive analysis of a YouTube video to extract creator and sponsor information
    
    Args:
        video_id (str): YouTube video ID
        
    Returns:
        dict: Detailed information about creator and sponsors
    """
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.warning(f"Failed to fetch video page: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        page_content = response.text
        
        # Initialize result dictionary
        result = {
            "creator": {
                "name": "",
                "channel_id": "",
                "industry": "",
                "categories": []
            },
            "sponsor": {
                "name": "",
                "industry": "",
                "confidence": 0,
                "mentions": [],
                "timestamps": []
            },
            "has_paid_promotion": False,
            "keywords": [],
            "categories": []
        }
        
        # Extract video title
        title = ""
        title_meta = soup.find("meta", {"property": "og:title"})
        if title_meta:
            title = title_meta.get("content", "")
            result["title"] = title
        
        # Get video description
        description = ""
        description_meta = soup.find("meta", {"name": "description"})
        if description_meta:
            description = description_meta.get("content", "")
            result["description"] = description
        
        # Extract creator information - improved methods
        channel_name = ""
        
        # Method 1: From meta tags
        channel_meta = soup.find("meta", {"property": "og:site_name"})
        if channel_meta:
            channel_name = channel_meta.get("content", "").replace("- YouTube", "").strip()
        
        # Method 2: From JSON-LD data
        if not channel_name:
            import json
            json_ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
            json_matches = re.findall(json_ld_pattern, page_content, re.DOTALL)
            
            for json_data in json_matches:
                try:
                    data = json.loads(json_data)
                    if isinstance(data, dict) and 'author' in data:
                        if isinstance(data['author'], dict) and 'name' in data['author']:
                            channel_name = data['author']['name']
                            break
                except:
                    continue
        
        # Method 3: From video owner information
        if not channel_name:
            owner_pattern = r'"ownerChannelName":"([^"]+)"'
            owner_match = re.search(owner_pattern, page_content)
            if owner_match:
                channel_name = owner_match.group(1)
        
        # Method 4: From microformat data
        if not channel_name:
            microformat_pattern = r'"ownerProfileUrl":"[^"]+","ownerChannelName":"([^"]+)"'
            microformat_match = re.search(microformat_pattern, page_content)
            if microformat_match:
                channel_name = microformat_match.group(1)
        
        # Method 5: From channel link in HTML
        if not channel_name:
            channel_link = soup.find("a", {"class": "yt-simple-endpoint style-scope yt-formatted-string"})
            if channel_link:
                channel_name = channel_link.text.strip()
        
        # Set the creator name
        if channel_name:
            result["creator"]["name"] = channel_name
        
        # Extract channel ID
        channel_id_pattern = r'"channelId":"([^"]+)"'
        channel_id_match = re.search(channel_id_pattern, page_content)
        if channel_id_match:
            result["creator"]["channel_id"] = channel_id_match.group(1)
        
        # Determine creator industry
        category_keywords = {
            "gaming": ["gaming", "game", "gameplay", "minecraft", "fortnite"],
            "technology": ["tech", "technology", "gadget", "review", "unboxing"],
            "beauty & fashion": ["beauty", "makeup", "fashion", "style", "clothing"],
            "food & cooking": ["food", "cooking", "recipe", "baking", "chef"],
            "health & fitness": ["fitness", "workout", "health", "exercise", "gym"],
            "travel": ["travel", "vacation", "trip", "destination", "tourism"],
            "lifestyle": ["vlog", "lifestyle", "day in the life", "routine"],
            "education": ["education", "tutorial", "how to", "learn", "course"],
            "finance": ["finance", "money", "investing", "stock", "crypto"],
            "entertainment": ["entertainment", "comedy", "funny", "prank", "challenge"]
        }
        
        # Check title and description for category keywords
        combined_text = (title + " " + description).lower()
        
        for industry, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    if not result["creator"]["industry"]:
                        result["creator"]["industry"] = industry.title()
                    result["creator"]["categories"].append(keyword)
        
        # Look for sponsor information
        sponsor_keywords = [
            "#ad", "#sponsored", "#partner", "#promotion", "#paidpartnership",
            "sponsored by", "thanks to", "brought to you by", "partnership with",
            "discount code", "promo code", "use code", "click the link", "affiliate"
        ]
        
        # Check for paid promotion tag
        if "includes paid promotion" in page_content.lower():
            result["has_paid_promotion"] = True
            result["sponsor"]["confidence"] += 30
        
        # Check description for sponsor keywords
        for keyword in sponsor_keywords:
            if keyword.lower() in description.lower() or keyword.lower() in title.lower():
                result["keywords"].append(keyword)
                result["sponsor"]["confidence"] += 10
        
        # Extract potential sponsor names
        sponsor_patterns = [
            r"(?:sponsored by|thanks to|brought to you by|partnership with)\s+([A-Z][A-Za-z0-9_\-]+(?:\s+[A-Z][A-Za-z0-9_\-]+){0,2})",
            r"(?:use code|promo code|discount code)\s+([A-Z0-9_\-]+)",
            r"(?:check out|visit)\s+(?:our sponsor)?(?:s)?\s+([A-Z][A-Za-z0-9_\-\.]+(?:\.[a-z]{2,})?)"
        ]
        
        for pattern in sponsor_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):  # Some regex groups return tuples
                        match = match[0]
                    if len(match) > 2:  # Avoid very short matches
                        result["sponsor"]["mentions"].append(match)
                        result["sponsor"]["confidence"] += 15
        
        # Determine most likely sponsor name
        if result["sponsor"]["mentions"]:
            # Count occurrences of each potential sponsor
            from collections import Counter
            sponsor_counts = Counter(result["sponsor"]["mentions"])
            most_common = sponsor_counts.most_common(1)[0][0]
            result["sponsor"]["name"] = most_common
            
            # Try to determine sponsor industry
            sponsor_industry_mapping = {
                "vpn": "Technology",
                "nord": "Technology",
                "express": "Technology",
                "skillshare": "Education",
                "brilliant": "Education",
                "coursera": "Education",
                "udemy": "Education",
                "squarespace": "Technology",
                "wix": "Technology",
                "shopify": "E-commerce",
                "audible": "Entertainment",
                "raid": "Gaming",
                "dollar": "Personal Care",
                "shave": "Personal Care",
                "manscaped": "Personal Care",
                "raycon": "Technology"
            }
            
            sponsor_name_lower = most_common.lower()
            for key, value in sponsor_industry_mapping.items():
                if key in sponsor_name_lower:
                    result["sponsor"]["industry"] = value
                    break
            
            # If no specific match, try to infer from video category
            if not result["sponsor"]["industry"] and result["creator"]["industry"]:
                result["sponsor"]["industry"] = result["creator"]["industry"]
        
        # If we still don't have creator industry but have categories
        if not result["creator"]["industry"] and result["creator"]["categories"]:
            # Set a default industry based on the first category
            result["creator"]["industry"] = "Content Creation"
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing video content: {str(e)}")
        return None

# Existing functions remain unchanged
def save_user_to_csv(username, email, password, user_type):
    """Save user information to CSV file for validation"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.isfile('data/database.csv')
        
        with open('data/database.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            
            # Write headers if file doesn't exist
            if not file_exists:
                writer.writerow(['username', 'email', 'password', 'user_type', 'date_registered'])
            
            # Write user data
            writer.writerow([
                username, 
                email, 
                password,  # Note: In a real app, never store plain passwords
                user_type,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        logger.info(f"User {username} saved to CSV")
        return True
    except Exception as e:
        logger.error(f"Error saving user to CSV: {str(e)}")
        return False

def validate_user_login(email, password):
    """Validate user login against CSV file"""
    try:
        # Check if file exists
        if not os.path.isfile('data/database.csv'):
            logger.warning("Database CSV file not found")
            return False, None
        
        # Read CSV file
        df = pd.read_csv('data/database.csv')
        
        # Find user by email
        user = df[df['email'] == email]
        
        if user.empty:
            logger.warning(f"User with email {email} not found in CSV")
            return False, None
        
        # Check password
        if user.iloc[0]['password'] == password:
            logger.info(f"User {email} validated via CSV")
            return True, user.iloc[0]['user_type']
        
        logger.warning(f"Invalid password for user {email}")
        return False, None
    except Exception as e:
        logger.error(f"Error validating user login: {str(e)}")
        return False, None