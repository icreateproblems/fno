"""Create a simple placeholder image for Instagram posts without images"""
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

# Create a simple 1080x1080 image with text
img = Image.new('RGB', (1080, 1080), color='#1a1a1a')
draw = ImageDraw.Draw(img)

# Add text
try:
    font = ImageFont.truetype("arial.ttf", 60)
except:
    font = ImageFont.load_default()

text = "FastNews.org\nनेपाल समाचार"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (1080 - text_width) // 2
y = (1080 - text_height) // 2
draw.text((x, y), text, fill='white', font=font, align='center')

# Save to bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG', quality=95)
img_bytes.seek(0)

# Upload to ImgBB
imgbb_key = os.getenv('IMGBB_API_KEY')
if imgbb_key:
    image_b64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    
    response = requests.post(
        'https://api.imgbb.com/1/upload',
        data={'key': imgbb_key, 'image': image_b64},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            url = result['data']['url']
            print(f"✅ Placeholder image uploaded!")
            print(f"URL: {url}")
            print(f"\nUpdate scheduler.py DEFAULT_IMAGE to:")
            print(f'DEFAULT_IMAGE = "{url}"')
        else:
            print(f"❌ Upload failed: {result}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
else:
    print("❌ No IMGBB_API_KEY found in .env")
    # Save locally instead
    img.save('placeholder.jpg', quality=95)
    print("✅ Saved as placeholder.jpg")
