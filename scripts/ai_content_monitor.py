"""
AI Content Monitor - Intelligent decision system for publishing news

Uses Groq/Claude to evaluate if content is:
- Ethical and appropriate
- Engaging and interesting
- Novel and not repetitive
- Suitable for Instagram audience
- Trending or newsworthy

Makes final publishing decision based on AI analysis.
"""
import os
import sys
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger
from app.config import GROQ_API_KEY

try:
    from app.api_key_manager import get_groq_key, mark_groq_key_failed
    USE_KEY_ROTATION = True
except ImportError:
    USE_KEY_ROTATION = False

logger = get_logger(__name__)


class AIContentMonitor:
    """Intelligent content decision system powered by Groq"""
    
    def __init__(self):
        if USE_KEY_ROTATION:
            self.api_key = None
        else:
            self.api_key = GROQ_API_KEY
        self.model = "llama-3.3-70b-versatile"  # Changed from 8b to 70b
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def evaluate_content(self, headline: str, description: str, category: str, source: str) -> dict:
        """
        Evaluate content using AI to decide if it should be published.
        
        Returns:
            {
                'should_publish': bool,
                'confidence': float (0-1),
                'score': int (0-100),
                'reasoning': str,
                'ethics_score': int,
                'engagement_score': int,
                'novelty_score': int,
                'trending_score': int
            }
        """
        try:
            prompt = self._build_evaluation_prompt(headline, description, category, source)
            
            logger.info(f"🤖 AI evaluating: {headline[:60]}...")
            
            if USE_KEY_ROTATION:
                api_key = get_groq_key()
            else:
                api_key = self.api_key
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 600,
                },
                timeout=30,
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            logger.debug(f"AI Response: {response_text}")
            
            # Parse AI response
            decision = self._parse_ai_response(response_text, headline)
            return decision
            
        except requests.exceptions.HTTPError as he:
            logger.error(f"❌ API HTTP Error: {he}")
            if he.response.status_code in (429, 401) and USE_KEY_ROTATION:
                mark_groq_key_failed(api_key)
            try:
                error_detail = he.response.json()
                logger.error(f"Error details: {error_detail}")
            except:
                logger.error(f"Response text: {he.response.text}")
            # Fallback: default to not publishing if API fails
            return {
                'should_publish': False,
                'confidence': 0.3,
                'score': 0,
                'reasoning': f'AI API error: {str(he)}',
                'ethics_score': 0,
                'engagement_score': 0,
                'novelty_score': 0,
                'trending_score': 0
            }
        except Exception as e:
            logger.error(f"❌ AI evaluation failed: {e}")
            # Fallback: default to not publishing if AI fails
            return {
                'should_publish': False,
                'confidence': 0.3,
                'score': 0,
                'reasoning': f'AI system error: {str(e)}',
                'ethics_score': 0,
                'engagement_score': 0,
                'novelty_score': 0,
                'trending_score': 0
            }
    

    def _build_evaluation_prompt(self, headline: str, description: str, category: str, source: str) -> str:
        """Build evaluation prompt with strict quality standards"""
        return f"""You are a senior editorial director at The New York Times evaluating content for Instagram (@fastnewsorg).

Your job: Decide if this news story meets PROFESSIONAL JOURNALISM STANDARDS for publication.

STORY TO EVALUATE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Headline: {headline}
Description: {description}
Category: {category}
Source: {source}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EVALUATION CRITERIA (Rate 0-100 for each):

1. **JOURNALISTIC INTEGRITY** (Weight: 40%)
    - Is this factual and verifiable? (not speculation, rumors, or unconfirmed reports)
    - Is the source credible and reputable?
    - Is reporting balanced (not heavily biased or one-sided)?
    - Does it avoid misinformation, conspiracy theories, or fake news?
   
    SCORING:
    • 90-100: Verified facts, credible source (Reuters, BBC, AP, major newspapers)
    • 70-89:  Likely accurate, reputable source, minor uncertainty
    • 50-69:  Some concerns but publishable (lower-tier sources, slight bias)
    • Below 50: REJECT (tabloid-quality, unverified, biased, suspicious)

2. **NEWS VALUE** (Weight: 30%)
    - Is this actually newsworthy? (significance, impact, timeliness)
    - Does it matter to a general audience?
    - Is this breaking news or old/stale content?
    - Is this interesting enough for Instagram?
   
    SCORING:
    • 90-100: Major news event, breaking story, high impact
    • 70-89:  Important news, trending topic, strong interest
    • 50-69:  Moderate interest, niche appeal
    • Below 50: REJECT (boring, outdated, nobody cares)

3. **CONTENT QUALITY** (Weight: 20%)
    - Is the writing clear and professional?
    - Does it have enough detail/context?
    - Is it well-structured and coherent?
    - Does it avoid clickbait language?
   
    SCORING:
    • 90-100: Excellent journalism, clear writing, good context
    • 70-89:  Good quality, minor issues
    • 50-69:  Acceptable but could be better
    • Below 50: REJECT (poorly written, confusing, clickbait)

4. **AUDIENCE FIT** (Weight: 10%)
    - Will Instagram users engage with this?
    - Is it visually/contextually appropriate for social media?
    - Does it fit our brand (professional news, not entertainment gossip)?
   
    SCORING:
    • 90-100: Perfect for Instagram news audience
    • 70-89:  Good fit, strong engagement potential
    • 50-69:  Okay fit, moderate engagement
    • Below 50: REJECT (wrong platform, won't resonate)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PUBLISHING THRESHOLDS:
✅ PUBLISH if:
    - Overall Score ≥ 70 AND
    - Journalistic Integrity ≥ 60 AND
    - News Value ≥ 60

❌ REJECT if:
    - Overall Score < 70 OR
    - Journalistic Integrity < 60 OR
    - News Value < 60

RESPOND IN THIS EXACT JSON FORMAT (no additional text):
{{
     "should_publish": true/false,
     "confidence": 0.0-1.0,
     "integrity_score": 0-100,
     "news_value_score": 0-100,
     "quality_score": 0-100,
     "audience_score": 0-100,
     "overall_score": 0-100,
     "reasoning": "Explain your decision in 1-2 sentences"
}}

Be STRICT. When in doubt, REJECT. We only want HIGH-QUALITY journalism.
"""
    
    def _parse_ai_response(self, response_text: str, headline: str) -> dict:
        """Parse AI response with stricter validation"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                logger.warning(f"Could not parse AI response")
                return self._rejection_fallback("Parse error")
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            integrity = data.get('integrity_score', 0)
            news_value = data.get('news_value_score', 0)
            quality = data.get('quality_score', 0)
            audience = data.get('audience_score', 0)
            overall_score = int(
                (integrity * 0.40) +
                (news_value * 0.30) +
                (quality * 0.20) +
                (audience * 0.10)
            )
            should_publish = (
                overall_score >= 70 and
                integrity >= 60 and
                news_value >= 60
            )
            decision = {
                'should_publish': should_publish,
                'confidence': min(1.0, max(0.0, data.get('confidence', 0.5))),
                'score': overall_score,
                'ethics_score': integrity,  # Legacy field name
                'engagement_score': news_value,  # Legacy field name
                'novelty_score': quality,  # Legacy field name
                'trending_score': audience,  # Legacy field name
                'reasoning': data.get('reasoning', 'No reasoning provided')
            }
            if integrity < 60:
                decision['should_publish'] = False
                decision['reasoning'] = f"Failed integrity check ({integrity}/100)"
            elif news_value < 60:
                decision['should_publish'] = False
                decision['reasoning'] = f"Insufficient news value ({news_value}/100)"
            elif overall_score < 70:
                decision['should_publish'] = False
                decision['reasoning'] = f"Below quality threshold ({overall_score}/100)"
            logger.info(f"📊 AI Decision: {'✅ PUBLISH' if decision['should_publish'] else '❌ REJECT'}")
            logger.info(f"   Overall: {overall_score}/100 | Integrity: {integrity} | News: {news_value} | Quality: {quality}")
            logger.info(f"   Reasoning: {decision['reasoning']}")
            return decision
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._rejection_fallback(str(e))

    def _rejection_fallback(self, reason: str) -> dict:
        """Return rejection decision when AI fails"""
        return {
            'should_publish': False,
            'confidence': 0.1,
            'score': 0,
            'reasoning': f'AI evaluation failed: {reason}',
            'ethics_score': 0,
            'engagement_score': 0,
            'novelty_score': 0,
            'trending_score': 0
        }


def should_publish_ai(headline: str, description: str, category: str = "general", source: str = "unknown") -> tuple:
    """
    Quick function to evaluate if content should be published.
    
    Returns:
        (should_publish: bool, score: int, reasoning: str)
    """
    monitor = AIContentMonitor()
    decision = monitor.evaluate_content(headline, description, category, source)
    
    return (
        decision['should_publish'],
        decision['score'],
        decision['reasoning']
    )


if __name__ == "__main__":
    # Test the monitor
    print("=" * 70)
    print("🤖 AI CONTENT MONITOR TEST")
    print("=" * 70)
    
    test_stories = [
        {
            "headline": "Bitcoin Reaches All-Time High Amid Global Market Shift",
            "description": "Cryptocurrency surges past $100,000 as institutional investors increase holdings",
            "category": "tech",
            "source": "Reuters"
        },
        {
            "headline": "New Cancer Treatment Shows 90% Success Rate in Clinical Trials",
            "description": "Revolutionary therapy approved for Phase 3 human trials, offers hope for thousands",
            "category": "health",
            "source": "Medical News Today"
        },
        {
            "headline": "Political Figure X Does Mundane Task",
            "description": "Politician seen walking down street in ordinary clothing",
            "category": "politics",
            "source": "Tabloid"
        }
    ]
    
    monitor = AIContentMonitor()
    
    for story in test_stories:
        print(f"\n📰 Story: {story['headline']}")
        decision = monitor.evaluate_content(
            story['headline'],
            story['description'],
            story['category'],
            story['source']
        )
        print(f"   Should Publish: {decision['should_publish']}")
        print(f"   Score: {decision['score']}/100")
        print(f"   Reasoning: {decision['reasoning']}")
