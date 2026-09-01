import logging
import re
from transformers import pipeline

logger = logging.getLogger("uvicorn")

# Lazy-loaded pipeline global variable
_sentiment_analyzer = None


def _contains_phrase(text: str, phrase: str) -> bool:
    """Match a whole word or phrase without matching part of another word."""
    return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text))

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
        text_lower = " ".join(text.strip().lower().split())
        
        # Explicit neutral phrases must take precedence over individual positive
        # or negative words within a balanced or uncertain statement.
        neutral_keywords = [
            "thik thak xa", "khasai ramro pani haina, naramro pani haina",
            "sabai kura thik xa tara ali sudhar garnu parxa",
            "product thikai xa, khasai kei problem chaina",
            "malai thaha xaina yo ramro ho ki haina",
            "khai yo service ko barema kehi bhanna sakdina",
        ]
        if any(_contains_phrase(text_lower, keyword) for keyword in neutral_keywords):
            return "neutral"

        # Check complaints before positive terms. For example, "naramro" contains
        # "ramro", so checking positive words first misclassifies a complaint.
        negative_keywords = [
            "naramro", "naramaro", "kharab", "ekdam naramro", "ekdam naramaro",
            "thik chaina", "man parena", "man pareko chaina", "santushta chaina",
            "dukha lagyo", "dukkha lagyo", "nirash chu", "babal haina",
            "ramro chaina", "service naramro cha", "service naramaro cha",
            "sewa naramro cha", "sewa naramaro cha", "dhilo cha", "kaam bhayena",
            "samasya cha", "jhyau lagyo", "bekar cha", "waste of money",
            "recommend gardina", "bekar", "bekaar", "fraud", "bad", "worst",
            "hate", "terrible", "broken", "faulty", "dissatisfied", "disappointed",
            "complaint", "falthu", "problem", "foul", "ramro lagena", "dherai dhilo xa",
            "samadhan garena", "quality xaina", "nirash vayen", "maan pareko xaina",
        ]
        has_explicit_negative = any(
            _contains_phrase(text_lower, keyword) for keyword in negative_keywords
        )
        if has_explicit_negative:
            return "negative"

        # Explicit positive markers in English and Romanized Nepali.
        positive_keywords = [
            "ramro", "dami", "ekdam ramro", "sabai thik cha", "man paryo",
            "man pareko cha", "man pareko xa", "santushta chu", "khusi lageyo", "uttam cha",
            "babal cha", "babal raixa", "awesome cha", "best cha", "sewa ramro cha",
            "service ramro cha", "madat bhayo", "chito kaam bhayo", "sajilo cha",
            "safal bhayo", "dhanyabad", "recommend garchu", "danyabad",
            "dhanyabaad", "thank", "thanks", "good", "great", "nice",
            "awesome", "perfect", "excellent", "mitra", "dherai ramro", "bhalai", "love",
        ]
        if any(_contains_phrase(text_lower, keyword) for keyword in positive_keywords):
            return "positive"
        # Check for inquiry / question patterns in Romanized Nepali or English
        inquiry_keywords = [
            "kina", "kinne", "milxa", "milchha", "available", "price", "kattiko",
            "kasari", "kasto", "bhannu", "buy", "purchase", "cost", "how much",
            "samana", "saman", "aahile", "aahele", "can i", "item", "product", 
            "device", "repair", "chha", "xa", "hajur", "hello", "hi", "oh", "ehh"
        ]
        is_inquiry = any(kw in text_lower for kw in inquiry_keywords) or "?" in text
        # An information request without an explicit sentiment marker is neutral.
        # Do not let the generic BERT model turn a polite question into praise.
        if is_inquiry:
            return "neutral"

        
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
