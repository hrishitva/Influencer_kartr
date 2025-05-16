import os
import io
import requests
from atproto import Client, models

# Bluesky account credentials and image path
handle = 'influencerkartr.bsky.social'#os.environ.get('BLUESKY_HANDLE') or '<your_handle>' # Replace with your handle if not set in environment
password = 'uode-ikgp-nh7p-vo3o'#os.environ.get('BLUESKY_PASSWORD') or '<your_app_password>' # Replace with your app password if not set in environment
image_path = 'Kartr_logo.png' # Replace with the actual path to your image
caption = "Hello World!!"

# Initialize Bluesky Client
client = Client()
client.login(handle, password)

# Upload the image
with open(image_path, 'rb') as image_file:
    img_bytes = image_file.read()

upload = client.upload_blob(img_bytes)

# Get image dimensions (optional, but recommended for aspect ratio)
img_data = io.BytesIO(img_bytes)
img_data.seek(0)

try:
    from PIL import Image
    img = Image.open(img_data)
    width, height = img.size
    aspect_ratio = {'width': width, 'height': height}
except ImportError:
    aspect_ratio = None
    print("PIL (Pillow) not installed. Aspect ratio will not be included.")
except Exception as e:
    aspect_ratio = None
    print(f"Error getting image dimensions: {e}. Aspect ratio will not be included.")

# Create the post with the image embed
images = [models.AppBskyEmbedImages.Image(alt=caption, image=upload.blob, aspectRatio=aspect_ratio)]
embed = models.AppBskyEmbedImages.Main(images=images)

post = client.send_post(text=caption, embed=embed)
print(f"Post created successfully: {post.uri}")