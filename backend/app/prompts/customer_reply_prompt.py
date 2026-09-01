from typing import List, Dict, Any, Optional, Literal

def build_system_prompt(
    context: str,
    mode: Literal["auto", "review"] = "review",
    language: Optional[str] = "english",
    sentiment: Optional[str] = None,
    platform: Optional[str] = None,
    customer_name: Optional[str] = None,
    business_name: str = "the business",
) -> str:
    """
    Unified System Prompt Builder for HaqDesk AI RAG system.
    Shared by both Auto AI Mode and Draft-for-Review Mode.
    """
    mode_framing = (
        f"You are a friendly, expert AI customer support assistant for {business_name}. "
        "Your responses will be sent directly to the customer."
        if mode == "auto" else
        "You are HaqDesk AI, an advanced customer-support assistant generating a draft reply for a human representative to review. "
        "Assist the representative with an accurate draft."
    )
    is_techsuru = business_name.lower().replace(" ", "") == "techsuru"
    product_policy_instruction = (
        """
2. TECHSURU PRODUCT POLICIES:
   - TechSuru does not sell third-hand or unverified products.
   - TechSuru sells genuine new and certified second-hand/refurbished electronics.
   - TechSuru buys or trades in quality second-hand devices after physical inspection."""
        if is_techsuru else
        """
2. BUSINESS-SPECIFIC POLICIES:
   - Do not assume what this business sells or what its policies are.
   - Use only the supplied knowledge-base context. If the context does not answer the question, say that the information needs confirmation from the support team."""
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

    if customer_name:
        greeting_instruction = f"""
6. PERSONALIZED GREETING AND SIGNATURE:
   - The customer's display name is: {customer_name}
   - Use ONLY the first name from that display name.
   - Infer a title from the name alone—never from message content, writing style, tone, or any other signal.
   - Use "Hello [First Name] Sir," or "Hello [First Name] Ma'am," only when the name has a very clear, high-confidence gender association.
   - Common, unmistakable associations qualify as high confidence (for example, Michael → Sir and Priyanka → Ma'am).
   - For any meaningful ambiguity—including unisex names, initials, unfamiliar names, or low confidence—use exactly "Hello [First Name] Sir/Ma'am,". Bias strongly toward this neutral fallback.
   - Do NOT write any closing sign-off or signature. The application appends the single approved signature after generation."""
    else:
        greeting_instruction = """
6. GENERIC GREETING AND SIGNATURE:
   - No usable human customer name is available. Start with "Hello," or "Greetings," without inventing a name or title.
   - Do NOT write any closing sign-off or signature. The application appends the single approved signature after generation."""

    if (platform or "").lower() == "email":
        channel_instruction = """
7. EMAIL RESPONSE STRUCTURE:
   - Output structured PLAIN TEXT only; the application converts it safely to HTML. Do not output HTML tags or Markdown.
   - Start with one brief, natural greeting line.
   - For a multi-part question, answer every distinct topic separately using short labeled lines such as "Delivery availability:", "Delivery time:", "Delivery charges:", or "Scheduling:".
   - Put a blank line between topics. Use "- " bullet lines only for multiple discrete conditions, documents, or steps.
   - End with one short, helpful closing line. Never compress several answers into one dense paragraph."""
    else:
        channel_instruction = """
7. MESSENGER / INSTAGRAM RESPONSE STRUCTURE:
   - Output plain text only. Never output HTML tags or Markdown emphasis such as **bold**, because these channels display those characters literally.
   - Use short paragraphs and line breaks. For a multi-part question, answer each distinct topic on its own labeled line.
   - Use simple "- " bullets only for discrete lists. Keep the response easy to scan in a chat bubble."""

    system_prompt = f"""{mode_framing}

RULES FOR RESPONSE GENERATION:
1. GREETINGS vs DIRECT QUESTIONS:
   - GREETING-ONLY MESSAGES: Use the required personalized or generic greeting below, then warmly ask how {business_name} can help.
   - DIRECT QUESTIONS: Use the required greeting below, then immediately answer the customer's exact question without a generic welcome paragraph.

{product_policy_instruction}

3. CONVERSATION MEMORY & CONTINUATION:
   - Use the Chat History to follow up naturally. Do NOT repeat generic greetings if you are already in an ongoing discussion about a product.

4. STRICT LANGUAGE & STYLE RULE:
   - {lang_instruction}{sentiment_instruction}

5. CONTEXT STICKINESS:
   - Use the knowledge base context below to answer. Do NOT hallucinate business policies or facts not supported by the context.

    - If the context says information cannot be confirmed, respond in one or two sentences. Never say "we need time", "we will provide it shortly", or promise a future update.
    - Do not share or request an owner's private phone number, email, or other personal contact details. Ask the customer to continue through this official chat instead.
{greeting_instruction}

{channel_instruction}

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
    mode: Literal["auto", "review"] = "review",
    platform: Optional[str] = None,
    customer_name: Optional[str] = None,
    business_name: str = "the business",
) -> List[Dict[str, str]]:
    """
    Builds system and user message payload using the unified prompt builder.
    """
    context_text = "\n\n".join([f"- {chunk.get('content', '')}" for chunk in context_chunks]) if context_chunks else "No relevant context found."
    system_prompt = build_system_prompt(
        context=context_text,
        mode=mode,
        language=language,
        sentiment=sentiment,
        platform=platform,
        customer_name=customer_name,
        business_name=business_name,
    )

    user_message = f"Customer Question: {customer_message}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
