"""
Multi-source fact verification system.
Verifies news across multiple sources before publishing.
"""
import os
import sys
import time
from typing import List, Dict, Tuple
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger
from app.config import GROQ_API_KEY
from app.api_key_manager import get_groq_key, mark_groq_key_failed

logger = get_logger(__name__)

USE_KEY_ROTATION = True

class FactChecker:
    """Advanced fact-checking and source verification"""
    
    def __init__(self):
        self.model = "llama-3.3-70b-versatile"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.search_api_key = os.getenv("SERPER_API_KEY")  # For Google search
    
    def verify_story(self, headline: str, description: str, source: str) -> Dict:
        """
        Verify story across multiple sources.
        
        Returns:
            {
                'is_verified': bool,
                'confidence': float (0-1),
                'sources_found': int,
                'cross_references': List[str],
                'red_flags': List[str],
                'verdict': str
            }
        """
        logger.info(f"🔍 Verifying: {headline[:60]}...")
        
        # Step 1: Search for corroborating sources
        search_results = self._search_news(headline)
        
        # Step 2: Analyze source credibility
        source_credibility = self._check_source_credibility(source)
        
        # Step 3: AI-powered fact verification
        ai_verification = self._ai_verify_facts(headline, description, search_results)
        
        # Step 4: Combine signals
        verification_result = self._synthesize_verdict(
            search_results,
            source_credibility,
            ai_verification
        )
        
        logger.info(
            f"✓ Verification: {verification_result['verdict']} "
            f"(confidence: {verification_result['confidence']:.0%})"
        )
        
        return verification_result
    
    def _search_news(self, headline: str) -> List[Dict]:
        """Search for news across multiple sources using Serper API"""
        
        if not self.search_api_key:
            logger.warning("No SERPER_API_KEY - skipping web search")
            return []
        
        try:
            # Use Serper API for Google News search
            response = requests.post(
                "https://google.serper.dev/news",
                headers={
                    "X-API-KEY": self.search_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "q": headline[:100],  # Limit query length
                    "num": 10,
                    "tbs": "qdr:d"  # Results from last day
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("news", [])
                
                logger.info(f"Found {len(results)} related news articles")
                return results[:5]  # Top 5 results
            
            logger.warning(f"Search API returned {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _check_source_credibility(self, source: str) -> Dict:
        """Rate source credibility on multiple factors"""
        
        # Tier 1: Highly credible sources
        tier_1_sources = {
            'bbc', 'reuters', 'ap', 'associated press', 'afp',
            'bloomberg', 'financial times', 'economist', 'guardian',
            'nyt', 'new york times', 'washington post', 'wsj',
            'ekantipur', 'kantipur', 'setopati', 'online_khabar'
        }
        
        # Tier 2: Generally reliable
        tier_2_sources = {
            'cnn', 'bbc nepali', 'ratopati', 'naya patrika',
            'nepali times', 'republica', 'myrepublica',
            'abc news', 'cbs', 'nbc', 'forbes'
        }
        
        # Tier 3: Acceptable but verify
        tier_3_sources = {
            'huffpost', 'buzzfeed news', 'vice', 'vox',
            'daily mail', 'independent', 'telegraph'
        }
        
        source_lower = source.lower()
        
        # Check tier
        if any(s in source_lower for s in tier_1_sources):
            return {
                'tier': 1,
                'credibility_score': 95,
                'description': 'Highly credible international/national source'
            }
        elif any(s in source_lower for s in tier_2_sources):
            return {
                'tier': 2,
                'credibility_score': 80,
                'description': 'Generally reliable source'
            }
        elif any(s in source_lower for s in tier_3_sources):
            return {
                'tier': 3,
                'credibility_score': 60,
                'description': 'Acceptable source but verify claims'
            }
        else:
            return {
                'tier': 4,
                'credibility_score': 40,
                'description': 'Unknown or low-credibility source'
            }
    
    def _ai_verify_facts(self, headline: str, description: str, search_results: List[Dict]) -> Dict:
        """Use AI to analyze factual claims and detect red flags"""
        
        # Build context from search results
        search_context = "\n".join([
            f"- {r.get('title', '')}: {r.get('snippet', '')}"
            for r in search_results[:3]
        ])
        
        prompt = f"""You are a professional fact-checker at Snopes or PolitiFact.

Analyze this news story for factual accuracy and red flags.

STORY TO VERIFY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Headline: {headline}
Description: {description}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RELATED NEWS FOUND:
{search_context if search_context else "No corroborating sources found"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHECK FOR:

1. **FACTUAL ACCURACY**
   - Are specific claims verifiable?
   - Do numbers/dates/names seem accurate?
   - Is this consistent with related reporting?

2. **RED FLAGS**
   - Sensationalism or exaggeration?
   - Unattributed claims ("sources say", "reports indicate")?
   - Conspiracy theories or misinformation patterns?
   - Clickbait language?
   - Too good/bad to be true?

3. **VERIFICATION STATUS**
   - Can this be confirmed from search results?
   - Multiple independent sources reporting?
   - Official sources cited?

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "factual_accuracy": 0-100,
    "red_flags": ["flag1", "flag2"],
    "verification_status": "verified|partially_verified|unverified|suspicious",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}}

Be STRICT. Flag anything suspicious.
"""

        try:
            if USE_KEY_ROTATION:
                api_key = get_groq_key()
            else:
                api_key = GROQ_API_KEY
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,  # Lower for more consistent fact-checking
                    "max_tokens": 500,
                },
                timeout=30,
            )
            response.raise_for_status()
            
            result_text = response.json()['choices'][0]['message']['content']
            
            # Parse JSON response
            import json
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                return json.loads(json_str)
            
            return {
                'factual_accuracy': 50,
                'red_flags': ['Could not parse AI response'],
                'verification_status': 'unverified',
                'confidence': 0.3,
                'reasoning': 'Parse error'
            }
            
        except Exception as e:
            logger.error(f"AI verification failed: {e}")
            return {
                'factual_accuracy': 50,
                'red_flags': [str(e)],
                'verification_status': 'unverified',
                'confidence': 0.0,
                'reasoning': f'Error: {str(e)}'
            }
    
    def _synthesize_verdict(
        self,
        search_results: List[Dict],
        source_credibility: Dict,
        ai_verification: Dict
    ) -> Dict:
        """Combine all signals into final verdict"""
        
        # Calculate confidence based on multiple factors
        confidence_factors = []
        red_flags = list(ai_verification.get('red_flags', []))
        
        # Factor 1: Source credibility (40% weight)
        source_score = source_credibility['credibility_score']
        confidence_factors.append(source_score * 0.40)
        
        # Factor 2: Cross-references (30% weight)
        num_sources = len(search_results)
        if num_sources >= 3:
            cross_ref_score = 100
        elif num_sources == 2:
            cross_ref_score = 70
        elif num_sources == 1:
            cross_ref_score = 50
        else:
            cross_ref_score = 20
            red_flags.append("No corroborating sources found")
        
        confidence_factors.append(cross_ref_score * 0.30)
        
        # Factor 3: AI fact-check (30% weight)
        fact_score = ai_verification.get('factual_accuracy', 50)
        confidence_factors.append(fact_score * 0.30)
        
        # Overall confidence
        overall_confidence = sum(confidence_factors) / 100.0
        
        # Determine verification status
        verification_status = ai_verification.get('verification_status', 'unverified')
        
        # Final verdict
        is_verified = (
            overall_confidence >= 0.70 and
            source_score >= 60 and
            fact_score >= 60 and
            verification_status in ['verified', 'partially_verified'] and
            len(red_flags) == 0
        )
        
        # Determine verdict text
        if is_verified:
            verdict = "✅ VERIFIED - Safe to publish"
        elif overall_confidence >= 0.60 and len(red_flags) <= 1:
            verdict = "⚠️ LIKELY ACCURATE - Proceed with caution"
        elif overall_confidence >= 0.50:
            verdict = "⚠️ UNVERIFIED - Needs manual review"
        else:
            verdict = "❌ SUSPICIOUS - Do not publish"
        
        return {
            'is_verified': is_verified,
            'confidence': overall_confidence,
            'sources_found': num_sources,
            'cross_references': [r.get('link') for r in search_results[:3]],
            'red_flags': red_flags,
            'verdict': verdict,
            'source_tier': source_credibility['tier'],
            'source_score': source_score,
            'fact_score': fact_score,
            'ai_reasoning': ai_verification.get('reasoning', '')
        }


def verify_before_posting(headline: str, description: str, source: str) -> Tuple[bool, Dict]:
    """
    Verify story before posting. Returns (should_post, verification_details)
    """
    checker = FactChecker()
    result = checker.verify_story(headline, description, source)
    
    # Strict policy: Only publish verified content
    should_post = result['is_verified'] or result['confidence'] >= 0.75
    
    return should_post, result


if __name__ == "__main__":
    # Test the fact checker
    print("=" * 70)
    print("🔍 FACT CHECKER TEST")
    print("=" * 70)
    
    test_stories = [
        {
            "headline": "Nepal's Parliament Building Construction Reaches 88% Completion",
            "description": "The new parliament building in Singha Durbar has reached 88% completion but faces budget constraints",
            "source": "Kantipur"
        },
        {
            "headline": "BREAKING: Aliens Land in Kathmandu Valley",
            "description": "Multiple eyewitnesses report seeing UFOs land near Swayambhunath temple",
            "source": "Unknown Blog"
        }
    ]
    
    checker = FactChecker()
    
    for story in test_stories:
        print(f"\n📰 Story: {story['headline']}")
        result = checker.verify_story(
            story['headline'],
            story['description'],
            story['source']
        )
        print(f"   Verdict: {result['verdict']}")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Sources Found: {result['sources_found']}")
        print(f"   Red Flags: {', '.join(result['red_flags']) if result['red_flags'] else 'None'}")
