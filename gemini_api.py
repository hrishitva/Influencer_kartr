import os
import google.generativeai as genai
import logging
from youtube_transcript_api import YouTubeTranscriptApi

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the Gemini API with your API key
# Replace this with the API key provided by Kiran
GEMINI_API_KEY = "AIzaSyDqiAjS3jYwdzv1o4hLQsHO_8O3E4ji6yg"
genai.configure(api_key=GEMINI_API_KEY)

def get_transcript(video_id):
    """Get transcript for a YouTube video"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([item['text'] for item in transcript_list])
        return transcript_text
    except Exception as e:
        logger.error(f"Error getting transcript: {str(e)}")
        return None

def analyze_transcript_with_gemini(transcript, video_info=None):
    """
    Use Gemini AI to analyze transcript and extract:
    - Creator name
    - Creator industry
    - Sponsor name
    - Sponsor industry
    """
    if not transcript:
        return None
    
    # Prepare prompt for Gemini
    prompt = f"""
    Analyze this YouTube video transcript and extract the following information:
    1. Creator name (the person or channel who created this content)
    2. Creator industry or niche
    3. Sponsor name (the brand or company being promoted, if any)
    4. Sponsor industry
    
    If any information is not available, respond with "Unknown".
    
    Video title: {video_info.get('title', 'Unknown') if video_info else 'Unknown'}
    Transcript: {transcript[:4000]}  # Limit transcript length
    
    Format your response as JSON with these keys: creator_name, creator_industry, sponsor_name, sponsor_industry
    """
    
    try:
        # Initialize the Gemini model - using gemini-pro instead of gemini-2.0-flash
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Process the response
        if response:
            try:
                # Extract the JSON part from the response
                import json
                import re
                
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                else:
                    # If no JSON found, parse manually
                    lines = response.text.split('\n')
                    data = {}
                    for line in lines:
                        if "creator name" in line.lower() and ":" in line:
                            data["creator_name"] = line.split(":", 1)[1].strip()
                        elif "creator industry" in line.lower() and ":" in line:
                            data["creator_industry"] = line.split(":", 1)[1].strip()
                        elif "sponsor name" in line.lower() and ":" in line:
                            data["sponsor_name"] = line.split(":", 1)[1].strip()
                        elif "sponsor industry" in line.lower() and ":" in line:
                            data["sponsor_industry"] = line.split(":", 1)[1].strip()
                
                return {
                    "creator_name": data.get("creator_name", "Unknown"),
                    "creator_industry": data.get("creator_industry", "Unknown"),
                    "sponsor_name": data.get("sponsor_name", "Unknown"),
                    "sponsor_industry": data.get("sponsor_industry", "Unknown")
                }
            except Exception as parse_error:
                logger.error(f"Error parsing Gemini response: {str(parse_error)}")
                return {"error": f"Error parsing response: {str(parse_error)}"}
        else:
            logger.error("Empty response from Gemini API")
            return {"error": "Empty response from Gemini API"}
            
    except Exception as e:
        logger.error(f"Error analyzing transcript with Gemini: {str(e)}")
        return {"error": str(e)}