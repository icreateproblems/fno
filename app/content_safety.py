"""
Content safety and moderation checks.
Prevents posting of harmful, hateful, or misleading content.
"""

import re
from typing import Dict, List, Tuple
from app.logger import get_logger

logger = get_logger(__name__)


class ContentSafety:
    """Content moderation and safety checks."""
    
    # Hate speech and harmful content indicators
    HATE_KEYWORDS = [
        # Racial slurs and discrimination
        r'\bn[i1]gg[e3a]r\b', r'\bk[i1]ke\b', r'\bch[i1]nk\b', r'\bsp[i1]c\b',
        # Religious hate
        r'\bterror[i1]st muslim\b', r'\bmusl[i1]m scum\b', r'\bj[e3]w[s5] control\b',
        # Gender-based hate
        r'\bf[e3]m[i1]nazi\b', r'\bwh[o0]r[e3]\b', r'\bsl[u0]t\b',
        # LGBTQ+ slurs
        r'\bf[a4]gg[o0]t\b', r'\btr[a4]nn[y1]\b', r'\bd[y1]ke\b',
        # Violence promotion
        r'\bk[i1]ll all\b', r'\bexterminate\b', r'\bgenocide\b', r'\bmass murder\b',
    ]
    
    # Misinformation indicators
    MISINFO_PATTERNS = [
        r'5g causes cancer',
        r'covid is fake',
        r'vaccines cause autism',
        r'flat earth',
        r'chemtrails',
        r'qanon',
        r'deep state controls',
        r'crisis actors',
        r'bill gates microchip',
        r'election was stolen \(2020\)',  # Specific false claim
        r'ivermectin cures covid',
        r'drinking bleach',
    ]
    
    # Clickbait and sensationalism
    CLICKBAIT_PATTERNS = [
        r'you won\'t believe',
        r'doctors hate',
        r'one weird trick',
        r'shocking secret',
        r'they don\'t want you to know',
        r'number \d+ will shock you',
        r'what happened next will',
        r'the truth they\'re hiding',
    ]
    
    # Spam indicators
    SPAM_PATTERNS = [
        r'buy now',
        r'click here',
        r'limited time offer',
        r'act now',
        r'earn \$\d+ from home',
        r'lose \d+ pounds',
        r'free money',
        r'get rich quick',
    ]
    
    # Explicit content
    EXPLICIT_KEYWORDS = [
        r'\bporn\b', r'\bxxx\b', r'\bsex tape\b',
        r'\bnaked\b', r'\bnude\b', r'\berotic\b',
    ]
    
    # Unverified sources (known for fake news)
    UNRELIABLE_SOURCES = [
        'infowars', 'naturalnews', 'beforeitsnews', 'yournewswire',
        'truepundit', 'thegatewaypundit', 'zerohedge',
    ]
    
    def __init__(self):
        self.compiled_hate = [re.compile(pattern, re.IGNORECASE) for pattern in self.HATE_KEYWORDS]
        self.compiled_misinfo = [re.compile(pattern, re.IGNORECASE) for pattern in self.MISINFO_PATTERNS]
        self.compiled_clickbait = [re.compile(pattern, re.IGNORECASE) for pattern in self.CLICKBAIT_PATTERNS]
        self.compiled_spam = [re.compile(pattern, re.IGNORECASE) for pattern in self.SPAM_PATTERNS]
        self.compiled_explicit = [re.compile(pattern, re.IGNORECASE) for pattern in self.EXPLICIT_KEYWORDS]
    
    def check_hate_speech(self, text: str) -> Tuple[bool, List[str]]:
        """Check for hate speech indicators."""
        violations = []
        
        for pattern in self.compiled_hate:
            if pattern.search(text):
                violations.append(f"Hate speech pattern: {pattern.pattern}")
        
        return len(violations) > 0, violations
    
    def check_misinformation(self, text: str) -> Tuple[bool, List[str]]:
        """Check for known misinformation patterns."""
        violations = []
        
        for pattern in self.compiled_misinfo:
            if pattern.search(text):
                violations.append(f"Misinformation pattern: {pattern.pattern}")
        
        return len(violations) > 0, violations
    
    def check_clickbait(self, text: str) -> Tuple[bool, float]:
        """Check for clickbait indicators. Returns (is_clickbait, severity 0-1)."""
        matches = 0
        
        for pattern in self.compiled_clickbait:
            if pattern.search(text):
                matches += 1
        
        severity = min(matches / 2, 1.0)  # 2+ patterns = max severity
        return severity > 0.3, severity
    
    def check_spam(self, text: str) -> Tuple[bool, List[str]]:
        """Check for spam indicators."""
        violations = []
        
        for pattern in self.compiled_spam:
            if pattern.search(text):
                violations.append(f"Spam pattern: {pattern.pattern}")
        
        return len(violations) > 0, violations
    
    def check_explicit_content(self, text: str) -> Tuple[bool, List[str]]:
        """Check for explicit content."""
        violations = []
        
        for pattern in self.compiled_explicit:
            if pattern.search(text):
                violations.append(f"Explicit content: {pattern.pattern}")
        
        return len(violations) > 0, violations
    
    def check_source_reliability(self, source: str) -> Tuple[bool, str]:
        """Check if source is known for unreliability."""
        source_lower = source.lower()
        
        for unreliable in self.UNRELIABLE_SOURCES:
            if unreliable in source_lower:
                return True, f"Unreliable source: {unreliable}"
        
        return False, ""
    
    def check_caps_spam(self, text: str) -> Tuple[bool, float]:
        """Check for excessive capitalization (spam indicator)."""
        if len(text) < 10:
            return False, 0.0
        
        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = caps_count / len(text)
        
        # More than 50% caps is suspicious
        return caps_ratio > 0.5, caps_ratio
    
    def check_excessive_punctuation(self, text: str) -> Tuple[bool, int]:
        """Check for excessive punctuation (sensationalism indicator)."""
        exclamation = text.count('!')
        question = text.count('?')
        
        total = exclamation + question
        
        # More than 3 exclamation/question marks is suspicious
        return total > 3, total
    
    def comprehensive_check(self, headline: str, description: str = "", source: str = "") -> Dict:
        """
        Run all safety checks on content.
        
        Returns dict with:
            - safe: bool (overall safety)
            - violations: list of violation descriptions
            - warnings: list of warning descriptions
            - severity: 0-1 (0=safe, 1=dangerous)
        """
        text = f"{headline} {description}".lower()
        violations = []
        warnings = []
        severity_scores = []
        
        # Critical checks (auto-reject)
        has_hate, hate_violations = self.check_hate_speech(text)
        if has_hate:
            violations.extend(hate_violations)
            severity_scores.append(1.0)
        
        has_misinfo, misinfo_violations = self.check_misinformation(text)
        if has_misinfo:
            violations.extend(misinfo_violations)
            severity_scores.append(0.9)
        
        has_explicit, explicit_violations = self.check_explicit_content(text)
        if has_explicit:
            violations.extend(explicit_violations)
            severity_scores.append(0.8)
        
        has_spam, spam_violations = self.check_spam(text)
        if has_spam:
            violations.extend(spam_violations)
            severity_scores.append(0.7)
        
        # Source reliability
        is_unreliable, source_msg = self.check_source_reliability(source)
        if is_unreliable:
            warnings.append(source_msg)
            severity_scores.append(0.6)
        
        # Warning-level checks (reduce score but don't auto-reject)
        is_clickbait, clickbait_severity = self.check_clickbait(headline)
        if is_clickbait:
            warnings.append(f"Clickbait detected (severity: {clickbait_severity:.2f})")
            severity_scores.append(clickbait_severity * 0.5)
        
        has_caps_spam, caps_ratio = self.check_caps_spam(headline)
        if has_caps_spam:
            warnings.append(f"Excessive caps ({caps_ratio:.1%})")
            severity_scores.append(caps_ratio * 0.4)
        
        has_excess_punct, punct_count = self.check_excessive_punctuation(headline)
        if has_excess_punct:
            warnings.append(f"Excessive punctuation ({punct_count} marks)")
            severity_scores.append(0.3)
        
        # Calculate overall severity
        overall_severity = max(severity_scores) if severity_scores else 0.0
        
        # Safe if no critical violations
        is_safe = len(violations) == 0
        
        return {
            "safe": is_safe,
            "violations": violations,
            "warnings": warnings,
            "severity": overall_severity,
            "should_post": is_safe and overall_severity < 0.7
        }
    
    def get_safety_score(self, headline: str, description: str = "", source: str = "") -> Tuple[int, str]:
        """
        Get safety score 0-100 (100 = safest).
        
        Returns:
            score: 0-100
            reason: explanation of score
        """
        result = self.comprehensive_check(headline, description, source)
        
        if not result["safe"]:
            return 0, f"Critical violations: {', '.join(result['violations'][:2])}"
        
        # Start at 100, deduct for warnings
        score = 100
        deductions = []
        
        if result["warnings"]:
            warning_penalty = min(len(result["warnings"]) * 15, 40)
            score -= warning_penalty
            deductions.append(f"-{warning_penalty} (warnings)")
        
        if result["severity"] > 0:
            severity_penalty = int(result["severity"] * 30)
            score -= severity_penalty
            deductions.append(f"-{severity_penalty} (severity)")
        
        score = max(0, score)
        
        if deductions:
            reason = f"Safety score: {score}/100 ({', '.join(deductions)})"
        else:
            reason = "Content passed all safety checks"
        
        return score, reason


# Global instance
content_safety = ContentSafety()


def is_safe_to_post(headline: str, description: str = "", source: str = "") -> Tuple[bool, int, str]:
    """
    Quick safety check for posting content.
    
    Returns:
        should_post: bool
        safety_score: 0-100
        reason: explanation
    """
    result = content_safety.comprehensive_check(headline, description, source)
    safety_score, reason = content_safety.get_safety_score(headline, description, source)
    
    should_post = result["should_post"] and safety_score >= 60
    
    if not should_post:
        if result["violations"]:
            reason = f"BLOCKED: {result['violations'][0]}"
        elif result["warnings"]:
            reason = f"Low safety score: {result['warnings'][0]}"
    
    return should_post, safety_score, reason
