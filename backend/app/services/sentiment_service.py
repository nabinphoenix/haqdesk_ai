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
    """
    if not text or not text.strip():
        return "neutral"
        
    try:
        analyzer = get_sentiment_analyzer()
        if analyzer is None:
            return "neutral"
            
        result = analyzer(text.strip())[0]
        label = result["label"].lower()
        
        # Ensure we map any model-specific labels to the standard set
        if "pos" in label:
            return "positive"
        elif "neg" in label:
            return "negative"
        else:
            return "neutral"
    except Exception as e:
        logger.error(f"⚠️ Sentiment analysis failed for text: '{text}': {e}")
        return "neutral"
