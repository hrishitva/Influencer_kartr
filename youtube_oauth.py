"""
YouTube OAuth2 Authentication Module

This module handles OAuth2 authentication for YouTube API.
"""
import os
import json
import logging
from typing import Optional, Dict
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth2 scopes required for YouTube API
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

def get_oauth2_credentials(credentials_path: str) -> Optional[Credentials]:
    """
    Get OAuth2 credentials for YouTube API.
    
    Args:
        credentials_path: Path to the OAuth2 credentials JSON file
        
    Returns:
        Optional[Credentials]: OAuth2 credentials if successful, None otherwise
    """
    creds = None
    
    # Check if token.json exists
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_info(
                json.load(open('token.json')),
                SCOPES
            )
        except Exception as e:
            logger.error(f"Error loading credentials from token.json: {str(e)}")
    
    # If credentials are not valid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {str(e)}")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                    
            except Exception as e:
                logger.error(f"Error getting new credentials: {str(e)}")
                return None
    
    return creds

def get_youtube_service(credentials_path: str) -> Optional[Dict]:
    """
    Get authenticated YouTube API service.
    
    Args:
        credentials_path: Path to the OAuth2 credentials JSON file
        
    Returns:
        Optional[Dict]: YouTube API service if successful, None otherwise
    """
    try:
        creds = get_oauth2_credentials(credentials_path)
        if not creds:
            logger.error("Failed to get OAuth2 credentials")
            return None
            
        youtube = build('youtube', 'v3', credentials=creds)
        return youtube
        
    except Exception as e:
        logger.error(f"Error building YouTube service: {str(e)}")
        return None 