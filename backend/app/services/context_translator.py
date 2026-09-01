import re
import logging
from typing import Optional
from app.services.llm_gateway import llm_gateway

logger = logging.getLogger("uvicorn")

# Qwen3 and other reasoning models may emit <think>...</think> blocks.
# We strip these before returning any translation to customers.
_THINK_TAG_RE = re.compile(r"<think>.*?(?:</think>|$)", re.DOTALL | re.IGNORECASE)

class ContextTranslator:
    """
    Contextual Translation Service for HaqDesk AI.
    Translates incoming customer queries from Nepali/Romanized Nepali into clear English,
    and translates generated English responses back to high-quality authentic Romanized or Devanagari Nepali.
    """

    @staticmethod
    def _strip_think_tags(text: str) -> str:
        """Remove <think>...</think> reasoning blocks emitted by Qwen3 and similar models."""
        return _THINK_TAG_RE.sub("", text).strip()

    async def analyze_and_translate(self, text: str) -> dict:
        """
        Analyzes the incoming customer query to determine its language/style,
        and translates it into clear, concise English for RAG processing.
        Returns a dict: {"english_translation": "...", "detected_language": "..."}
        """
        if not text or not text.strip():
            return {"english_translation": "", "detected_language": "English"}

        logger.info(f"[Translator] Analyzing and translating incoming query...")

        system_instruction = (
            "You are an expert linguist and translator. Analyze the following customer support query.\n"
            "Identify the language style used by the customer. It could be 'Pure English', 'Romanized Nepali', "
            "'Devanagari Nepali', or 'Mixed English and Romanized Nepali'.\n"
            "Then, translate the query into clear, concise English. If it's already Pure English, just output the exact same text.\n\n"
            "Rules:\n"
            "1. Output ONLY valid JSON, with exactly two keys: 'english_translation' and 'detected_language'.\n"
            "2. Retain exact product names, parameters, and brand names (e.g. 'TechSuru').\n"
            "3. Do not include markdown formatting or reasoning blocks."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Text to analyze and translate:\n{text}"}
        ]

        try:
            import json
            # Use JSON mode if supported by litellm, but here we just rely on prompt engineering
            result = await llm_gateway.complete(messages=messages, max_tokens=1000, temperature=0.1)
            raw_content = self._strip_think_tags(result.get("content", ""))
            
            # Try to extract JSON from markdown if the model wrapped it
            if "```json" in raw_content:
                json_str = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                json_str = raw_content.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_content.strip()

            parsed = json.loads(json_str)
            logger.info(f"[Translator] Original: '{text}' -> Analysis: {parsed}")
            return {
                "english_translation": parsed.get("english_translation", text),
                "detected_language": parsed.get("detected_language", "English")
            }
        except Exception as e:
            logger.error(f"[Translator] Analysis and translation failed: {e}. Falling back to Pure English.")

        # Fallback
        return {"english_translation": text, "detected_language": "Pure English"}

    async def translate_to_target_language(self, text: str, target_lang_style: str) -> str:
        """
        Translates generated English response into the exact style of the customer.
        """
        if not text or not text.strip():
            return ""

        if target_lang_style.lower() in ["pure english", "english"]:
            return text

        logger.info(f"[Translator] Translating generated answer to target_lang_style={target_lang_style}...")

        system_instruction = (
            f"You are an expert customer support agent translator.\n"
            f"Translate the following English customer support reply into exactly this language style: {target_lang_style}.\n\n"
            "STRICT RULES:\n"
            "1. Output ONLY the translated text. Do not add notes, metadata, warnings, or explanations.\n"
            "2. If translating to Romanized Nepali or a mix involving it:\n"
            "   a. Use authentic Romanized Nepali words (e.g., 'tapailai', 'hajur', 'cha', 'milchha', 'hamro').\n"
            "   b. NEVER use Hindi words (do NOT use 'aapko', 'hai', 'karein', 'hoga', 'humara', 'shukriya').\n"
            "3. If it's a mixed language, seamlessly blend English terms (especially product names) with the target language structure.\n"
            "4. Ensure the tone is polite, professional, and helpful."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"English text to translate:\n{text}"}
        ]

        try:
            # Provide enough tokens for the translation
            result = await llm_gateway.complete(messages=messages, max_tokens=2000, temperature=0.2)
            translated = self._strip_think_tags(result.get("content", ""))
            if translated:
                logger.info(f"[Translator] Answer translated successfully to {target_lang_style}")
                return translated
        except Exception as e:
            logger.error(f"[Translator] Translation to {target_lang_style} failed: {e}")

        # Fallback to original text if translation fails
        return text

context_translator = ContextTranslator()
