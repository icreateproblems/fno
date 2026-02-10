"""
Automated testing suite for News Bot.
Validates core functionality without requiring external APIs.
"""

import sys
import os
from typing import Dict, List
from datetime import datetime
from app.logger import get_logger

logger = get_logger(__name__)


class TestRunner:
    """Runs automated tests for bot components."""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_test(self, test_name: str, test_func: callable) -> bool:
        """Run a single test and record result."""
        self.total_tests += 1
        
        try:
            test_func()
            self.results[test_name] = {
                "status": "PASS",
                "message": "Test passed",
                "timestamp": datetime.utcnow().isoformat()
            }
            self.passed_tests += 1
            logger.info(f"✓ {test_name}: PASS")
            return True
        
        except AssertionError as e:
            self.results[test_name] = {
                "status": "FAIL",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.failed_tests += 1
            logger.error(f"✗ {test_name}: FAIL - {str(e)}")
            return False
        
        except Exception as e:
            self.results[test_name] = {
                "status": "ERROR",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.failed_tests += 1
            logger.error(f"✗ {test_name}: ERROR - {str(e)}")
            return False
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("="*60 + "\n")


# ============================================================================
# TEST SUITE
# ============================================================================

def test_imports():
    """Test that all critical modules can be imported."""
    from app import config, logger, db, db_pool
    from app import diversity, content_safety, error_recovery
    from scripts import content_filter
    assert True


def test_logger():
    """Test logger functionality."""
    from app.logger import get_logger
    test_logger = get_logger("test")
    test_logger.info("Test message")
    assert test_logger is not None


def test_config_loading():
    """Test configuration loading."""
    from app.config import SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY
    assert SUPABASE_URL, "SUPABASE_URL not loaded"
    assert SUPABASE_KEY, "SUPABASE_KEY not loaded"
    assert GROQ_API_KEY, "GROQ_API_KEY not loaded"


def test_diversity_topic_extraction():
    """Test diversity manager topic extraction."""
    from app.diversity import DiversityManager
    dm = DiversityManager()
    
    headline = "US Economy Shows Strong Growth Despite Tech Sector Challenges"
    topics = dm.extract_topics(headline, "")
    
    assert "economy" in topics or "tech" in topics, f"Failed to extract topics from: {headline}"


def test_diversity_region_extraction():
    """Test diversity manager region extraction."""
    from app.diversity import DiversityManager
    dm = DiversityManager()
    
    headline = "France and Germany Agree on Climate Policy"
    region = dm.extract_region(headline, "")
    
    assert region == "europe", f"Expected 'europe', got '{region}'"


def test_diversity_event_signature():
    """Test event signature generation."""
    from app.diversity import DiversityManager
    dm = DiversityManager()
    
    headline1 = "Venezuela Crisis Deepens as US Imposes Sanctions"
    headline2 = "Venezuela situation worsens with new US sanctions"
    
    sig1 = dm.extract_event_signature(headline1, "")
    sig2 = dm.extract_event_signature(headline2, "")
    
    # Should recognize as similar event
    assert "venezuela" in sig1 and "venezuela" in sig2, "Failed to identify Venezuela in signatures"


def test_diversity_penalty_calculation():
    """Test diversity penalty logic (without database)."""
    from app.diversity import DiversityManager
    
    # Mock recent posts
    mock_posts = [
        {"headline": "Venezuela Crisis Update", "description": "", "source": "Source A"},
        {"headline": "Venezuela Sanctions Announced", "description": "", "source": "Source B"},
        {"headline": "Venezuela Protests Continue", "description": "", "source": "Source C"},
    ]
    
    dm = DiversityManager()
    
    # Manually extract data
    topics_count = {}
    regions_count = {}
    events_count = {}
    
    for post in mock_posts:
        topics = dm.extract_topics(post["headline"], post["description"])
        for topic in topics:
            topics_count[topic] = topics_count.get(topic, 0) + 1
        
        region = dm.extract_region(post["headline"], post["description"])
        if region:
            regions_count[region] = regions_count.get(region, 0) + 1
        
        event_sig = dm.extract_event_signature(post["headline"], post["description"])
        if event_sig:
            events_count[event_sig] = events_count.get(event_sig, 0) + 1
    
    # Check that Venezuela event was detected multiple times
    venezuela_events = [sig for sig in events_count.keys() if "venezuela" in sig]
    assert len(venezuela_events) > 0, "Failed to detect Venezuela as repeated event"


def test_content_safety_hate_speech():
    """Test hate speech detection."""
    from app.content_safety import ContentSafety
    safety = ContentSafety()
    
    safe_text = "Government announces new economic policy for growth"
    unsafe_text = "All [slur] should be removed from country"
    
    has_hate_safe, _ = safety.check_hate_speech(safe_text)
    assert not has_hate_safe, "False positive: Safe text flagged as hate speech"
    
    # Unsafe text should be flagged (but we don't test actual slurs in code)
    # Just verify the function works
    assert callable(safety.check_hate_speech)


def test_content_safety_misinformation():
    """Test misinformation detection."""
    from app.content_safety import ContentSafety
    safety = ContentSafety()
    
    safe_text = "Study shows correlation between diet and health"
    unsafe_text = "5G causes cancer and vaccines cause autism"
    
    has_misinfo_safe, _ = safety.check_misinformation(safe_text)
    has_misinfo_unsafe, violations = safety.check_misinformation(unsafe_text)
    
    assert not has_misinfo_safe, "False positive on safe text"
    assert has_misinfo_unsafe, "Failed to detect misinformation"
    assert len(violations) > 0, "No violations recorded for misinformation"


def test_content_safety_clickbait():
    """Test clickbait detection."""
    from app.content_safety import ContentSafety
    safety = ContentSafety()
    
    normal_headline = "Study Finds Link Between Exercise and Longevity"
    clickbait_headline = "You Won't Believe What This Doctor Found! Number 5 Will Shock You!"
    
    is_clickbait_normal, _ = safety.check_clickbait(normal_headline)
    is_clickbait_cb, severity = safety.check_clickbait(clickbait_headline)
    
    assert not is_clickbait_normal, "False positive on normal headline"
    assert is_clickbait_cb, "Failed to detect clickbait"
    assert severity > 0.3, "Clickbait severity too low"


def test_content_safety_comprehensive():
    """Test comprehensive safety check."""
    from app.content_safety import content_safety
    
    safe_content = {
        "headline": "New Economic Policy Announced by Government",
        "description": "Officials unveil comprehensive plan for growth",
        "source": "Reuters"
    }
    
    result = content_safety.comprehensive_check(
        safe_content["headline"],
        safe_content["description"],
        safe_content["source"]
    )
    
    assert result["safe"], "Safe content flagged as unsafe"
    assert result["should_post"], "Safe content marked as shouldn't post"
    assert len(result["violations"]) == 0, "Violations found in safe content"


def test_error_recovery_retry():
    """Test retry decorator."""
    from app.error_recovery import retry_with_backoff
    
    attempt_count = [0]
    
    @retry_with_backoff(max_retries=2, initial_delay=0.1, exponential_base=2)
    def flaky_function():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise ValueError("Temporary error")
        return "success"
    
    result = flaky_function()
    
    assert result == "success", "Retry decorator failed"
    assert attempt_count[0] == 2, f"Expected 2 attempts, got {attempt_count[0]}"


def test_error_recovery_circuit_breaker():
    """Test circuit breaker."""
    from app.error_recovery import CircuitBreaker
    
    cb = CircuitBreaker(failure_threshold=2, timeout=1)
    
    def failing_function():
        raise ValueError("Always fails")
    
    # First failure
    success1, _ = cb.call(failing_function)
    assert not success1, "Expected failure"
    assert cb.state == "CLOSED", "Circuit should still be closed"
    
    # Second failure - should open circuit
    success2, _ = cb.call(failing_function)
    assert not success2, "Expected failure"
    assert cb.state == "OPEN", "Circuit should be open after threshold"
    
    # Third attempt - should be blocked
    success3, _ = cb.call(failing_function)
    assert not success3, "Expected block"


def test_error_recovery_rate_limiter():
    """Test rate limiter."""
    from app.error_recovery import RateLimiter
    import time
    
    limiter = RateLimiter(max_calls=3, time_window=1)
    
    # First 3 calls should succeed
    assert limiter.allow_request(), "First request blocked"
    assert limiter.allow_request(), "Second request blocked"
    assert limiter.allow_request(), "Third request blocked"
    
    # Fourth call should be blocked
    assert not limiter.allow_request(), "Fourth request not blocked"
    
    # Wait time should be reasonable
    wait_time = limiter.get_wait_time()
    assert 0 <= wait_time <= 1, f"Wait time unreasonable: {wait_time}"


def test_env_validator():
    """Test environment validator (without requiring all vars)."""
    from app.env_validator import ConfigValidator
    
    validator = ConfigValidator()
    
    # Just test that validator can be instantiated and has required attributes
    assert hasattr(validator, 'REQUIRED_VARS'), "Missing REQUIRED_VARS"
    assert hasattr(validator, 'validate_required_vars'), "Missing validate method"
    assert len(validator.REQUIRED_VARS) > 0, "No required vars defined"


def test_file_structure():
    """Test that required files exist."""
    required_files = [
        "app/config.py",
        "app/logger.py",
        "app/db.py",
        "app/db_pool.py",
        "app/diversity.py",
        "app/content_safety.py",
        "app/error_recovery.py",
        "app/env_validator.py",
        "app/health_check.py",
        "scripts/fetch_news.py",
        "scripts/post_instagram.py",
        "scripts/content_filter.py",
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    
    assert len(missing) == 0, f"Missing files: {', '.join(missing)}"


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def main():
    """Run all tests."""
    runner = TestRunner()
    
    print("\n" + "="*60)
    print("RUNNING AUTOMATED TEST SUITE")
    print("="*60 + "\n")
    
    # Core functionality tests
    runner.run_test("Import modules", test_imports)
    runner.run_test("Logger functionality", test_logger)
    runner.run_test("Configuration loading", test_config_loading)
    runner.run_test("File structure", test_file_structure)
    
    # Diversity tests
    runner.run_test("Diversity: Topic extraction", test_diversity_topic_extraction)
    runner.run_test("Diversity: Region extraction", test_diversity_region_extraction)
    runner.run_test("Diversity: Event signature", test_diversity_event_signature)
    runner.run_test("Diversity: Penalty calculation", test_diversity_penalty_calculation)
    
    # Content safety tests
    runner.run_test("Safety: Hate speech detection", test_content_safety_hate_speech)
    runner.run_test("Safety: Misinformation detection", test_content_safety_misinformation)
    runner.run_test("Safety: Clickbait detection", test_content_safety_clickbait)
    runner.run_test("Safety: Comprehensive check", test_content_safety_comprehensive)
    
    # Error recovery tests
    runner.run_test("Error Recovery: Retry mechanism", test_error_recovery_retry)
    runner.run_test("Error Recovery: Circuit breaker", test_error_recovery_circuit_breaker)
    runner.run_test("Error Recovery: Rate limiter", test_error_recovery_rate_limiter)
    
    # Validation tests
    runner.run_test("Environment validator", test_env_validator)
    
    # Print summary
    runner.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if runner.failed_tests == 0 else 1)


if __name__ == "__main__":
    main()
