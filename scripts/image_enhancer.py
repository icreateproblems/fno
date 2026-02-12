"""
Enhance generated images for professional appearance.
Adds subtle effects, optimizes colors, ensures readability.
"""
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import os

class ImageEnhancer:
    """Professional image enhancement pipeline"""
    
    def enhance_post_image(self, image_path: str, output_path: str = None) -> str:
        """
        Apply professional enhancements to post image.
        
        Steps:
        1. Optimize contrast and sharpness
        2. Add subtle vignette (darkens edges)
        3. Ensure text readability
        4. Add subtle shadow/depth
        """
        if output_path is None:
            output_path = image_path
        
        img = Image.open(image_path).convert("RGB")
        
        # Enhancement 1: Subtle contrast boost
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.05)  # 5% more contrast
        
        # Enhancement 2: Slight sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)  # 10% sharper
        
        # Enhancement 3: Add subtle vignette for depth
        img = self._add_vignette(img, intensity=0.15)
        
        # Enhancement 4: Ensure JPEG optimization
        img.save(
            output_path,
            "JPEG",
            quality=95,
            optimize=True,
            progressive=True  # Progressive JPEG for faster loading
        )
        
        return output_path
    
    def _add_vignette(self, img: Image.Image, intensity: float = 0.2) -> Image.Image:
        """Add subtle vignette effect (darkens edges)"""
        width, height = img.size
        
        # Create radial gradient mask
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        
        # Calculate center and radius
        center_x, center_y = width // 2, height // 2
        max_radius = ((width/2)**2 + (height/2)**2) ** 0.5
        
        # Draw concentric circles with increasing opacity
        for i in range(100, 0, -1):
            radius = max_radius * (i / 100)
            opacity = int(255 * (1 - intensity * (100 - i) / 100))
            bbox = [
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ]
            draw.ellipse(bbox, fill=opacity)
        
        # Apply mask
        # Create black image
        vignette = Image.new('RGB', (width, height), (0, 0, 0))
        
        # Composite original with vignette using mask
        output = Image.composite(img, vignette, mask)
        
        return output
    
    def add_watermark(
        self,
        image_path: str,
        watermark_text: str = "@fastnewsorg",
        output_path: str = None
    ) -> str:
        """Add subtle watermark to image"""
        if output_path is None:
            output_path = image_path
        
        img = Image.open(image_path).convert("RGBA")
        
        # Create watermark layer
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        # TODO: Add watermark text in corner
        # with semi-transparent overlay
        
        # Composite and save
        output = Image.alpha_composite(img, watermark)
        output.convert('RGB').save(output_path, quality=95)
        
        return output_path
