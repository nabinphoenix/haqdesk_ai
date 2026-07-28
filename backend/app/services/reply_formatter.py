"""Channel-safe formatting for generated support replies."""

import html
import re


_MARKDOWN_EMPHASIS = re.compile(r"(?<!\*)\*{1,2}([^*\n]+?)\*{1,2}(?!\*)")
_HTML_TAG = re.compile(r"<[^>]+>")
# Labels must occupy the entire line. This deliberately rejects colons inside
# prose and values such as 9:00, 16:9, https://..., and key:value.
_LABEL = re.compile(r"^([A-Za-z][A-Za-z0-9 /&()'-]{1,48}):$")
_GENERIC_NAME = re.compile(
    r"^(facebook|instagram|messenger|whatsapp)\s+user\b|"
    r"^user\s*\d*$|^customer\s*\d*$|^unknown$",
    re.IGNORECASE,
)
_SIGNATURE = "Best regards,\nTechSuru Support Team"


def usable_customer_name(value: str):
    """Return a human-looking display name, otherwise None."""
    name = re.sub(r"\s+", " ", (value or "").strip())
    if not name or "@" in name or _GENERIC_NAME.search(name):
        return None
    if re.fullmatch(r"[\W_\d]+", name) or "_" in name:
        return None
    if len(name) < 2 or len(name) > 80:
        return None
    return name


def ensure_signature(value: str) -> str:
    """Guarantee one consistent plain-text support signature."""
    text = structured_plain_text(value)
    text = re.sub(
        r"\n*(?:Best regards,?\s*\n+)?TechSuru Support Team\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).rstrip()
    return f"{text}\n\n{_SIGNATURE}" if text else _SIGNATURE


def structured_plain_text(value: str) -> str:
    """Return plain text that is safe for Messenger and Instagram."""
    text = html.unescape(value or "")
    text = _HTML_TAG.sub("", text)
    text = _MARKDOWN_EMPHASIS.sub(r"\1", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def email_html(value: str) -> str:
    """Render structured plain text as conservative, Gmail-safe HTML."""
    text = structured_plain_text(value)
    lines = text.split("\n")
    blocks = []
    bullets = []

    def flush_bullets():
        if not bullets:
            return
        items = "".join(
            f'<li style="margin:0 0 8px 0;">{html.escape(item)}</li>'
            for item in bullets
        )
        blocks.append(
            '<ul style="margin:8px 0 16px 22px;padding:0;">'
            f"{items}</ul>"
        )
        bullets.clear()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_bullets()
            continue
        if re.match(r"^[-•]\s+", line):
            bullets.append(re.sub(r"^[-•]\s+", "", line))
            continue

        flush_bullets()
        match = _LABEL.match(line)
        if match:
            label = match.group(1)
            blocks.append(
                '<p style="margin:0 0 12px 0;">'
                f"<strong>{html.escape(label)}:</strong></p>"
            )
        else:
            blocks.append(
                f'<p style="margin:0 0 12px 0;">{html.escape(line)}</p>'
            )
    flush_bullets()

    return (
        '<div style="font-family:Arial,sans-serif;max-width:640px;'
        'padding:20px;color:#222;font-size:15px;line-height:1.6;">'
        + "".join(blocks)
        + "</div>"
    )
