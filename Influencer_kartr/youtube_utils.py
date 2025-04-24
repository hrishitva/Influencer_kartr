import os
import csv
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from werkzeug.security import generate_password_hash, check_password_hash

# CSV file paths
DATABASE_CSV = os.path.join(os.getcwd(), 'data/database.csv')
ANALYSIS_CSV = os.path.join(os.getcwd(), 'data/ANALYSIS.CSV')

def save_user_to_csv(username, email, password, user_type, public_email=False):
    """
    Save user information to database.csv
    Ensures records are properly appended one below the other
    
    Parameters:
    - username: The user's username
    - email: The user's email
    - password: The user's password (will be hashed)
    - user_type: 'influencer' or 'sponsor'
    - public_email: Boolean indicating if the email should be public in searches
    """
    # Hash the password for security
    hashed_password = generate_password_hash(password)
    
    # Make sure directory exists
    os.makedirs(os.path.dirname(DATABASE_CSV), exist_ok=True)
    
    # Check if file exists and create with headers if not
    if not os.path.exists(DATABASE_CSV):
        with open(DATABASE_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'email', 'password', 'user_type', 'date_registered', 'public_email'])
    
    # Read the file to check existing headers
    existing_headers = []
    existing_data = []
    try:
        with open(DATABASE_CSV, 'r', newline='') as file:
            reader = csv.reader(file)
            all_rows = list(reader)
            if all_rows:
                existing_headers = all_rows[0]
                existing_data = all_rows[1:] if len(all_rows) > 1 else []
    except Exception as e:
        print(f"Error reading existing headers: {e}")
        
    # Update file if 'public_email' is missing from headers
    headers_updated = False
    if 'public_email' not in existing_headers and existing_headers:
        headers_updated = True
        existing_headers.append('public_email')
        # Add False to all existing records
        for row in existing_data:
            row.append('False')
    
    # Prepare new record
    new_record = [
        username, 
        email, 
        hashed_password, 
        user_type, 
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        str(public_email)
    ]
    
    # If headers were updated or for safety, rewrite the entire file
    with open(DATABASE_CSV, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write headers
        writer.writerow(existing_headers if existing_headers else 
                        ['username', 'email', 'password', 'user_type', 'date_registered', 'public_email'])
        
        # Write existing data
        for row in existing_data:
            writer.writerow(row)
            
        # Write the new record
        writer.writerow(new_record)
    
    print(f"Successfully added user {username} to {DATABASE_CSV}")
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

def save_analysis_to_csv(video_link, transcript, analysis_data, source="demo"):
    """
    Save analysis data to ANALYSIS.CSV
    Ensures data is appended correctly below previous records
    Only updates when source is 'demo' (meaning it's called from the demo page)
    """
    # Only proceed if this is from the demo page
    if source != "demo":
        print(f"Analysis data not saved: source '{source}' is not 'demo'")
        return False
        
    # Check if file exists and create with headers if not
    if not os.path.exists(ANALYSIS_CSV):
        os.makedirs(os.path.dirname(ANALYSIS_CSV), exist_ok=True)
        with open(ANALYSIS_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['video_link', 'transcript', 'analysis_data', 'date_analyzed'])
    
    # Make sure to properly format transcript and analysis data for CSV storage
    # by removing any internal newlines that might break CSV formatting
    transcript_formatted = transcript.replace('\n', ' ') if transcript else ''
    analysis_formatted = analysis_data.replace('\n', ' ') if analysis_data else ''
    
    # Append the analysis data with proper newline formatting
    with open(ANALYSIS_CSV, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            video_link, 
            transcript_formatted, 
            analysis_formatted, 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    print(f"Successfully appended analysis data to {ANALYSIS_CSV}")
    return True