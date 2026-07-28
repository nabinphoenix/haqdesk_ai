import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("uvicorn")


def parse_qa_pairs(text: str) -> List[Dict[str, str]]:
    """
    Parses Q&A pairs from text formatted as Q1) ... A) ... or Q1: ... A: ...
    Strips document header noise and table of contents entries.
    Returns a list of dicts: [{"question": ..., "answer": ..., "content": "Q: ...\nA: ..."}, ...]
    If no valid Q&A pairs are found, returns an empty list.
    """
    if not text or not text.strip():
        return []

    # Pattern matching Q1) or Q1: or Question 1: followed by answer marker A) or A: or Answer:
    pattern = r"(?:Q\d*[\s.:)-]|Question\s*\d*[\s.:)-])\s*(.+?)\s*(?:A\d*[\s.:)-]|Answer\s*\d*[\s.:)-])\s*(.+?)(?=(?:Q\d*[\s.:)-]|Question\s*\d*[\s.:)-])|\Z)"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    qa_pairs = []
    header_keywords = ['TechSuru', 'For RAG', 'Page ', 'Contents', 'All Questions and Answers']

    for q_match, a_match in matches:
        q_raw = q_match.strip()
        a_raw = a_match.strip()

        # Skip cover page / meta dataset text artifacts
        if any(ignore in q_raw or ignore in a_raw for ignore in [
            "This PDF contains", "dataset for TechSuru", "structured FA", "RAG AI Knowledge Base"
        ]):
            continue

        # Filter out header artifacts from question text
        q_lines = q_raw.split('\n')
        if len(q_lines) > 1:
            filtered_lines = [
                line for line in q_lines
                if not any(header in line for header in header_keywords)
            ]
            q_raw = " ".join(filtered_lines).strip()

        # Remove section titles like "1. Company Information\nWhat is..."
        q_clean = re.sub(r'^\d+\.\s+[A-Za-z\s,-]+?\n', '', q_raw).strip()

        # Normalize spaces
        q_clean = re.sub(r'\s+', ' ', q_clean).strip()
        a_clean = re.sub(r'\s+', ' ', a_raw).strip()

        # Skip invalid or TOC entries (e.g., "10 Q&As;" or truncated headers)
        if not q_clean or not a_clean or len(q_clean) < 5:
            continue
        if "Q&As;" in q_clean or "Q&As;" in a_clean:
            continue

        formatted_content = f"Q: {q_clean}\nA: {a_clean}"
        qa_pairs.append({
            "question": q_clean,
            "answer": a_clean,
            "content": formatted_content
        })

    logger.info(f"[QA Parser] Extracted {len(qa_pairs)} Q&A pairs from text.")
    return qa_pairs
