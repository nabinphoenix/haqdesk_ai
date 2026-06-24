from typing import List, Dict, Any

def build_customer_reply_messages(
    customer_message: str,
    context_chunks: List[Dict[str, Any]],
    sentiment: str | None = None,
    language: str = "english",
    business_profile: Dict[str, Any] | None = None
) -> List[Dict[str, str]]:
    """
    Build the messages list (system and user role) for the LLM call.
    """
    context_text = "\n\n".join([f"- {chunk['content']}" for chunk in context_chunks])
    
    # Language instructions
    lang_instruction = {
        "english": "Reply in English only.",
        "nepali": "Reply in Nepali using Devanagari script only.",
        "romanized_nepali": "Reply in casual romanized Nepali matching the customer's tone. Do not use Devanagari script."
    }.get(language, "Reply in the same language and tone as the customer.")

    sentiment_instruction = ""
    if sentiment:
        sentiment_instruction = f"The customer's current sentiment is classified as: '{sentiment}'. Adjust your tone accordingly (e.g., be exceptionally polite and reassuring if negative)."

    business_info = ""
    if business_profile:
        name = business_profile.get("name", "our business")
        desc = business_profile.get("description", "")
        business_info = f"Business Name: {name}\nBusiness Description: {desc}"

    system_instruction = f"""You are HaqDesk AI, an advanced customer-support assistant.
Generate a draft reply for a human representative to review. 
Your goal is to assist the representative with a draft reply using ONLY the provided business knowledge-base context.

RULES:
1. Use ONLY the provided business knowledge-base context below.
2. Do NOT hallucinate business policies, facts, or contact details not present in the context.
3. If the answer is not supported by the context, clearly indicate that the representative should review or request more information (e.g., "I'm sorry, I cannot find information on X in the knowledge base. The representative will check and get back to you.").
4. Keep the tone professional, helpful, and concise.
5. The output is a draft for the representative, not an auto-sent reply.
{sentiment_instruction}
{lang_instruction}

{business_info}

--- KNOWLEDGE BASE CONTEXT START ---
{context_text}
--- KNOWLEDGE BASE CONTEXT END ---
"""

    user_message = f"Customer Question: {customer_message}\n\nDraft Answer:"

    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_message}
    ]
