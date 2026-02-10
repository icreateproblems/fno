"""
Test the modernized content safety system
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.content_safety import ContentSafety

def test_content_grading():
    """Test AI-based content grade evaluation"""
    safety = ContentSafety()
    
    print("=" * 70)
    print("Testing Content Grade Evaluation System (AI-Based)")
    print("=" * 70)
    print()
    
    test_cases = [
        # Should be FILTERED (high-grade)
        ("5 people passed away in Kathmandu accident", True),
        ("Major incident reported in Kashmir region", True),
        ("Remains found after earthquake in Nepal", True),
        ("Casualty count rises to 50 in incident", True),
        
        # Should be APPROVED (appropriate)
        ("New government policy announced today", False),
        ("NEPSE stock market reaches new high", False),
        ("Cricket team crushes competition in final", False),  # Context matters!
        ("Tech startup raises $1M in funding round", False),
        ("Nepal wins international award for tourism", False),
    ]
    
    results = []
    for text, should_filter in test_cases:
        needs_filter, reasons, intensity = safety.check_content_grade(text, use_ai=True)
        
        status = "🔴 FILTERED" if needs_filter else "🟢 APPROVED"
        expected = "🔴 FILTERED" if should_filter else "🟢 APPROVED"
        match = "✅" if (needs_filter == should_filter) else "❌"
        
        print(f"{match} {status} | Intensity: {intensity:.2f} | Expected: {expected}")
        print(f"   Text: {text[:60]}")
        if reasons:
            print(f"   Reason: {reasons[0]}")
        print()
        
        results.append((needs_filter == should_filter, text))
    
    # Summary
    correct = sum(1 for r, _ in results if r)
    total = len(results)
    accuracy = (correct / total) * 100
    
    print("=" * 70)
    print(f"Results: {correct}/{total} correct ({accuracy:.1f}% accuracy)")
    print("=" * 70)
    
    if accuracy >= 80:
        print("✅ Content grading system is working well!")
    else:
        print("⚠️  Consider adjusting AI intensity threshold")
        print("   See: app/content_safety.py - check_content_grade()")

if __name__ == "__main__":
    test_content_grading()
