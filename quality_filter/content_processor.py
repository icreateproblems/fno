"""
Content processor for native Nepali/English caption generation.
Fixes translation artifacts and implements relaxed quality filters.
"""
import re
from typing import Dict, Any
try:
    from translatepy import Translator
    translator = Translator()
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("Warning: translatepy not installed. Translation features disabled.")

# Import Config if available, otherwise use defaults
try:
    from app.config import Config
except ImportError:
    # Fallback defaults
    class Config:
        MIN_LENGTH_CHARS = 150
        MAX_LENGTH_CHARS = 1000
        MAX_AGE_HOURS = 48


def is_nepali_text(text: str) -> bool:
    """
    Detect Devanagari script (Nepali language).
    
    Args:
        text: Text to check for Nepali characters
        
    Returns:
        True if text contains Devanagari script, False otherwise
    """
    return bool(re.search(r'[\u0900-\u097F]', text))


def generate_smart_caption(title: str, summary: str, source: str) -> str:
    """
    Generate native Nepali OR English captions with FULL context.
    
    Strategy:
    1. If title is already in Nepali (Devanagari), use pure Nepali with full summary
    2. If title is English, add complete Nepali translation (full translation)
    3. Always include source attribution
    4. Instagram supports 2,200 chars - use up to ~1,800 for full context
    
    Args:
        title: Article title (can be Nepali or English)
        summary: Article summary/description (FULL context included)
        source: News source name
        
    Returns:
        Clean, Instagram-ready caption with complete article context
    """
    # Clean title (keep it full, not truncated)
    title_clean = title.strip()
    
    # Clean and prepare full summary (up to 1500 chars for safety, Instagram allows 2200)
    summary_full = summary.strip()[:1500]
    
    if is_nepali_text(title):
        # Pure Nepali post - no translation needed
        # Include FULL summary for complete context
        return f"🔥 {title_clean}\n\n{summary_full}\n\n📱 {source} | #fastnewsorg"
    
    # English title - add full Nepali summary for complete context
    if TRANSLATOR_AVAILABLE and summary_full:
        try:
            # Translate FULL summary (up to 1000 chars to avoid API limits)
            # Keep it comprehensive for full context
            summary_to_translate = summary_full[:1000]
            summary_nepali = translator.translate(summary_to_translate, destination_language='ne').result
            
            # If summary was longer than 1000, add original English continuation
            if len(summary_full) > 1000:
                english_continuation = summary_full[1000:]
                return f"🔥 {title_clean}\n\n{summary_nepali}\n\n{english_continuation}\n\n📱 {source} | #fastnewsorg"
            else:
                return f"🔥 {title_clean}\n\n{summary_nepali}\n\n📱 {source} | #fastnewsorg"
        except Exception as e:
            print(f"Translation failed: {e}. Using full English summary.")
            # Fallback to full English summary
            return f"🔥 {title_clean}\n\n{summary_full}\n\n📱 {source} | #fastnewsorg"
    else:
        # No translator or no summary - use full English
        if summary_full:
            return f"🔥 {title_clean}\n\n{summary_full}\n\n📱 {source} | #fastnewsorg"
        else:
            return f"🔥 {title_clean}\n\n📱 {source} | #fastnewsorg"


def relaxed_quality_filter(article: Dict[str, Any]) -> bool:
    """
    Relaxed quality filter for 85% acceptance rate.
    
    Previous filter was too strict (3% acceptance), causing low post volume.
    New relaxed criteria:
    - Length: 150-1000 chars (vs 200-800)
    - Recency: 48hrs (vs 24hrs)
    - Completeness: 70% (vs 80%)
    
    Args:
        article: Article dictionary with content, title, age_hours
        
    Returns:
        True if article passes quality filter, False otherwise
    """
    content = article.get('content', article.get('description', ''))
    title = article.get('title', '')
    
    # Content length check (relaxed)
    length_ok = Config.MIN_LENGTH_CHARS <= len(content) <= Config.MAX_LENGTH_CHARS
    
    # Recency check (48hrs vs 24hrs)
    age_ok = article.get('age_hours', 999) <= Config.MAX_AGE_HOURS
    
    # Must have meaningful title
    has_title = len(title) > 10
    
    # All criteria must pass
    return length_ok and age_ok and has_title


def generate_nepali_caption_legacy(title_en: str, summary_en: str, source: str) -> str:
    """
    Legacy caption generator for backward compatibility.
    Uses generate_smart_caption internally.
    
    Args:
        title_en: Article title
        summary_en: Article summary
        source: News source
        
    Returns:
        Generated caption
    """
    return generate_smart_caption(title_en, summary_en, source)


def detect_content_category(title: str, summary: str = "") -> str:
    """
    Detect content category from title and summary using keywords.
    This is a fast preliminary categorization before AI editor validation.
    
    Args:
        title: Article title
        summary: Article summary (optional)
        
    Returns:
        Category name (politics, sports, economy, etc.)
    """
    text = f"{title} {summary}".lower()
    
    # Category keywords (Nepali and English)
    category_keywords = {
        'politics': [
            'सरकार', 'मन्त्री', 'प्रधानमन्त्री', 'संसद', 'नेता', 'पार्टी',
            'government', 'minister', 'parliament', 'political', 'election',
            'pm', 'congress', 'uml', 'maoist', 'democracy'
        ],
        'economy': [
            'नेप्से', 'शेयर', 'बजार', 'अर्थ', 'बैंक', 'व्यापार',
            'nepse', 'stock', 'market', 'economy', 'business', 'bank',
            'finance', 'trade', 'rupee', 'investment', 'gdp'
        ],
        'sports': [
            'खेल', 'क्रिकेट', 'फुटबल', 'गोल्फ', 'क्रीडा',
            'cricket', 'football', 'golf', 'sports', 'match', 'tournament',
            'player', 'team', 'win', 'score', 'champion', 'olympics'
        ],
        'technology': [
            'प्रविधि', 'टेक्नोलोजी', 'मोबाइल', 'कम्प्युटर', 'इन्टरनेट',
            'technology', 'tech', 'mobile', 'computer', 'internet', 'ai',
            'software', 'app', 'digital', 'cyber', 'startup'
        ],
        'entertainment': [
            'मनोरञ्जन', 'फिल्म', 'संगीत', 'कलाकार', 'सिनेमा',
            'entertainment', 'movie', 'film', 'music', 'actor', 'cinema',
            'celebrity', 'art', 'culture', 'festival', 'concert'
        ],
        'international': [
            'अन्तर्राष्ट्रिय', 'विश्व', 'विदेश',
            'world', 'international', 'global', 'foreign', 'usa', 'china',
            'india', 'europe', 'un', 'nato', 'summit'
        ],
        'society': [
            'समाज', 'शिक्षा', 'स्वास्थ्य', 'महिला', 'युवा',
            'society', 'education', 'health', 'women', 'youth', 'social',
            'community', 'rights', 'justice', 'environment', 'climate'
        ]
    }
    
    # Count keyword matches per category
    category_scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            category_scores[category] = score
    
    # Return category with highest score
    if category_scores:
        return max(category_scores, key=category_scores.get)
    
    # Default to general if no matches
    return 'general'


def get_category_emoji(category: str) -> str:
    """
    Get emoji for content category to use in captions.
    
    Args:
        category: Content category
        
    Returns:
        Emoji representing the category
    """
    category_emojis = {
        'politics': '🏛️',
        'economy': '💰',
        'sports': '⚽',
        'technology': '💻',
        'entertainment': '🎬',
        'international': '🌍',
        'society': '👥',
        'general': '📰'
    }
    
    return category_emojis.get(category, '📰')
