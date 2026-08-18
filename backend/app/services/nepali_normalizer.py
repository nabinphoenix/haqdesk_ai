"""
Nepali Normalizer Utility
Normalizes Romanized Nepali text into Devanagari script for improved cross-lingual RAG retrieval.
"""

import re
from typing import Dict

# Dictionary mapping Romanized Nepali terms to Devanagari script
ROMANIZED_NEPALI_MAP: Dict[str, str] = {
    # Pronouns & Greetings
    "hajur": "हजुर",
    "tapai": "तपाई",
    "tapailai": "तपाईलाई",
    "malai": "मलाई",
    "hijo": "हिजो",
    "aaja": "आज",
    "aahele": "अहिले",
    "aahile": "अहिले",
    "maile": "मैले",
    "yo": "यो",
    "tyo": "त्यो",
    "hamro": "हाम्रो",
    "sanchai": "सन्चै",
    "sanchhai": "सन्चै",
    "namaste": "नमस्ते",

    # Verbs & Auxiliaries
    "cha": "छ",
    "chha": "छ",
    "xa": "छ",
    "xaina": "छैन",
    "chaina": "छैन",
    "huncha": "हुन्छ",
    "hunchha": "हुन्छ",
    "hudaina": "हुदैन",
    "hoina": "होइन",
    "ho": "हो",
    "milcha": "मिल्छ",
    "milchha": "मिल्छ",
    "milxa": "मिल्छ",
    "paunchha": "पाउँछ",
    "pauxa": "पाउँछ",
    "paucha": "पाउँछ",
    "garne": "गर्ने",
    "garna": "गर्न",
    "garnu": "गर्नु",
    "bhayo": "भयो",
    "bhaneko": "भनेको",
    "bhanda": "भन्दा",
    "hunuhuncha": "हुनुहुन्छ",
    "hunuhunchha": "हुनुहुन्छ",

    # Interrogatives & General Vocabulary
    "kina": "किन",
    "kinne": "किन्ने",
    "kasari": "कसरी",
    "kasto": "कस्तो",
    "kattiko": "कत्तिको",
    "k": "के",
    "ke": "के",
    "khoji": "खोजी",
    "parne": "पर्ने",
    "ramro": "राम्रो",
    "dherai": "धेरै",
    "dhanyabad": "धन्यवाद",
    "danyabad": "धन्यवाद",

    # Commerce, Support & Product Terms
    "saman": "सामान",
    "samana": "सामान",
    "firta": "फिर्ता",
    "stock": "स्टक",
    "price": "मूल्य",
    "moolya": "मूल्य",
    "daam": "दाम",
    "laptop": "ल्यापटप",
    "mobile": "मोबाइल",
    "device": "उपकरण",
    "repair": "मर्मत",
    "service": "सेवा",
    "warranty": "वारेन्टी",
    "return": "फिर्ता",
    "policy": "नीति",
}


def normalize_nepali_text(text: str) -> str:
    """
    Normalizes Romanized Nepali words in `text` to Devanagari script using dictionary lookup.
    Returns the space-separated Devanagari tokens found.
    
    Example:
        normalize_nepali_text("hajur sanchai hunuhuncha?") -> "हजुर सन्चै हुनुहुन्छ"
    """
    if not text or not text.strip():
        return ""

    tokens = re.findall(r'\b\w+\b', text.lower())
    devanagari_tokens = []

    for token in tokens:
        if token in ROMANIZED_NEPALI_MAP:
            devanagari_tokens.append(ROMANIZED_NEPALI_MAP[token])

    return " ".join(devanagari_tokens)


def get_embedding_input(text: str) -> str:
    """
    Builds dual-language embedding input string for the multilingual embedding model.
    Preserves original text and appends normalized Devanagari text.
    
    Example:
        get_embedding_input("hajur sanchai hunuhuncha?")
        -> "hajur sanchai hunuhuncha? हजुर सन्चै हुनुहुन्छ"
    """
    if not text or not text.strip():
        return ""

    devanagari_part = normalize_nepali_text(text)
    if devanagari_part:
        return f"{text.strip()} {devanagari_part}"
    return text.strip()
