"""Generate visual preview images of pending posts using template rendering"""
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

from scripts.template_render import render_news_on_template
from app.config import Config
from PIL import Image, ImageDraw, ImageFont

PENDING_DIR = "pending_posts"
PREVIEW_DIR = "pending_posts/previews"

def create_post_preview(post_data, output_path):
    """Create Instagram-style preview image using template rendering"""
    
    # Extract article data
    title = post_data.get('title', 'FastNews.org')
    summary = post_data.get('summary', '')
    source = post_data.get('source', 'FastNews.org')
    
    # Clean title
    english_title = title.strip()
    for prefix in ["BREAKING:", "UPDATE:", "URGENT:", "LIVE:", "LATEST:"]:
        if english_title.upper().startswith(prefix):
            english_title = english_title[len(prefix):].strip()
    
    # Prepare description for image
    image_description = summary
    if len(image_description) > 150:
        # Try to find first sentence
        period_idx = image_description.find('. ')
        if period_idx > 0:
            image_description = image_description[:period_idx + 1]
        else:
            image_description = image_description[:150] + '...'
    
    # Template paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, Config.TEMPLATE_PATH)
    title_font = os.path.join(base_dir, Config.TITLE_FONT_PATH)
    body_font = os.path.join(base_dir, Config.BODY_FONT_PATH)
    
    # Render article onto template
    print(f"🎨 Rendering preview: {english_title[:50]}...")
    render_news_on_template(
        template_path,
        english_title,
        image_description,
        output_path,
        title_font_path=title_font,
        body_font_path=body_font,
        target_size=Config.OUTPUT_IMAGE_SIZE,
        source=source,
        published_at=''
    )
    
    # Add "PREVIEW" watermark
    if os.path.exists(output_path):
        img = Image.open(output_path)
        draw = ImageDraw.Draw(img)
        
        # Load font for watermark
        try:
            watermark_font = ImageFont.truetype(title_font, size=60)
        except:
            watermark_font = ImageFont.load_default()
        
        # Add semi-transparent watermark
        width, height = img.size
        watermark_text = f"PREVIEW - {post_data['category'].upper()} - AI:{post_data['ai_score']}/100"
        
        # Add red banner at bottom
        banner_height = 80
        draw.rectangle([0, height - banner_height, width, height], fill=(200, 0, 0, 180))
        
        # Draw watermark text
        bbox = draw.textbbox((0, 0), "PREVIEW - NOT PUBLISHED", font=watermark_font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, height - 60), "PREVIEW - NOT PUBLISHED", fill='white', font=watermark_font)
        
        img.save(output_path, quality=95)
        print(f"✅ Created preview: {output_path}")

def generate_all_previews():
    """Generate preview images for all pending posts"""
    
    print("\n" + "="*70)
    print("🖼️  GENERATING VISUAL PREVIEWS")
    print("="*70 + "\n")
    
    # Create preview directory
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    
    # Get all pending posts
    if not os.path.exists(PENDING_DIR):
        print("❌ No pending posts found")
        return
    
    count = 0
    for filename in sorted(os.listdir(PENDING_DIR)):
        if filename.endswith('.json'):
            filepath = os.path.join(PENDING_DIR, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                post_data = json.load(f)
            
            # Generate preview image
            preview_name = filename.replace('.json', '.jpg')
            preview_path = os.path.join(PREVIEW_DIR, preview_name)
            
            create_post_preview(post_data, preview_path)
            
            count += 1
            print(f"   Post #{count}: {post_data['title'][:50]}...")
    
    print("\n" + "="*70)
    print(f"✅ Generated {count} preview images")
    print("="*70)
    print(f"\nPreview images saved to: {PREVIEW_DIR}/")
    print("Open the .jpg files to see how posts will look on Instagram")
    print()

if __name__ == "__main__":
    generate_all_previews()
