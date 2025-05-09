"""
Social Media Poster Module

This module handles the actual posting of content to various social media platforms.
It includes functionality for posting to Instagram and YouTube.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from instagrapi import Client
from instagrapi.types import Media
from instagrapi.exceptions import TwoFactorRequired
from youtube_oauth import get_youtube_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaPoster:
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path
        self.instagram_client = None
        self.youtube_client = None
        
        if credentials_path:
            self._init_youtube_client()
    
    def _init_youtube_client(self) -> None:
        """Initialize YouTube API client."""
        try:
            self.youtube_client = get_youtube_service(self.credentials_path)
            if self.youtube_client:
                logger.info("YouTube client initialized successfully")
            else:
                logger.error("Failed to initialize YouTube client")
        except Exception as e:
            logger.error(f"Error initializing YouTube client: {str(e)}")
            self.youtube_client = None
    
    def _save_instagram_session(self, session_path: str = "instagram_session.json") -> None:
        """Save Instagram session to file."""
        if self.instagram_client:
            try:
                session_data = self.instagram_client.get_settings()
                with open(session_path, 'w') as f:
                    json.dump(session_data, f)
                logger.info(f"Instagram session saved to {session_path}")
            except Exception as e:
                logger.error(f"Error saving Instagram session: {str(e)}")
    
    def _load_instagram_session(self, session_path: str = "instagram_session.json") -> bool:
        """Load Instagram session from file."""
        if not os.path.exists(session_path):
            logger.info("No existing Instagram session found")
            return False
            
        try:
            logger.info("Attempting to load existing Instagram session")
            with open(session_path, 'r') as f:
                session_data = json.load(f)
            
            self.instagram_client = Client()
            self.instagram_client.load_settings(session_data)
            logger.info("Loaded session settings, attempting login")
            self.instagram_client.login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'))
            logger.info("Instagram session loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading Instagram session: {str(e)}")
            return False
    
    def init_instagram_client(self, username: str, password: str) -> bool:
        """
        Initialize Instagram client with credentials.
        
        Args:
            username: Instagram username
            password: Instagram password
            
        Returns:
            bool: True if initialization was successful
        """
        try:
            logger.info("Starting Instagram client initialization")
            
            # First try to load existing session
            if self._load_instagram_session():
                return True
                
            # If no session exists or loading failed, try normal login
            logger.info("No valid session found, attempting fresh login")
            self.instagram_client = Client()
            
            try:
                # First attempt to login
                logger.info("Attempting initial login")
                self.instagram_client.login(username, password)
            except TwoFactorRequired:
                # If 2FA is required, prompt for the code
                logger.info("Two-factor authentication required")
                code = input("Please enter the 2FA code sent to your device: ")
                
                # Try login again with 2FA code
                logger.info("Attempting login with 2FA code")
                self.instagram_client.login(username, password, verification_code=code)
            
            # Save the session after successful login
            logger.info("Login successful, saving session")
            self._save_instagram_session()
            
            logger.info("Instagram client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Instagram client: {str(e)}")
            self.instagram_client = None
            return False
    
    def post_to_youtube(
        self,
        video_path: str,
        title: str,
        description: str,
        thumbnail_path: Optional[str] = None,
        privacy_status: str = "private"
    ) -> Dict:
        """
        Post a video to YouTube.
        
        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            thumbnail_path: Path to the thumbnail image (optional)
            privacy_status: Privacy status ('private', 'unlisted', or 'public')
            
        Returns:
            Dict: Response from YouTube API
        """
        if not self.youtube_client:
            raise ValueError("YouTube client not initialized")
        
        try:
            # Create video upload request
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["influencer", "content"],
                    "categoryId": "22"  # People & Blogs category
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                }
            }
            
            # Upload video
            media = MediaFileUpload(
                video_path,
                mimetype="video/*",
                resumable=True
            )
            
            upload_request = self.youtube_client.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = upload_request.execute()
            logger.info(f"Video uploaded successfully: {response['id']}")
            
            # Upload thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    self.youtube_client.thumbnails().set(
                        videoId=response['id'],
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    logger.info("Thumbnail uploaded successfully")
                except Exception as e:
                    logger.warning(f"Could not upload thumbnail: {str(e)}")
                    logger.info("Video was uploaded successfully, but thumbnail upload failed")
            
            return response
            
        except Exception as e:
            logger.error(f"Error posting to YouTube: {str(e)}")
            raise
    
    def post_to_instagram(
        self,
        media_path: str,
        caption: Optional[str] = None,
        thumbnail_path: Optional[str] = None
    ) -> Dict:
        """
        Post content to Instagram.
        
        Args:
            media_path: Path to the media file
            caption: Post caption (optional)
            thumbnail_path: Path to the thumbnail (optional, required for video)
            
        Returns:
            Dict: Response from Instagram API
        """
        if not self.instagram_client:
            raise ValueError("Instagram client not initialized")
        
        try:
            # Determine if it's a video or image
            is_video = media_path.lower().endswith(('.mp4', '.mov', '.avi'))
            
            if is_video:
                if not thumbnail_path:
                    raise ValueError("Thumbnail path required for video posts")
                
                # Upload video
                media = self.instagram_client.video_upload(
                    media_path,
                    caption=caption,
                    thumbnail=thumbnail_path
                )
            else:
                # Upload image
                media = self.instagram_client.photo_upload(
                    media_path,
                    caption=caption
                )
            
            logger.info(f"Content posted to Instagram successfully: {media.id}")
            return {"id": media.id, "type": "video" if is_video else "photo"}
            
        except Exception as e:
            logger.error(f"Error posting to Instagram: {str(e)}")
            raise

def create_poster(credentials_path: Optional[str] = None) -> SocialMediaPoster:
    """
    Create a new SocialMediaPoster instance.
    
    Args:
        credentials_path: Path to YouTube credentials (optional)
        
    Returns:
        SocialMediaPoster: New poster instance
    """
    return SocialMediaPoster(credentials_path) 