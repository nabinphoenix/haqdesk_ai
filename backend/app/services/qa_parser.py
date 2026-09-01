import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("uvicorn")


def _is_document_noise(line: str) -> bool:
    """Recognize generic document scaffolding without naming any tenant."""
    normalized = re.sub(r"\s+", " ", line).strip()
    return bool(
        re.fullmatch(r"page\s+\d+(?:\s+of\s+\d+)?", normalized, re.IGNORECASE)
        or re.fullmatch(r"(?:table\s+of\s+)?contents", normalized, re.IGNORECASE)
        or re.fullmatch(r"all\s+questions\s+and\s+answers", normalized, re.IGNORECASE)
        or re.fullmatch(r"(?:for\s+)?rag(?:\s+ai)?\s+knowledge\s+base", normalized, re.IGNORECASE)
        or normalized.casefold() in {
            "techsuru rag ai knowledge base",
            "all questions and answers for business ai training",
            "for rag ai assistant training and business faq use",
        }
        or re.fullmatch(r"\d+\.\s+.+?(?:\s+-\s+\d+\s+q&as?;?)?", normalized, re.IGNORECASE)
    )


def _clean_qa_field(value: str) -> str:
    """Remove repeated PDF headers/section lines while preserving real content."""
    lines = [
        line.strip()
        for line in value.splitlines()
        if line.strip() and not _is_document_noise(line)
    ]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


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
    # Q/A markers are normally at the start of a line, but an answer marker
    # may also follow the question on the same line. Requiring punctuation
    # after A prevents the lowercase "a" in "test a product" from ending
    # the question early.
    question_marker = r"(?:Q\d*|Question\s*\d*)\s*[.:)\-]"
    answer_marker = r"(?:A\d*|Answer\s*\d*)\s*[.:)\-]"
    pattern = re.compile(
        rf"^[ \t]*{question_marker}[ \t]*(?P<question>.*?)"
        rf"[ \t]*{answer_marker}[ \t]*(?P<answer>.*?)"
        rf"(?=^[ \t]*{question_marker}|\Z)",
        re.DOTALL | re.IGNORECASE | re.MULTILINE,
    )

    qa_pairs = []
    for match in pattern.finditer(text):
        q_raw = match.group("question").strip()
        a_raw = match.group("answer").strip()

        # Skip cover page / meta dataset text artifacts
        if any(ignore.casefold() in q_raw.casefold() or ignore.casefold() in a_raw.casefold() for ignore in [
            "This PDF contains", "structured FAQ", "RAG AI Knowledge Base"
        ]):
            continue

        q_clean = _clean_qa_field(q_raw)
        a_clean = _clean_qa_field(a_raw)

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
