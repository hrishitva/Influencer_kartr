"""
Test script for social media posting functionality.
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from post_scheduler import create_scheduler
from scheduled_posts import schedule_post
from social_media_poster import create_poster

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    'youtube_credentials_path': 'credentials/client_secret.json',
    'instagram_username': os.getenv('INSTAGRAM_USERNAME'),
    'instagram_password': os.getenv('INSTAGRAM_PASSWORD'),
    'test_video_path': 'test_data/test_video.mp4',
    'test_thumbnail_path': 'test_data/test_thumbnail.jpg',
    'test_image_path': 'test_data/test_image.jpg'
}

def setup_test_environment():
    """Create test directories and files if they don't exist."""
    # Create test data directory
    test_dir = Path('test_data')
    test_dir.mkdir(exist_ok=True)
    
    # Create dummy test files if they don't exist
    if not Path(TEST_CONFIG['test_video_path']).exists():
        logger.warning(f"Test video not found at {TEST_CONFIG['test_video_path']}")
        logger.info("Please place a test video file at this location")
    
    if not Path(TEST_CONFIG['test_thumbnail_path']).exists():
        logger.warning(f"Test thumbnail not found at {TEST_CONFIG['test_thumbnail_path']}")
        logger.info("Please place a test thumbnail image at this location")
    
    if not Path(TEST_CONFIG['test_image_path']).exists():
        logger.warning(f"Test image not found at {TEST_CONFIG['test_image_path']}")
        logger.info("Please place a test image file at this location")

def test_youtube_posting():
    """Test YouTube posting functionality."""
    logger.info("Testing YouTube posting...")
    
    # Create poster instance
    poster = create_poster(TEST_CONFIG['youtube_credentials_path'])
    
    try:
        # Test video upload
        response = poster.post_to_youtube(
            video_path=TEST_CONFIG['test_video_path'],
            title="Test Video",
            description="This is a test video upload",
            thumbnail_path=TEST_CONFIG['test_thumbnail_path'],
            privacy_status="private"  # Use private for testing
        )
        logger.info(f"YouTube test successful: {response['id']}")
        return True
    except Exception as e:
        logger.error(f"YouTube test failed: {str(e)}")
        return False

def test_instagram_image_posting():
    """Test Instagram image posting functionality."""
    logger.info("Testing Instagram image posting...")
    
    # Create poster instance
    logger.info("Creating poster instance...")
    poster = create_poster()
    
    try:
        # Initialize Instagram client
        logger.info("Attempting to initialize Instagram client...")
        logger.info(f"Using username: {TEST_CONFIG['instagram_username']}")
        
        if not poster.init_instagram_client(
            TEST_CONFIG['instagram_username'],
            TEST_CONFIG['instagram_password']
        ):
            logger.error("Failed to initialize Instagram client")
            return False
        
        logger.info("Instagram client initialized successfully")
        
        # Test image upload only
        logger.info("Attempting to upload test image...")
        response = poster.post_to_instagram(
            media_path=TEST_CONFIG['test_image_path'],
            caption="Test image post"
        )
        logger.info(f"Instagram image test successful: {response['id']}")
        
        return True
    except Exception as e:
        logger.error(f"Instagram image test failed: {str(e)}")
        return False

def test_instagram_video_posting():
    """Test Instagram video posting functionality."""
    logger.info("Testing Instagram video posting...")
    
    # Create poster instance
    logger.info("Creating poster instance...")
    poster = create_poster()
    
    try:
        # Initialize Instagram client
        logger.info("Attempting to initialize Instagram client...")
        logger.info(f"Using username: {TEST_CONFIG['instagram_username']}")
        
        if not poster.init_instagram_client(
            TEST_CONFIG['instagram_username'],
            TEST_CONFIG['instagram_password']
        ):
            logger.error("Failed to initialize Instagram client")
            return False
        
        logger.info("Instagram client initialized successfully")
        
        # Test video upload
        logger.info("Attempting to upload test video...")
        response = poster.post_to_instagram(
            media_path=TEST_CONFIG['test_video_path'],
            caption="Test video post",
            thumbnail_path=TEST_CONFIG['test_thumbnail_path']
        )
        logger.info(f"Instagram video test successful: {response['id']}")
        
        return True
    except Exception as e:
        logger.error(f"Instagram video test failed: {str(e)}")
        return False

def test_scheduling():
    """Test post scheduling functionality."""
    logger.info("Testing post scheduling...")
    
    try:
        # Create scheduler
        scheduler = create_scheduler(TEST_CONFIG['youtube_credentials_path'])
        
        # Schedule a test post for 1 minute from now
        scheduled_time = (datetime.now() + timedelta(minutes=1)).strftime('%H:%M')
        
        # Schedule YouTube post
        youtube_post = schedule_post(
            platform="youtube",
            content_type="video",
            media_path=TEST_CONFIG['test_video_path'],
            thumbnail_path=TEST_CONFIG['test_thumbnail_path'],
            caption="Scheduled test video",
            scheduled_time=scheduled_time
        )
        logger.info(f"Scheduled YouTube post: {youtube_post['post_id']}")
        
        # Schedule Instagram post
        instagram_post = schedule_post(
            platform="instagram",
            content_type="video",
            media_path=TEST_CONFIG['test_video_path'],
            thumbnail_path=TEST_CONFIG['test_thumbnail_path'],
            caption="Scheduled test video",
            scheduled_time=scheduled_time
        )
        logger.info(f"Scheduled Instagram post: {instagram_post['post_id']}")
        
        # Start scheduler
        scheduler.start()
        
        # Wait for 2 minutes to allow posts to be processed
        logger.info("Waiting for scheduled posts to be processed...")
        import time
        time.sleep(120)
        
        # Stop scheduler
        scheduler.stop()
        
        return True
    except Exception as e:
        logger.error(f"Scheduling test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    logger.info("Setting up test environment...")
    setup_test_environment()
    
    # Check required credentials
    if not TEST_CONFIG['instagram_username'] or not TEST_CONFIG['instagram_password']:
        logger.error("Instagram credentials not found in environment variables")
        return
    
    # Run tests
    logger.info("Starting tests...")
    
    # Skip YouTube test temporarily due to quota limits
    # youtube_success = test_youtube_posting()
    
    # Test Instagram video upload
    instagram_video_success = test_instagram_video_posting()
    
    # Print results
    logger.info("\nTest Results:")
    logger.info(f"Instagram video posting: {'✓' if instagram_video_success else '✗'}")

if __name__ == "__main__":
    main() 