"""
Post Scheduler Module

This module handles the scheduling and execution of social media posts.
It includes functionality for managing the posting queue and executing posts at scheduled times.
"""
import os
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule

from scheduled_posts import (
    get_scheduled_posts,
    update_post_status,
    ScheduledPost
)
from social_media_poster import create_poster

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostScheduler:
    def __init__(self, youtube_api_key: Optional[str] = None):
        self.poster = create_poster(youtube_api_key)
        self.running = False
        self.scheduler_thread = None
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        logger.info("Post scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Post scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        while self.running:
            try:
                # Get pending posts
                pending_posts = get_scheduled_posts(status="pending")
                
                for post in pending_posts:
                    self._process_post(post)
                
                # Sleep for a minute before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Sleep before retrying
    
    def _process_post(self, post: Dict) -> None:
        """
        Process a pending post.
        
        Args:
            post: Post information
        """
        try:
            # Parse scheduled time
            scheduled_time = datetime.strptime(post['scheduled_time'], '%H:%M').time()
            current_time = datetime.now().time()
            
            # Check if it's time to post
            if current_time >= scheduled_time:
                # Update status to processing
                update_post_status(post['post_id'], 'processing')
                
                # Post to the appropriate platform
                if post['platform'] == 'youtube':
                    self._post_to_youtube(post)
                elif post['platform'] == 'instagram':
                    self._post_to_instagram(post)
                
                # Update status to completed
                update_post_status(post['post_id'], 'completed')
                logger.info(f"Successfully processed post {post['post_id']}")
            
        except Exception as e:
            logger.error(f"Error processing post {post['post_id']}: {str(e)}")
            update_post_status(post['post_id'], 'failed')
    
    def _post_to_youtube(self, post: Dict) -> None:
        """
        Post content to YouTube.
        
        Args:
            post: Post information
        """
        try:
            response = self.poster.post_to_youtube(
                video_path=post['media_path'],
                title=post.get('caption', 'New Video'),
                description=post.get('caption', ''),
                thumbnail_path=post.get('thumbnail_path'),
                privacy_status='public'
            )
            logger.info(f"YouTube post successful: {response['id']}")
            
        except Exception as e:
            logger.error(f"Error posting to YouTube: {str(e)}")
            raise
    
    def _post_to_instagram(self, post: Dict) -> None:
        """
        Post content to Instagram.
        
        Args:
            post: Post information
        """
        try:
            response = self.poster.post_to_instagram(
                media_path=post['media_path'],
                caption=post.get('caption'),
                thumbnail_path=post.get('thumbnail_path')
            )
            logger.info(f"Instagram post successful: {response['id']}")
            
        except Exception as e:
            logger.error(f"Error posting to Instagram: {str(e)}")
            raise

def create_scheduler(youtube_api_key: Optional[str] = None) -> PostScheduler:
    """
    Create a new PostScheduler instance.
    
    Args:
        youtube_api_key: YouTube API key (optional)
        
    Returns:
        PostScheduler: New scheduler instance
    """
    return PostScheduler(youtube_api_key) 