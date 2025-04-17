import os
import csv
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from werkzeug.security import generate_password_hash, check_password_hash

# CSV file paths
DATABASE_CSV = os.path.join(os.getcwd(), 'data/database.csv')
ANALYSIS_CSV = os.path.join(os.getcwd(), 'data/ANALYSIS.CSV')

def save_user_to_csv(username, email, password, user_type):
    """
    Save user information to database.csv
    """
    # Hash the password for security
    hashed_password = generate_password_hash(password)
    
    # Check if file exists and create with headers if not
    if not os.path.exists(DATABASE_CSV):
        with open(DATABASE_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'email', 'password', 'user_type', 'date_registered'])
    
    # Append the new user
    with open(DATABASE_CSV, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, email, hashed_password, user_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    
    return True

def validate_user_login(email, password):
    """
    Validate user login against database.csv
    Returns (is_valid, user_type) tuple
    """
    if not os.path.exists(DATABASE_CSV):
        return False, None
    
    try:
        df = pd.read_csv(DATABASE_CSV)
        user = df[df['email'] == email]
        
        if not user.empty:
            stored_hash = user.iloc[0]['password']
            if check_password_hash(stored_hash, password):
                return True, user.iloc[0]['user_type']
    except Exception as e:
        print(f"Error validating user: {e}")
    
    return False, None

def extract_video_id(youtube_url):
    """
    Extract video ID from YouTube URL
    """
    try:
        parsed_url = urlparse(youtube_url)
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]
            elif parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
            elif parsed_url.path.startswith('/shorts/'):
                return parsed_url.path.split('/')[2]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        
        return None
    except Exception as e:
        print(f"Error extracting video ID: {e}")
        return None

def save_analysis_to_csv(video_link, transcript, analysis_data):
    """
    Save analysis data to ANALYSIS.CSV
    """
    # Check if file exists and create with headers if not
    if not os.path.exists(ANALYSIS_CSV):
        with open(ANALYSIS_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['video_link', 'transcript', 'analysis_data', 'date_analyzed'])
    
    # Append the analysis data
    with open(ANALYSIS_CSV, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            video_link, 
            transcript, 
            analysis_data, 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return True