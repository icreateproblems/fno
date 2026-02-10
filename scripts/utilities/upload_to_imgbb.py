"""
Utility to upload images to imgbb (temporary public hosting)
This is a helper for Instagram Graph API which requires public URLs

For production, use S3/CloudFlare instead.
"""
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')


def upload_image_bytes_to_imgbb(image_bytes: bytes, api_key: str = None) -> str:
    """
    Upload image bytes to imgbb and get public URL
    
    Args:
        image_bytes: Binary image data
        api_key: ImgBB API key (optional, uses env var if not provided)
        
    Returns:
        Public URL if successful, None if failed
    """
    key = api_key or IMGBB_API_KEY
    if not key:
        return None
    
    try:
        # Base64 encode the image
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        url = "https://api.imgbb.com/1/upload"
        payload = {
            'key': key,
            'image': image_b64
        }
        
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            return result['data']['url']
        else:
            return None
            
    except Exception as e:
        print(f"ImgBB upload error: {e}")
        return None


def upload_image_to_imgbb(image_path: str, expiration: int = 3600) -> tuple:
    """
    Upload image to imgbb and get public URL
    
    Args:
        image_path: Local path to image file
        expiration: Seconds until expiration (default 1 hour = 3600)
        
    Returns:
        (success: bool, url: str, error: str)
    """
    if not IMGBB_API_KEY:
        return False, None, "IMGBB_API_KEY not set in .env"
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        url = "https://api.imgbb.com/1/upload"
        
        payload = {
            'key': IMGBB_API_KEY,
            'expiration': expiration  # Auto-delete after X seconds
        }
        
        files = {
            'image': ('image.jpg', image_data, 'image/jpeg')
        }
        
        response = requests.post(url, data=payload, files=files, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            image_url = result['data']['url']
            return True, image_url, None
        else:
            return False, None, f"Upload failed: {result}"
            
    except Exception as e:
        return False, None, str(e)


def upload_image_to_cloudflare(image_path: str) -> tuple:
    """
    Upload image to Cloudflare R2 (requires setup)
    TODO: Implement if using Cloudflare
    
    Returns:
        (success: bool, url: str, error: str)
    """
    # Placeholder for Cloudflare R2 implementation
    return False, None, "Not implemented - use imgbb or S3"


if __name__ == "__main__":
    # Test upload
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python upload_to_imgbb.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)
    
    print(f"Uploading {image_path} to imgbb...")
    success, url, error = upload_image_to_imgbb(image_path)
    
    if success:
        print(f"✅ Uploaded successfully!")
        print(f"URL: {url}")
    else:
        print(f"❌ Upload failed: {error}")
