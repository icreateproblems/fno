from app.logger import get_logger
logger = get_logger(__name__)
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

MODEL = "llama-3.3-70b-versatile"  # Upgraded to 70B model for higher quality

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
    """Generate caption using Groq API with improved prompting"""
    if USE_KEY_ROTATION:
        api_key = get_groq_key()
    else:
        api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    MODEL = "llama-3.3-70b-versatile"

    if language == "nepali":
        prompt = """You are a senior news editor at Kantipur Publications (Nepal's most respected newspaper).

Your task: Create a compelling Instagram post in Nepali that sounds NATURAL and PROFESSIONAL - not AI-generated.

CRITICAL RULES:
1. Write like a human journalist - conversational yet authoritative
2. NO clichés like "यो घटना..." or "यस सन्दर्भमा..."
3. Lead with the MOST compelling fact (who/what/why it matters)
4. Use active voice and concrete details
5. Keep it concise but informative (2-4 sentences max)
6. End with context or significance, NOT with a cliffhanger

VERIFY: Does this sound like something a real journalist would write? If it sounds generic or AI-like, rewrite it.

Headline: {headline}
Details: {description}

Return ONLY valid JSON:
{{
  "caption": "Natural Nepali text that sounds human-written",
  "hashtags": "#Breaking #News #Nepal [2-3 more relevant tags]"
}}

Example of GOOD writing:
"सिंहदरबारमा नयाँ संसद भवनको निर्माण ८८% सम्पन्न भएको छ। तर यो परियोजना कहिले सम्पन्न हुन्छ भन्ने स्पष्ट छैन। सरकारी स्रोतका अनुसार, बजेट अभाव र प्राविधिक समस्याले समयमै पूरा हुने सम्भावना कम छ।"

Example of BAD (AI-like) writing:
"यो घटनाले राजनीतिक परिदृश्यमा महत्त्वपूर्ण प्रभाव पार्नेछ। यस सन्दर्भमा विशेषज्ञहरूले विभिन्न मत राखेका छन्..."
"""
    elif language == "nepali_to_english":
        prompt = """You are a professional news translator and editor for an international audience.

Your task: Translate this Nepali news into COMPELLING English that sounds natural and authoritative.

CRITICAL RULES:
1. Write like BBC News or Reuters - professional but engaging
2. Lead with the HOOK - the most newsworthy angle
3. Include specific facts: WHO did WHAT, WHEN, WHERE, WHY
4. Explain significance - why should global readers care?
5. NO generic phrases like "In a recent development" or "According to sources"
6. Use concrete language: "surged 12%" not "increased significantly"

VERIFY: Does this read like professional international journalism? If it sounds AI-generated, rewrite it.

Headline (Nepali): {headline}
Details (Nepali): {description}

Return ONLY valid JSON:
{{
  "caption": "Sharp, professional English news summary",
  "hashtags": "#Breaking #Nepal #GlobalNews [2-3 relevant tags]"
}}

Example of GOOD translation:
"Nepal's new Parliament building in Singha Durbar has reached 88% completion, but officials cannot confirm a finish date. Budget shortfalls and technical delays now threaten the project timeline, government sources confirm."

Example of BAD (AI-like) translation:
"In a recent development, the construction of the new parliament building has shown significant progress. This is expected to have implications for the political landscape of the country."
"""
    else:
        prompt = """You are a senior editor at The Guardian or BBC News writing for Instagram.

Your task: Create a powerful news post that stops scrolling and commands attention.

CRITICAL RULES:
1. Hook readers IMMEDIATELY - lead with the drama/significance
2. Use specific facts and concrete details (numbers, names, impact)
3. Write with authority but energy - like you're telling a friend important news
4. NO clichés: "game-changer," "unprecedented," "shocking," etc. unless absolutely true
5. Show, don't tell - "protests blocked 3 highways" not "large protests occurred"
6. Include human impact when relevant

VERIFY: Would a professional journalist at NYT or BBC write this? If it sounds generic or clickbait-y, rewrite it.

Headline: {headline}
Details: {description}

Return ONLY valid JSON:
{{
  "caption": "Compelling, journalistic Instagram caption",
  "hashtags": "#Breaking #News #Politics [2-3 specific tags]"
}}

Example of GOOD writing:
"Bitcoin crossed $100,000 for the first time today as institutional investors poured $2.3B into crypto funds this week. The surge comes despite regulatory warnings from the SEC, marking a dramatic shift in Wall Street's crypto stance."

Example of BAD (AI-like) writing:
"In a groundbreaking development, Bitcoin has achieved unprecedented heights, signaling a potential game-changer for the cryptocurrency market. Experts believe this could reshape the financial landscape."
"""

    prompt = prompt.format(headline=headline, description=description)

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,  # Now using 70B model
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,  # Slightly higher for more natural variation
                "max_tokens": 300,
            },
            timeout=30,  # Increased timeout for larger model
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
            caption = data.get("caption", "").strip().replace('"', "")
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
    Rephrase content with journalistic excellence.
    for_image: If True, generates concise 2-sentence summary for visual display
    """
    if USE_KEY_ROTATION:
        api_key = get_groq_key()
    else:
        api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not description:
        return description

    MODEL = "llama-3.3-70b-versatile"

    if for_image:
        # For image - attention-grabbing summary that works visually
        if language == "nepali":
            prompt = """आफूलाई Kantipur का वरिष्ठ सम्पादक मान्नुहोस्। Instagram को लागि छवि पाठ तयार गर्नुहोस्।

आवश्यकताहरू:
1. केवल 2 वाक्य - छोटो, शक्तिशाली, स्पष्ट
2. सबैभन्दा महत्त्वपूर्ण तथ्यबाट सुरु गर्नुहोस्
3. ठोस विवरणहरू प्रयोग गर्नुहोस् (संख्या, नाम, प्रभाव)
4. सक्रिय स्वरमा लेख्नुहोस्
5. कुनै सामान्य वाक्यांश प्रयोग नगर्नुहोस्

शीर्षक: {headline}
विवरण: {description}

उदाहरण (राम्रो):
"Planning Boys United ले Laliguras FC लाई २-१ ले हराएर Buda Subba Gold Cup को फाइनलमा प्रवेश गरेको छ। यो जितले टिमलाई पहिलो पटक यो प्रतिष्ठित प्रतियोगिताको उपाधि जित्ने अवसर दिएको छ।"

केवल पाठ फर्काउनुहोस् (कुनै JSON होइन)।
"""
        elif language == "nepali_to_english":
            prompt = """You are translating Nepali news for a global Instagram audience.

Requirements:
1. Exactly 2 sentences - sharp, clear, impactful
2. Lead with the most newsworthy fact
3. Include specifics: numbers, names, outcomes
4. Use active voice throughout
5. Professional journalism standards (BBC/Reuters quality)

Headline: {headline}
Details: {description}

Example (GOOD):
"Planning Boys United secured their spot in the Buda Subba Gold Cup final after defeating Laliguras FC 2-1 in Dhankuta. This victory marks the team's first-ever chance to claim the prestigious regional tournament title."

Example (BAD - too generic):
"In a thrilling turn of events, Planning Boys United has advanced to the finals. The match was highly competitive with both teams showing excellent performance."

Return ONLY the text (no JSON).
"""
        else:
            prompt = """You are a BBC News editor writing image text for Instagram.

Requirements:
1. Exactly 2 sentences - powerful, visual, memorable
2. Open with the HOOK - why does this matter RIGHT NOW?
3. Use concrete details: "surged 12%" not "increased significantly"
4. Active voice only
5. Professional tone but conversational energy

Headline: {headline}
Details: {description}

Example (GOOD):
"The new Parliament building in Nepal's Singha Durbar complex has reached 88% completion, but lacks a confirmed finish date. Budget constraints and technical delays now threaten the ambitious reconstruction project."

Example (BAD - too vague):
"A major facelift is underway at Singha Durbar. The new parliament building is taking shape with significant progress being made."

Return ONLY the text (no JSON).
"""
    else:
        # For caption - fuller journalistic treatment
        # [Similar upgrade for caption version - see full implementation below]
        if language == "nepali":
            prompt = """तपाईं Kantipur का वरिष्ठ पत्रकार हुनुहुन्छ। Instagram को लागि समाचारको व्याख्या गर्नुहोस्।

आवश्यकताहरू:
1. सबैभन्दा महत्त्वपूर्ण तथ्यबाट सुरु गर्नुहोस्
2. 2-4 वाक्य, स्पष्ट र सशक्त
3. ठोस विवरणहरू, नाम, संख्या, स्थान प्रयोग गर्नुहोस्
4. निष्कर्षमा सन्दर्भ वा महत्त्व दिनुहोस्
5. कुनै सामान्य वाक्यांश प्रयोग नगर्नुहोस्

शीर्षक: {headline}
विवरण: {description}

केवल पाठ फर्काउनुहोस् (कुनै JSON होइन)।
"""
        elif language == "nepali_to_english":
            prompt = """You are a senior news translator. Translate this Nepali news for Instagram with professional journalism standards.

Requirements:
1. Lead with the most newsworthy angle
2. 2-4 sentences, sharp and clear
3. Include key facts: who, what, when, where, why
4. Explain significance and impact
5. No generic phrases or AI-like language

Headline: {headline}
Details: {description}

Return ONLY the English text.
"""
        else:
            prompt = """You are a senior journalist at The Guardian. Write this story for Instagram with professional excellence.

STORYTELLING FORMULA:
1. HOOK - Open with the most dramatic/important element
2. CORE FACTS - Who, what, when, where with concrete details
3. SO WHAT - Why readers should care, immediate significance
4. IMPACT/CONTEXT - Broader implications or what's next

Journalistic principles:
- Active voice, strong verbs
- Specific facts over vague statements
- Show impact on real people/situations
- Professional, authoritative tone

Headline: {headline}
Details: {description}

Return ONLY the story text.
"""

    prompt = prompt.format(headline=headline, description=description)

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
            timeout=30,
        )
        r.raise_for_status()
        rephrased = r.json()["choices"][0]["message"]["content"].strip()
        # Verify quality - if it's too short or generic, use original
        if len(rephrased) < 50 or "in a recent development" in rephrased.lower():
            # logger.warning("AI output too generic, using original")
            return description
        return rephrased
    except Exception as e:
        # logger.error(f"Rephrase error: {e}")
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