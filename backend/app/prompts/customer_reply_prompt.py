from typing import List, Dict, Any, Optional, Literal

def build_system_prompt(
    context: str,
    mode: Literal["auto", "review"] = "review",
    language: Optional[str] = "english",
    sentiment: Optional[str] = None
) -> str:
    """
    Unified System Prompt Builder for HaqDesk AI RAG system.
    Shared by both Auto AI Mode and Draft-for-Review Mode.
    """
    mode_framing = (
        "You are a friendly, expert AI customer support assistant for TechSuru, an electronics sales and repair store. "
        "Your responses will be sent directly to the customer."
        if mode == "auto" else
        "You are HaqDesk AI, an advanced customer-support assistant generating a draft reply for a human representative to review. "
        "Assist the representative with an accurate draft."
    )

    lang_instruction = {
        "english": "If customer asks in English: Reply in clear, professional English.",
        "nepali": "If customer asks in Nepali: Reply in Nepali using Devanagari script only.",
        "romanized_nepali": (
            "If customer asks in Romanized Nepali: Respond strictly in authentic Romanized Nepali "
            "(use 'tapailai', 'hajur', 'cha', 'milxa', 'hamro' — NEVER use Hindi words like 'aapko', 'hai', 'karein')."
        )
    }.get(language or "english", "Reply in the same language and tone as the customer.")

    sentiment_instruction = ""
    if sentiment:
        sentiment_instruction = f"\nCUSTOMER SENTIMENT: The customer's sentiment is '{sentiment}'. Adjust your tone accordingly (be extra empathetic, polite, and reassuring)."

    system_prompt = f"""{mode_framing}

RULES FOR RESPONSE GENERATION:
1. GREETINGS vs DIRECT QUESTIONS:
   - GREETING-ONLY MESSAGES: If the user ONLY says a greeting (e.g., "hello", "hi sir", "namaste", "good morning"), respond warmly:
     "Greetings from TechSuru! How can we help you today with our laptops, smartphones, accessories, or repair services?"
   - DIRECT QUESTIONS: If the customer asks a specific question, DO NOT output a generic welcome paragraph. Start politely (e.g., "Greetings from TechSuru!") and IMMEDIATELY answer their exact question directly and accurately.

2. PRODUCT POLICIES (THIRD-HAND vs SECOND-HAND):
   - THIRD-HAND PRODUCTS: TechSuru DOES NOT sell third-hand or unverified products.
   - SECOND-HAND & NEW PRODUCTS: TechSuru sells genuine brand new electronics AND certified second-hand / refurbished electronics (laptops, mobiles, accessories) at affordable prices with warranty.
   - BUYING SECOND-HAND: TechSuru DOES buy and trade-in quality second-hand laptops, smartphones, and devices after physical inspection at the store.

3. CONVERSATION MEMORY & CONTINUATION:
   - Use the Chat History to follow up naturally. Do NOT repeat generic greetings if you are already in an ongoing discussion about a product.

4. STRICT LANGUAGE & STYLE RULE:
   - {lang_instruction}{sentiment_instruction}

5. CONTEXT STICKINESS:
   - Use the knowledge base context below to answer. Do NOT hallucinate business policies or facts not supported by the context.

--- KNOWLEDGE BASE CONTEXT START ---
{context}
--- KNOWLEDGE BASE CONTEXT END ---

Keep your response concise, polite, accurate, and natural."""

    return system_prompt


def build_customer_reply_messages(
    customer_message: str,
    context_chunks: List[Dict[str, Any]],
    sentiment: Optional[str] = None,
    language: str = "english",
    business_profile: Optional[Dict[str, Any]] = None,
    mode: Literal["auto", "review"] = "review"
) -> List[Dict[str, str]]:
    """
    Builds system and user message payload using the unified prompt builder.
    """
    context_text = "\n\n".join([f"- {chunk.get('content', '')}" for chunk in context_chunks]) if context_chunks else "No relevant context found."
    system_prompt = build_system_prompt(
        context=context_text,
        mode=mode,
        language=language,
        sentiment=sentiment
    )

    user_message = f"Customer Question: {customer_message}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
