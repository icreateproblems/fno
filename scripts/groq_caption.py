import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Import key manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from app.api_key_manager import get_groq_key, mark_groq_key_failed
    USE_KEY_ROTATION = True
except ImportError:
    USE_KEY_ROTATION = False
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROK_API_KEY = os.getenv("GROK_API_KEY")  

MODEL = "llama-3.1-8b-instant"  # Changed to stable model that works

# Brand hashtag for reach
BRAND_HASHTAG = "#fastnewsorg"

def generate_fallback_caption(headline: str, category: str, language: str = "en"):
    if language == "nepali":
        base = f"🚨 ताजा खबर: {headline}"
        tags = f"#Breaking #News #Nepal #Update #Trending {BRAND_HASHTAG}"
    else:
        base = f"🚨 BREAKING: {headline}"
        tags = f"#Breaking #News #Update #Trending {BRAND_HASHTAG}"
    if category == "financial":
        tags += " #Markets #Stocks #Economy"
    return {"caption": base, "hashtags": tags, "success": False}

def generate_with_groq(headline: str, description: str = "", language: str = "en"):
    """Generate caption using Groq API"""
    if USE_KEY_ROTATION:
        api_key = get_groq_key()
    else:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return None

    if language == "nepali":
        prompt = (
            "You're a social media editor at a professional news outlet.\n"
            "Write an engaging Instagram caption in Nepali with strategic hashtags.\n\n"
            "Caption: Hook readers immediately, use active voice, be authoritative.\n"
            "Hashtags: Mix trending + niche tags (5-8 tags: broad reach + targeted audience)\n\n"
            "Return ONLY valid JSON: {\"caption\": \"...\", \"hashtags\": \"#Tag1 #Tag2\"}\n\n"
            f"Headline: {headline}\n"
            f"Description: {description}\n"
        )
    elif language == "nepali_to_english":
        prompt = (
            "You're a professional news editor translating for global audience.\n"
            "Translate Nepali news to English with journalistic impact.\n\n"
            "Caption: Professional tone, strong hook, clear facts.\n"
            "Hashtags: Strategic mix - trending + topic-specific (5-8 tags for reach)\n\n"
            "Return ONLY valid JSON: {\"caption\": \"...\", \"hashtags\": \"#Breaking #News\"}\n\n"
            f"Headline (Nepali): {headline}\n"
            f"Description (Nepali): {description}\n"
        )
    else:
        prompt = (
            "You're a senior editor at a major news outlet writing for Instagram.\n\n"
            "Caption: Start with a powerful hook. Use journalistic style - active voice, concrete facts, immediate impact.\n"
            "Hashtags: Strategic selection - combine trending + niche tags. 5-8 tags: broad reach + targeted.\n\n"
            "Example: {\"caption\": \"BREAKING: Major development as...\", \"hashtags\": \"#BreakingNews #Politics #Global\"}\n\n"
            f"Headline: {headline}\n"
            f"Description: {description}\n\n"
            "Return ONLY valid JSON."
        )

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 200,
            },
            timeout=15,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()

        # Remove markdown code blocks if present
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1].replace("json", "").replace("JSON", "").strip()

        # Extract JSON object
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            data = json.loads(json_str)
            caption = data.get("caption", "").strip().replace("\"", "")
            hashtags = data.get("hashtags", "#Breaking #News").strip()
            
            return {"caption": caption[:300], "hashtags": hashtags}
        
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in (429, 401):
            if USE_KEY_ROTATION:
                mark_groq_key_failed(api_key)
        print(f"Groq error: {e}")
        return None
    except Exception as e:
        print(f"Groq error: {e}")
        return None

def generate_with_grok(headline: str, description: str = ""):
    """Generate caption using Grok API (xAI) - Optional fallback"""
    if not GROK_API_KEY:
        return None

    prompt = (
        "Write a short, punchy Instagram caption for breaking news. JSON format with 'caption' and 'hashtags'.\n"
        f"Headline: {headline}\n"
        f"Description: {description}\n"
    )

    try:
        # Note: Grok API endpoint may vary - update if needed
        r = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-2",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "max_tokens": 200,
            },
            timeout=15,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()

        # Extract JSON
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            data = json.loads(json_str)
            caption = data.get("caption", "").strip().replace("\"", "")
            hashtags = data.get("hashtags", "#Breaking #News").strip()
            
            return {"caption": caption[:300], "hashtags": hashtags}
        
        return None
    except Exception as e:
        print(f"Grok error: {e}")
        return None


def rephrase_description_with_groq(headline: str, description: str, language: str = "en", for_image: bool = False):
    """
    Rephrase the description to add context and avoid copyright issues.
    Makes the content more informative and readable.
    for_image: If True, generates a very concise 2-sentence summary for the image
    """
    if USE_KEY_ROTATION:
        api_key = get_groq_key()
    else:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key or not description:
        return description

    if for_image:
        # For image - professional, attention-grabbing summary
        if language == "nepali":
            prompt = (
                "You're a professional journalist. Write 1-2 powerful sentences in Nepali that capture the essence of this breaking news.\n"
                "START with a strong hook - the most compelling fact or angle.\n"
                "Use journalistic style: active voice, concrete details, immediate relevance.\n"
                "Each sentence MUST end with proper punctuation.\n\n"
                f"Headline: {headline}\n"
                f"Details: {description}\n\n"
                "Make it compelling and professional. Return ONLY the text."
            )
        elif language == "nepali_to_english":
            prompt = (
                "You're a professional news editor. Translate this Nepali news to English with impact.\n"
                "START with the most newsworthy angle - what makes this matter?\n"
                "Use journalistic writing: who, what, when, where - in 1-2 sharp sentences.\n"
                "Make readers want to know more.\n\n"
                f"Headline: {headline}\n"
                f"Details: {description}\n\n"
                "Return ONLY the powerful English text."
            )
        else:
            prompt = (
                "You're a senior journalist at a major news outlet. Write 1-2 compelling sentences.\n"
                "HOOK: Start with the most dramatic or important element - grab attention immediately.\n"
                "Style: Professional journalism - active voice, specific facts, clear impact.\n"
                "Think: 'Why should readers care RIGHT NOW?'\n\n"
                f"Headline: {headline}\n"
                f"Details: {description}\n\n"
                "Return ONLY the text - no fluff, pure news value."
            )
    else:
        # For caption - professional journalism with narrative flow
        if language == "nepali":
            prompt = (
                "You're a professional journalist writing for Instagram. Explain this news in Nepali with journalistic excellence.\n\n"
                "STRUCTURE:\n"
                "1. HOOK - Start with the most compelling fact or consequence\n"
                "2. CONTEXT - Explain who, what, when, where with specific details\n"
                "3. SIGNIFICANCE - Why this matters to readers right now\n"
                "4. [Optional] IMPACT - What happens next or broader implications\n\n"
                "Style: Professional but accessible, active voice, concrete facts.\n"
                "Length: Adapt to story importance (2-4 sentences).\n\n"
                f"Headline: {headline}\n"
                f"Details: {description}\n\n"
                "Write with journalistic authority. Return ONLY the text."
            )
        elif language == "nepali_to_english":
            prompt = (
                "You're a news editor translating Nepali news to English with professional journalism standards.\n\n"
                "STRUCTURE:\n"
                "1. Lead with the most newsworthy angle - hook readers immediately\n"
                "2. Provide key facts: who, what, when, where, why\n"
                "3. Explain significance and impact\n"
                "4. Add context or consequences if relevant\n\n"
                "Style: Sharp, professional journalism. Active voice. Specific details.\n"
                "Make it authoritative yet engaging.\n\n"
                f"Headline: {headline}\n"
                f"Details: {description}\n\n"
                "Return ONLY the English text."
            )
        else:
            prompt = (
                "You're a senior journalist at a prestigious news outlet. Write this story for Instagram with professional excellence.\n\n"
                "STORYTELLING FORMULA:\n"
                "1. HOOK - Open with the most dramatic/important element (lead)\n"
                "2. CORE FACTS - Who, what, when, where with concrete details\n"
                "3. SO WHAT - Why readers should care, immediate significance\n"
                "4. IMPACT/CONTEXT - Broader implications or what's next\n\n"
                "Journalistic principles:\n"
                "- Active voice, strong verbs\n"
                "- Specific facts over vague statements\n"
                "- Show impact on real people/situations\n"
                "- Professional, authoritative tone\n"
                "- Proper attribution if needed\n\n"
                f"Headline: {headline}\n"
                f"Details: {description}\n\n"
                "Write with authority and narrative flow. Return ONLY the story text."
            )

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6,
                "max_tokens": 300,
            },
            timeout=15,
        )
        r.raise_for_status()
        rephrased = r.json()["choices"][0]["message"]["content"].strip()
        return rephrased
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in (429, 401):
            if USE_KEY_ROTATION:
                mark_groq_key_failed(api_key)
        print(f"Rephrase error: {e}")
        return description
    except Exception as e:
        print(f"Rephrase error: {e}")
        return description


def translate_nepali_to_english(text: str) -> str:
    """
    Translate Nepali text to English. Returns input on failure.
    """
    if USE_KEY_ROTATION:
        api_key = get_groq_key()
    else:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key or not text:
        return text

    prompt = (
        "Translate the following Nepali text to natural, clear English. "
        "Return ONLY the translation text.\n\n"
        f"Nepali: {text}"
    )

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 200,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in (429, 401):
            if USE_KEY_ROTATION:
                mark_groq_key_failed(api_key)
        print(f"Translate error: {e}")
        return text
    except Exception as e:
        print(f"Translate error: {e}")
        return text


def generate_caption(headline: str, description: str = "", category: str = "general", language: str = "en"):
    """
    Generate caption with multi-AI fallback strategy.
    Tries: Groq → Grok → Fallback
    """
    
    # Try Groq first (primary)
    result = generate_with_groq(headline, description, language=language)
    if result:
        print("✓ Caption generated with Groq")
        hashtags = result.get("hashtags", "") + f" {BRAND_HASHTAG}"
        return {"caption": result["caption"], "hashtags": hashtags.strip(), "success": True}
    
    # Try Grok if Groq fails (secondary)
    result = generate_with_grok(headline, description)
    if result:
        print("✓ Caption generated with Grok")
        hashtags = result.get("hashtags", "") + f" {BRAND_HASHTAG}"
        return {"caption": result["caption"], "hashtags": hashtags.strip(), "success": True}
    
    # Fallback to template
    print("✓ Using fallback caption template")
    fallback = generate_fallback_caption(headline, category, language=language)
    fallback["hashtags"] += f" {BRAND_HASHTAG}"
    return fallback

if __name__ == "__main__":
    print(generate_caption("Example headline", "Example description", "general"))