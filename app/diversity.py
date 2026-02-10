"""
Content Diversity Manager
Ensures balanced coverage across topics, regions, and events to prevent echo chambers.
"""
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from app.logger import get_logger

logger = get_logger(__name__)

# Topic keywords for categorization
TOPIC_KEYWORDS = {
    "geopolitics": ["war", "military", "attack", "conflict", "sanction", "invasion", "strike", "troops", "defense", "missile"],
    "economy": ["market", "stock", "trade", "inflation", "gdp", "recession", "economy", "financial", "bank", "interest rate"],
    "tech": ["ai", "artificial intelligence", "tech", "software", "startup", "cybersecurity", "data", "algorithm", "crypto"],
    "health": ["covid", "pandemic", "vaccine", "health", "disease", "medical", "virus", "hospital", "treatment"],
    "climate": ["climate", "weather", "hurricane", "flood", "wildfire", "temperature", "carbon", "emission", "green energy"],
    "politics": ["election", "president", "congress", "parliament", "vote", "campaign", "minister", "government", "policy"],
    "disaster": ["earthquake", "tsunami", "disaster", "emergency", "evacuation", "casualty", "rescue"],
    "business": ["merger", "acquisition", "ceo", "revenue", "profit", "earnings", "ipo", "investment"],
}

REGION_KEYWORDS = {
    "north_america": ["usa", "us", "america", "united states", "canada", "mexico"],
    "south_america": ["venezuela", "brazil", "argentina", "colombia", "chile", "peru"],
    "europe": ["uk", "france", "germany", "italy", "spain", "russia", "ukraine"],
    "middle_east": ["israel", "iran", "saudi", "syria", "iraq", "lebanon", "yemen"],
    "asia": ["china", "japan", "korea", "india", "pakistan", "indonesia", "philippines"],
    "africa": ["nigeria", "south africa", "kenya", "egypt", "ethiopia"],
    "oceania": ["australia", "new zealand"],
}

class DiversityManager:
    """Manages content diversity across topics, regions, and events"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def extract_topics(self, headline: str, description: str) -> List[str]:
        """Extract topics from headline and description"""
        text = (headline + " " + description).lower()
        topics = []
        
        for topic, keywords in TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    topics.append(topic)
                    break
        
        return list(set(topics)) if topics else ["general"]
    
    def extract_region(self, headline: str, description: str, source: str) -> str:
        """Extract geographic region from content"""
        text = (headline + " " + description).lower()
        
        for region, keywords in REGION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return region
        
        # Check source for regional hints
        source_lower = source.lower()
        if "asia" in source_lower:
            return "asia"
        elif "europe" in source_lower:
            return "europe"
        elif "mundo" in source_lower or "arabic" in source_lower:
            return "middle_east"
        
        return "global"
    
    def extract_event_signature(self, headline: str) -> str:
        """
        Extract event signature to detect duplicate coverage.
        E.g., 'venezuela attack' for all Venezuela attack stories.
        """
        # Remove common filler words
        stopwords = {"breaking", "the", "a", "an", "in", "on", "at", "to", "for", "of", "by", "with"}
        words = re.findall(r'\b\w+\b', headline.lower())
        words = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Take first 3-4 significant words as signature
        signature = " ".join(sorted(words[:4]))
        return signature
    
    def get_recent_posts(self, hours: int = 24) -> List[Dict]:
        """Get posts from last N hours"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        try:
            result = self.supabase.table("posting_history") \
                .select("story_id, created_at") \
                .eq("success", True) \
                .gte("created_at", cutoff) \
                .execute()
            
            if not result.data:
                return []
            
            # Get story details
            story_ids = [row["story_id"] for row in result.data]
            stories = self.supabase.table("stories") \
                .select("id, headline, description, source, category") \
                .in_("id", story_ids) \
                .execute()
            
            return stories.data if stories.data else []
        except Exception as e:
            logger.warning(f"Failed to get recent posts: {e}")
            return []
    
    def calculate_diversity_penalty(self, headline: str, description: str, source: str, category: str) -> int:
        """
        Calculate diversity penalty (0-50 points reduction).
        Higher penalty = more repetitive content.
        
        Returns penalty to subtract from content score.
        """
        recent_posts = self.get_recent_posts(hours=24)
        
        if not recent_posts:
            return 0  # No recent posts, no penalty
        
        # Extract features of current story
        current_topics = self.extract_topics(headline, description)
        current_region = self.extract_region(headline, description, source)
        current_event = self.extract_event_signature(headline)
        
        # Analyze recent posts
        recent_topics = []
        recent_regions = []
        recent_events = []
        
        for post in recent_posts:
            recent_topics.extend(self.extract_topics(post["headline"], post.get("description", "")))
            recent_regions.append(self.extract_region(post["headline"], post.get("description", ""), post.get("source", "")))
            recent_events.append(self.extract_event_signature(post["headline"]))
        
        # Count occurrences
        topic_counts = Counter(recent_topics)
        region_counts = Counter(recent_regions)
        event_counts = Counter(recent_events)
        
        penalty = 0
        
        # Event duplication penalty (strongest)
        if current_event in event_counts:
            event_frequency = event_counts[current_event]
            if event_frequency >= 5:
                penalty += 40  # 5+ posts about same event = major penalty
                logger.info(f"Event '{current_event}' already posted {event_frequency}x: -40 penalty")
            elif event_frequency >= 3:
                penalty += 25  # 3-4 posts = significant penalty
                logger.info(f"Event '{current_event}' already posted {event_frequency}x: -25 penalty")
            elif event_frequency >= 2:
                penalty += 15  # 2 posts = moderate penalty
                logger.info(f"Event '{current_event}' already posted {event_frequency}x: -15 penalty")
        
        # Regional saturation penalty
        if current_region in region_counts:
            region_frequency = region_counts[current_region]
            region_percentage = (region_frequency / len(recent_posts)) * 100
            if region_percentage > 80:  # >80% from one region (relaxed from 60%)
                penalty += 15  # Reduced from 20
                logger.info(f"Region '{current_region}' is {region_percentage:.0f}% of recent posts: -15 penalty")
            elif region_percentage > 60:  # >60% from one region (relaxed from 40%)
                penalty += 8  # Reduced from 10
                logger.info(f"Region '{current_region}' is {region_percentage:.0f}% of recent posts: -8 penalty")
        
        # Topic saturation penalty
        for topic in current_topics:
            if topic in topic_counts:
                topic_frequency = topic_counts[topic]
                topic_percentage = (topic_frequency / len(recent_posts)) * 100
                if topic_percentage > 70:  # >70% same topic (relaxed from 50%)
                    penalty += 12  # Reduced from 15
                    logger.info(f"Topic '{topic}' is {topic_percentage:.0f}% of recent posts: -12 penalty")
                elif topic_percentage > 50:  # >50% same topic (relaxed from 30%)
                    penalty += 6  # Reduced from 8
                    logger.info(f"Topic '{topic}' is {topic_percentage:.0f}% of recent posts: -6 penalty")
        
        # Cap penalty at 50 (don't make it impossible for important breaking news)
        penalty = min(penalty, 50)
        
        if penalty > 0:
            logger.info(f"Total diversity penalty for '{headline[:50]}...': -{penalty} points")
        
        return penalty
    
    def get_diversity_report(self) -> Dict:
        """Get report on content diversity over last 24 hours"""
        recent_posts = self.get_recent_posts(hours=24)
        
        if not recent_posts:
            return {"message": "No recent posts"}
        
        topics = []
        regions = []
        events = []
        
        for post in recent_posts:
            topics.extend(self.extract_topics(post["headline"], post.get("description", "")))
            regions.append(self.extract_region(post["headline"], post.get("description", ""), post.get("source", "")))
            events.append(self.extract_event_signature(post["headline"]))
        
        return {
            "total_posts": len(recent_posts),
            "topics": dict(Counter(topics).most_common()),
            "regions": dict(Counter(regions).most_common()),
            "events": dict(Counter(events).most_common(10)),
            "diversity_score": self._calculate_overall_diversity(topics, regions)
        }
    
    def _calculate_overall_diversity(self, topics: List[str], regions: List[str]) -> int:
        """
        Calculate overall diversity score (0-100).
        100 = perfect diversity, 0 = all same topic/region.
        """
        if not topics or not regions:
            return 100
        
        # Use entropy-like measure
        topic_diversity = len(set(topics)) / len(topics) * 100
        region_diversity = len(set(regions)) / len(regions) * 100
        
        return int((topic_diversity + region_diversity) / 2)
