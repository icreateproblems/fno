"""
Content Editor/Decider Module
Uses GROQ AI to validate and approve content before publishing.
Acts as a final quality gate to ensure only valuable content is posted.
"""
import json
from typing import Dict, Any, Tuple
from groq import Groq

try:
    from app.config import Config
    from app.logger import get_logger
except ImportError:
    # Fallback for standalone usage
    class Config:
        GROQ_EDITOR_API_KEY = None
        GROQ_EDITOR_MODEL = "llama-3.3-70b-versatile"
        GROQ_EDITOR_TEMPERATURE = 0.3
    
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class ContentEditor:
    """
    AI-powered content editor that validates articles before publishing.
    Uses GROQ to assess quality, relevance, and category.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize content editor with GROQ API.
        
        Args:
            api_key: GROQ API key (uses Config if not provided)
        """
        self.api_key = api_key or Config.GROQ_EDITOR_API_KEY
        
        if not self.api_key:
            logger.warning("No GROQ Editor API key found - validation disabled")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
    
    def validate_content(
        self, 
        title: str, 
        summary: str, 
        source: str,
        content: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate content using AI editor before publishing.
        
        The AI editor decides:
        1. Should this be published? (yes/no)
        2. What category does it belong to?
        3. Quality score (0-100)
        4. Reasons for decision
        
        Args:
            title: Article title
            summary: Article summary/description
            source: News source
            content: Full article content (optional)
            
        Returns:
            Tuple of (should_publish, category, metadata)
            - should_publish: True if article should be posted
            - category: Content category (politics, sports, etc.)
            - metadata: Dict with score, reasons, etc.
        """
        if not self.client:
            # Fallback when no API key - approve with generic category
            logger.warning("Editor validation skipped (no API key)")
            return True, 'general', {'score': 70, 'reason': 'No validation'}
        
        try:
            # Prepare validation prompt
            prompt = self._create_validation_prompt(title, summary, source, content)
            
            # Call GROQ for validation
            response = self.client.chat.completions.create(
                model=Config.GROQ_EDITOR_MODEL,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=Config.GROQ_EDITOR_TEMPERATURE,
                max_tokens=500
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            result = self._parse_validation_result(result_text)
            
            should_publish = result.get('approved', False)
            category = result.get('category', 'general')
            metadata = {
                'score': result.get('score', 50),
                'reason': result.get('reason', 'Unknown'),
                'interest_level': result.get('interest_level', 'medium'),
                'raw_response': result_text[:200]
            }
            
            logger.info(
                f"Editor decision: {'✅ PUBLISH' if should_publish else '❌ REJECT'} "
                f"[{category.upper()}] Score: {metadata['score']}/100 - {title[:50]}"
            )
            
            return should_publish, category, metadata
            
        except Exception as e:
            logger.error(f"Content validation error: {e}")
            # On error, be conservative - approve with low score
            return True, 'general', {'score': 60, 'reason': f'Validation error: {e}'}
    
    def _create_validation_prompt(
        self, 
        title: str, 
        summary: str, 
        source: str,
        content: str
    ) -> str:
        """Create prompt for GROQ validation."""
        return f"""You are a senior news editor for FastNews Nepal, an Instagram news page.
Your job is to decide if this article should be published.

ARTICLE:
Title: {title}
Summary: {summary}
Source: {source}
Content: {content[:500] if content else '(no content)'}

DECISION CRITERIA:
1. Is it newsworthy and interesting for Nepali Instagram audience?
2. Is it factual and from a credible source?
3. Will it engage users (likes, shares, comments)?
4. Does it fit our quality standards?

CATEGORIES: politics, economy, sports, international, technology, entertainment, society, general

Respond in JSON format:
{{
    "approved": true/false,
    "category": "category_name",
    "score": 0-100,
    "interest_level": "low/medium/high",
    "reason": "brief explanation"
}}

IMPORTANT: We want variety - approve interesting stories from ALL categories.
Approve stories about NEPSE, golf, cricket, politics, technology, entertainment, etc.
Only reject if clearly spam, offensive, or very low quality."""
    
    def _parse_validation_result(self, result_text: str) -> Dict[str, Any]:
        """Parse GROQ validation response."""
        try:
            # Try to extract JSON from response
            result_text = result_text.strip()
            
            # Find JSON in response (might have extra text)
            if '{' in result_text and '}' in result_text:
                json_start = result_text.index('{')
                json_end = result_text.rindex('}') + 1
                json_str = result_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                # No JSON found, parse manually
                result = {
                    'approved': 'approve' in result_text.lower() or 'yes' in result_text.lower(),
                    'category': 'general',
                    'score': 70,
                    'reason': result_text[:100]
                }
            
            # Validate required fields
            if 'approved' not in result:
                result['approved'] = True  # Default to approve
            
            if 'category' not in result or result['category'] not in Config.CONTENT_CATEGORIES:
                result['category'] = 'general'
            
            if 'score' not in result:
                result['score'] = 70
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse validation JSON: {e}")
            # Default: approve with generic category
            return {
                'approved': True,
                'category': 'general',
                'score': 65,
                'reason': 'Parse error - default approve'
            }
    
    def get_category_balance(self, posted_categories: list) -> Dict[str, int]:
        """
        Calculate category balance for diversity.
        
        Args:
            posted_categories: List of categories posted today
            
        Returns:
            Dict of category counts and whether we need more diversity
        """
        from collections import Counter
        
        category_counts = Counter(posted_categories)
        
        # Check which categories are underrepresented
        needs_more = {}
        for category, min_posts in Config.CATEGORY_MIN_POSTS_PER_DAY.items():
            current = category_counts.get(category, 0)
            if current < min_posts:
                needs_more[category] = min_posts - current
        
        return {
            'counts': dict(category_counts),
            'needs_more': needs_more,
            'most_posted': category_counts.most_common(1)[0][0] if category_counts else None,
            'total': len(posted_categories)
        }


# Global instance
_editor_instance = None


def get_content_editor() -> ContentEditor:
    """Get or create global content editor instance."""
    global _editor_instance
    if _editor_instance is None:
        _editor_instance = ContentEditor()
    return _editor_instance


# Convenience function
def validate_article(title: str, summary: str, source: str, content: str = "") -> Tuple[bool, str, Dict]:
    """
    Validate an article using the content editor.
    
    Args:
        title: Article title
        summary: Article summary
        source: News source
        content: Full content (optional)
        
    Returns:
        Tuple of (should_publish, category, metadata)
    """
    editor = get_content_editor()
    return editor.validate_content(title, summary, source, content)
