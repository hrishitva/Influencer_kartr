"""
Scheduled Posts Module

This module handles the scheduling and posting of content to various social media platforms.
It includes functionality for managing media files and scheduling posts with time delays.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from typing import Dict, List, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MEDIA_DIR = Path("data/media")
SCHEDULED_POSTS_FILE = Path("data/scheduled_posts.json")
DEFAULT_POST_TIME = "21:00"  # 9:00 PM
POST_DELAY_HOURS = 24

# Create necessary directories
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.joinpath("videos").mkdir(exist_ok=True)
MEDIA_DIR.joinpath("thumbnails").mkdir(exist_ok=True)

class ScheduledPost:
    def __init__(
        self,
        post_id: str,
        platform: str,
        content_type: str,
        media_path: str,
        thumbnail_path: Optional[str] = None,
        caption: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        status: str = "pending"
    ):
        self.post_id = post_id
        self.platform = platform
        self.content_type = content_type
        self.media_path = media_path
        self.thumbnail_path = thumbnail_path
        self.caption = caption
        self.scheduled_time = scheduled_time or DEFAULT_POST_TIME
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def to_dict(self) -> Dict:
        return {
            "post_id": self.post_id,
            "platform": self.platform,
            "content_type": self.content_type,
            "media_path": self.media_path,
            "thumbnail_path": self.thumbnail_path,
            "caption": self.caption,
            "scheduled_time": self.scheduled_time,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ScheduledPost':
        return cls(**data)

def save_media_file(file_path: str, content_type: str) -> str:
    """
    Save a media file to the appropriate directory.
    
    Args:
        file_path: Path to the source file
        content_type: Type of content ('video' or 'image')
        
    Returns:
        str: Path where the file was saved
    """
    source_path = Path(file_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")
    
    # Determine target directory based on content type
    target_dir = MEDIA_DIR / ("videos" if content_type == "video" else "thumbnails")
    target_path = target_dir / source_path.name
    
    # Copy the file
    shutil.copy2(source_path, target_path)
    logger.info(f"Saved {content_type} file to {target_path}")
    
    return str(target_path)

def schedule_post(
    platform: str,
    content_type: str,
    media_path: str,
    thumbnail_path: Optional[str] = None,
    caption: Optional[str] = None,
    scheduled_time: Optional[str] = None
) -> Dict:
    """
    Schedule a new post.
    
    Args:
        platform: Social media platform ('instagram' or 'youtube')
        content_type: Type of content ('video' or 'image')
        media_path: Path to the media file
        thumbnail_path: Path to the thumbnail (optional)
        caption: Post caption (optional)
        scheduled_time: Time to post (optional, defaults to 9:00 PM)
        
    Returns:
        Dict: Scheduled post information
    """
    # Validate platform
    if platform not in ['instagram', 'youtube']:
        raise ValueError("Unsupported platform. Must be 'instagram' or 'youtube'")
    
    # Validate content type
    if content_type not in ['video', 'image']:
        raise ValueError("Unsupported content type. Must be 'video' or 'image'")
    
    # Save media files
    saved_media_path = save_media_file(media_path, content_type)
    saved_thumbnail_path = save_media_file(thumbnail_path, 'image') if thumbnail_path else None
    
    # Create post
    post = ScheduledPost(
        post_id=f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        platform=platform,
        content_type=content_type,
        media_path=saved_media_path,
        thumbnail_path=saved_thumbnail_path,
        caption=caption,
        scheduled_time=scheduled_time
    )
    
    # Save to scheduled posts file
    save_scheduled_post(post)
    
    return post.to_dict()

def save_scheduled_post(post: ScheduledPost) -> None:
    """Save a scheduled post to the JSON file."""
    posts = []
    if SCHEDULED_POSTS_FILE.exists():
        try:
            with open(SCHEDULED_POSTS_FILE, 'r') as f:
                posts = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Error reading scheduled posts file. Starting with empty list.")
    
    posts.append(post.to_dict())
    
    with open(SCHEDULED_POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=2)
    
    logger.info(f"Saved scheduled post {post.post_id}")

def get_scheduled_posts(status: Optional[str] = None) -> List[Dict]:
    """
    Get all scheduled posts, optionally filtered by status.
    
    Args:
        status: Filter posts by status (optional)
        
    Returns:
        List[Dict]: List of scheduled posts
    """
    if not SCHEDULED_POSTS_FILE.exists():
        return []
    
    try:
        with open(SCHEDULED_POSTS_FILE, 'r') as f:
            posts = json.load(f)
        
        if status:
            posts = [p for p in posts if p['status'] == status]
        
        return posts
    except Exception as e:
        logger.error(f"Error reading scheduled posts: {str(e)}")
        return []

def update_post_status(post_id: str, status: str) -> bool:
    """
    Update the status of a scheduled post.
    
    Args:
        post_id: ID of the post to update
        status: New status
        
    Returns:
        bool: True if update was successful
    """
    if not SCHEDULED_POSTS_FILE.exists():
        return False
    
    try:
        with open(SCHEDULED_POSTS_FILE, 'r') as f:
            posts = json.load(f)
        
        # Find and update the post
        for post in posts:
            if post['post_id'] == post_id:
                post['status'] = status
                post['updated_at'] = datetime.now().isoformat()
                
                # Save updated posts
                with open(SCHEDULED_POSTS_FILE, 'w') as f:
                    json.dump(posts, f, indent=2)
                
                logger.info(f"Updated post {post_id} status to {status}")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error updating post status: {str(e)}")
        return False 