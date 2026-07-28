import logging
from transformers import pipeline

logger = logging.getLogger("uvicorn")

# Lazy-loaded pipeline global variable
_sentiment_analyzer = None

def get_sentiment_analyzer():
    """Lazy-load the multilingual sentiment analysis pipeline."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        logger.info("🧠 Loading Hugging Face sentiment model (lxyuan/distilbert-base-multilingual-cased-sentiments-student)...")
        # This is a small (~270MB) cased student model that classifies English, Nepali, Hindi, Spanish, etc.
        # It outputs label predictions: 'positive', 'neutral', or 'negative'
        try:
            _sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="lxyuan/distilbert-base-multilingual-cased-sentiments-student"
            )
            logger.info("✅ Sentiment analyzer loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load Hugging Face sentiment pipeline: {e}")
            raise e
    return _sentiment_analyzer

def detect_sentiment(text: str) -> str:
    """
    Detect the sentiment of the text.
    Returns: 'positive', 'neutral', or 'negative'.
    Handles Romanized Nepali and English inquiries safely.
    """
    if not text or not text.strip():
        return "neutral"
        
    try:
        text_lower = text.strip().lower()
        
        # Check for explicit positive markers in English & Romanized Nepali
        positive_keywords = [
            "ramro", "dhanyabad", "danyabad", "dhanyabaad", "thank", "thanks", 
            "good", "great", "nice", "awesome", "perfect", "excellent", "mitra",
            "ekdam ramro", "dherai ramro", "bhalai", "love"
        ]
        if any(kw in text_lower for kw in positive_keywords):
            return "positive"

        # Explicit negative complaint terms
        negative_keywords = [
            "bekar", "bekaar", "naramro", "fraud", "bad", "worst", "hate", 
            "terrible", "broken", "faulty", "dissatisfied", "disappointed", 
            "complaint", "falthu", "kharab", "dukkha", "problem", "foul"
        ]
        has_explicit_negative = any(kw in text_lower for kw in negative_keywords)

        # Check for inquiry / question patterns in Romanized Nepali or English
        inquiry_keywords = [
            "kina", "kinne", "milxa", "milchha", "available", "price", "kattiko",
            "kasari", "kasto", "bhannu", "buy", "purchase", "cost", "how much",
            "samana", "saman", "aahile", "aahele", "can i", "item", "product", 
            "device", "repair", "chha", "xa", "hajur", "hello", "hi", "oh", "ehh"
        ]
        is_inquiry = any(kw in text_lower for kw in inquiry_keywords) or "?" in text
        
        analyzer = get_sentiment_analyzer()
        if analyzer is None:
            return "neutral"
            
        result = analyzer(text.strip())[0]
        label = result["label"].lower()
        
        # Map model outputs
        if "pos" in label:
            return "positive"
        elif "neg" in label:
            # If the text is a product/purchase inquiry or contains no explicit negative words, classify as neutral/positive
            if is_inquiry and not has_explicit_negative:
                return "positive" if "buy" in text_lower or "kinne" in text_lower or "milxa" in text_lower else "neutral"
            if not has_explicit_negative:
                return "neutral"
            return "negative"
        else:
            return "neutral"
    except Exception as e:
        logger.error(f"⚠️ Sentiment analysis failed for text: '{text}': {e}")
        return "neutral"
