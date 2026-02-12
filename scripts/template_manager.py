"""
Dynamic template system with multiple layouts.
Automatically selects best template for each story type.
"""
import os
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from enum import Enum

class TemplateType(Enum):
    """Different template layouts for different story types"""
    BREAKING_NEWS = "breaking"      # Large text, urgent feel
    STANDARD = "standard"            # Balanced layout
    SPORTS = "sports"                # Score-focused
    QUOTE = "quote"                  # Quotation-focused
    INFOGRAPHIC = "infographic"      # Data visualization
    PHOTO_STORY = "photo"            # Image-first


class TemplateManager:
    """Manage multiple template layouts"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        self.templates = {
            TemplateType.BREAKING_NEWS: "breaking_template.png",
            TemplateType.STANDARD: "standard_template.png",
            TemplateType.SPORTS: "sports_template.png",
            TemplateType.QUOTE: "quote_template.png",
        }
    
    def select_template(
        self,
        headline: str,
        description: str,
        category: str,
        has_image: bool = False
    ) -> Tuple[str, TemplateType]:
        """
        Intelligently select best template for story.
        
        Returns:
            (template_path, template_type)
        """
        
        # Rule 1: Breaking news gets breaking template
        if self._is_breaking_news(headline):
            return self._get_template_path(TemplateType.BREAKING_NEWS), TemplateType.BREAKING_NEWS
        
        # Rule 2: Sports scores get sports template
        if category == "sports" and self._has_scores(headline, description):
            return self._get_template_path(TemplateType.SPORTS), TemplateType.SPORTS
        
        # Rule 3: Stories with quotes get quote template
        if self._has_quote(description):
            return self._get_template_path(TemplateType.QUOTE), TemplateType.QUOTE
        
        # Rule 4: Image-rich stories get photo template
        if has_image and len(description) < 200:
            return self._get_template_path(TemplateType.PHOTO_STORY), TemplateType.PHOTO_STORY
        
        # Default: Standard template
        return self._get_template_path(TemplateType.STANDARD), TemplateType.STANDARD
    
    def _is_breaking_news(self, headline: str) -> bool:
        """Detect breaking news from headline"""
        breaking_keywords = [
            'breaking', 'just in', 'urgent', 'alert',
            'developing', 'live', 'update'
        ]
        headline_lower = headline.lower()
        return any(kw in headline_lower for kw in breaking_keywords)
    
    def _has_scores(self, headline: str, description: str) -> bool:
        """Detect sports scores"""
        import re
        combined = f"{headline} {description}"
        # Pattern: "X-Y" or "X vs Y" or "X:Y"
        score_pattern = r'\d+[-:]\d+|\d+\s+vs\s+\d+'
        return bool(re.search(score_pattern, combined))
    
    def _has_quote(self, description: str) -> bool:
        """Detect if story contains a notable quote"""
        return '"' in description and description.count('"') >= 2
    
    def _get_template_path(self, template_type: TemplateType) -> str:
        """Get full path to template file"""
        template_file = self.templates.get(template_type, self.templates[TemplateType.STANDARD])
        return os.path.join(self.templates_dir, template_file)


def render_with_smart_template(
    headline: str,
    description: str,
    category: str,
    output_path: str,
    **kwargs
) -> str:
    """
    Render using automatically selected template.
    Replaces the current render_news_on_template function.
    """
    manager = TemplateManager()
    template_path, template_type = manager.select_template(
        headline, description, category
    )
    
    # Use appropriate rendering function based on template type
    if template_type == TemplateType.BREAKING_NEWS:
        return render_breaking_news(template_path, headline, description, output_path, **kwargs)
    elif template_type == TemplateType.SPORTS:
        return render_sports_story(template_path, headline, description, output_path, **kwargs)
    elif template_type == TemplateType.QUOTE:
        return render_quote_story(template_path, headline, description, output_path, **kwargs)
    else:
        # Use standard rendering
        from template_render import render_news_on_template
        return render_news_on_template(template_path, headline, description, output_path, **kwargs)


# Specialized rendering functions
def render_breaking_news(template_path, headline, description, output_path, **kwargs):
    """Render with BREAKING NEWS style - large text, urgent"""
    # TODO: Implement breaking news specific rendering
    # - Larger title font
    # - Red/urgent color accents
    # - "BREAKING" badge
    pass

def render_sports_story(template_path, headline, description, output_path, **kwargs):
    """Render sports with score emphasis"""
    # TODO: Implement sports-specific rendering
    # - Highlight scores
    # - Team logos if available
    # - Stats visualization
    pass

def render_quote_story(template_path, headline, description, output_path, **kwargs):
    """Render with quote emphasis"""
    # TODO: Implement quote-specific rendering
    # - Large quote marks
    # - Attribution prominent
    # - Different text hierarchy
    pass
