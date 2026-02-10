"""
Diversity Report Tool
View content diversity metrics for the last 24 hours.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.diversity import DiversityManager
from app.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Missing SUPABASE_URL or SUPABASE_KEY in .env")
        return
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    dm = DiversityManager(supabase)
    
    report = dm.get_diversity_report()
    
    print("\n" + "="*70)
    print("CONTENT DIVERSITY REPORT (Last 24 Hours)")
    print("="*70)
    
    if "message" in report:
        print(f"\n{report['message']}")
        return
    
    print(f"\nTotal Posts: {report['total_posts']}")
    print(f"Diversity Score: {report['diversity_score']}/100")
    
    print("\n\nTOP TOPICS:")
    print("-" * 40)
    for topic, count in list(report['topics'].items())[:5]:
        percentage = (count / report['total_posts']) * 100
        print(f"  {topic:20} {count:3} posts ({percentage:5.1f}%)")
    
    print("\n\nREGIONS:")
    print("-" * 40)
    for region, count in list(report['regions'].items())[:5]:
        percentage = (count / report['total_posts']) * 100
        print(f"  {region:20} {count:3} posts ({percentage:5.1f}%)")
    
    print("\n\nTOP EVENTS (Potential Duplicates):")
    print("-" * 40)
    for event, count in list(report['events'].items())[:5]:
        if count > 1:
            print(f"  {event[:50]:50} {count} posts")
    
    print("\n" + "="*70)
    print("\nDIVERSITY INTERPRETATION:")
    score = report['diversity_score']
    if score >= 80:
        print("  ✓ Excellent diversity - wide range of topics and regions")
    elif score >= 60:
        print("  → Good diversity - some repetition but generally balanced")
    elif score >= 40:
        print("  ⚠ Moderate diversity - consider posting from different topics/regions")
    else:
        print("  ✗ Low diversity - too much focus on same topics/regions")
    
    # Check for over-saturated topics
    for topic, count in report['topics'].items():
        percentage = (count / report['total_posts']) * 100
        if percentage > 50:
            print(f"\n  ⚠ WARNING: '{topic}' is {percentage:.0f}% of recent posts")
    
    # Check for over-saturated regions
    for region, count in report['regions'].items():
        percentage = (count / report['total_posts']) * 100
        if percentage > 60:
            print(f"  ⚠ WARNING: '{region}' is {percentage:.0f}% of recent posts")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
