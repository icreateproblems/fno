def _wrap_text_smart(draw, text, font, max_width_px, max_lines=None):
    """
    Smart text wrapping that handles:
    - Long words by breaking them
    - Hyphenation for better appearance
    - Unicode (Nepali) text properly
    """
    words = (text or "").split()
    lines = []
    current_line = ""
    for word in words:
        test_line = (current_line + " " + word).strip()
        test_width = draw.textlength(test_line, font=font)
        if test_width <= max_width_px:
            current_line = test_line
        else:
            if not current_line:
                chars_that_fit = 0
                for i in range(1, len(word) + 1):
                    if draw.textlength(word[:i], font=font) <= max_width_px:
                        chars_that_fit = i
                    else:
                        break
                if chars_that_fit > 0:
                    lines.append(word[:chars_that_fit])
                    current_line = word[chars_that_fit:]
                else:
                    lines.append(word)
                    current_line = ""
            else:
                lines.append(current_line)
                current_line = word
        if max_lines and len(lines) >= max_lines:
            break
    if current_line and (not max_lines or len(lines) < max_lines):
        lines.append(current_line)
    return lines
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
    pad_x = int(w * 0.08)      # 8% padding (cleaner look)
    top_y = int(h * 0.10)      # 10% from top (more breathing room)
    max_text_w = w - 2 * pad_x

    # Footer detection
    footer_h = _detect_footer_height(img)
    safe_bottom = h - footer_h - int(h * 0.08)

    # IMPROVED FONT SIZING
    title_size = int(h * 0.070)   # Increased from 0.060 to 0.070 (~75px instead of 65px)
    body_size  = int(h * 0.036)   # Decreased from 0.038 to 0.036 (~39px for better contrast)

    title_font = _load_font(title_font_path, title_size)
    body_font  = _load_font(body_font_path, body_size)

    headline = (headline or "").strip()
    paragraph = (paragraph or "").strip()

    # SMART TEXT WRAPPING
    title_lines = _wrap_text_smart(draw, headline, title_font, max_text_w, max_lines=3)
    body_lines  = _wrap_text_smart(draw, paragraph, body_font, max_text_w)

    # DRAW TITLE (BOLD & PROMINENT)
    y = top_y
    title_line_h = int(title_size * 1.25)  # Increased line height for readability
    for i, line in enumerate(title_lines):
        draw.text((pad_x, y), line, font=title_font, fill=(0, 0, 0))
        y += title_line_h

    # LARGER GAP BETWEEN TITLE AND BODY
    y += int(h * 0.06)  # Increased from 0.05 to 0.06 for better visual separation

    # DRAW BODY TEXT
    body_line_h = int(body_size * 1.60)  # Increased from 1.55 for better readability
    metadata_reserved_space = int(h * 0.12)
    text_safe_bottom = safe_bottom - metadata_reserved_space
    line_count = 0
    for line in body_lines:
        if y + body_line_h > text_safe_bottom:
            break
        draw.text((pad_x, y), line, font=body_font, fill=(45, 45, 45))
        y += body_line_h
        line_count += 1
        if line_count >= 7:
            break

    # ADD DATE AND SOURCE
    metadata_parts = []
    if published_at:
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            date_str = pub_date.strftime("%B %d, %Y")
            metadata_parts.append(date_str)
        except:
            metadata_parts.append(datetime.now().strftime("%B %d, %Y"))
    else:
        metadata_parts.append(datetime.now().strftime("%B %d, %Y"))
    if source:
        metadata_parts.append(f"Source: {source}")
    metadata_text = " • ".join(metadata_parts)
    date_font = _load_font(body_font_path, int(h * 0.030))  # Slightly larger
    date_y = safe_bottom - int(h * 0.09)
    draw.text((pad_x, date_y), metadata_text, font=date_font, fill=(120, 120, 120))

    img.save(output_path, quality=96, optimize=True)  # Increased quality
    return output_path
