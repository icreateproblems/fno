import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

def _load_font(path: str | None, size: int):
    if path:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
        if not os.path.isabs(path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            alt_path = os.path.join(base_dir, path)
            if os.path.exists(alt_path):
                return ImageFont.truetype(alt_path, size=size)
    return ImageFont.load_default()

def _wrap_to_width(draw, text, font, max_width_px):
    words = (text or "").split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width_px:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def _detect_footer_height(img: Image.Image, sample_x=40, threshold=45):
    """
    Detect dark footer height by scanning upward from bottom.
    Works well for templates like yours (white body + dark footer).
    """
    w, h = img.size
    px = img.load()
    for y in range(h - 1, 0, -1):
        r, g, b = px[min(sample_x, w - 1), y]
        if (r + g + b) / 3 > threshold:  # becomes bright -> footer ended
            return h - y
    return int(h * 0.18)  # fallback

def render_news_on_template(
    template_path: str,
    headline: str,
    paragraph: str,
    output_path: str = "/tmp/post.jpg",
    title_font_path: str | None = None,
    body_font_path: str | None = None,
    target_size: tuple[int, int] | None = None,
    source: str | None = None,
    published_at: str | None = None,
):
    img = Image.open(template_path).convert("RGB")
    if target_size:
        img = img.resize(target_size, Image.LANCZOS)
    w, h = img.size
    draw = ImageDraw.Draw(img)

    # Safe margins (left/right space)
    pad_x = int(w * 0.09)      # 9% padding each side (looks clean)
    top_y = int(h * 0.09)      # 9% from top
    max_text_w = w - 2 * pad_x

    # Footer detection so text never goes onto @fastnewsorg bar
    footer_h = _detect_footer_height(img)
    safe_bottom = h - footer_h - int(h * 0.06)

    # Font sizes tuned for 1080x1080
    title_size = int(h * 0.060)   # ~65px
    body_size  = int(h * 0.038)   # ~41px

    title_font = _load_font(title_font_path, title_size)
    body_font  = _load_font(body_font_path, body_size)

    headline = (headline or "").strip()
    paragraph = (paragraph or "").strip()

    # Wrap
    title_lines = _wrap_to_width(draw, headline, title_font, max_text_w)
    body_lines  = _wrap_to_width(draw, paragraph, body_font, max_text_w)

    # Draw Title (max 3–4 lines)
    y = top_y
    title_line_h = int(title_size * 1.20)
    for line in title_lines[:4]:
        draw.text((pad_x, y), line, font=title_font, fill=(0, 0, 0))
        y += title_line_h

    # Gap between title and paragraph (increased for better spacing)
    y += int(h * 0.05)

    # Draw Paragraph (stop before date section)
    body_line_h = int(body_size * 1.55)  # Increased line height for readability
    # Reserve space for date at bottom
    metadata_reserved_space = int(h * 0.12)  # Reserve 12% for date
    text_safe_bottom = safe_bottom - metadata_reserved_space
    
    for line in body_lines:
        if y + body_line_h > text_safe_bottom:
            break
        draw.text((pad_x, y), line, font=body_font, fill=(35, 35, 35))
        y += body_line_h

    # Add date at bottom (date only, no time)
    if published_at:
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            date_str = pub_date.strftime("%B %d, %Y")
        except:
            date_str = datetime.now().strftime("%B %d, %Y")
    else:
        date_str = datetime.now().strftime("%B %d, %Y")
    
    date_font = _load_font(body_font_path, int(h * 0.028))
    date_y = safe_bottom - int(h * 0.08)
    draw.text((pad_x, date_y), date_str, font=date_font, fill=(100, 100, 100))

    img.save(output_path, quality=95)
    return output_path
