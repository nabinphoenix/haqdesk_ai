from app.services.reply_formatter import (
    email_html,
    ensure_signature,
    structured_plain_text,
    usable_customer_name,
)


def test_email_renderer_creates_paragraphs_labels_and_list():
    reply = """Namaste Rupa ji,

Delivery availability:
Delivery is available in selected locations.

Delivery conditions:
- Confirm the address.
- Keep identification ready.

Thank you."""
    rendered = email_html(reply)
    assert "<strong>Delivery availability:</strong>" in rendered
    assert "<strong>Delivery conditions:</strong>" in rendered
    assert "<ul" in rendered
    assert rendered.count("<li") == 2


def test_colons_in_body_values_are_not_treated_as_labels():
    reply = """Hello,

Business hours:
Our standard business hours are 9:00 AM to 6:00 PM, Sunday to Friday.

Display details:
The screen ratio is 16:9 and status is key:value.

More information is available at https://example.com/support:8443/hours."""
    rendered = email_html(reply)

    assert "<strong>Business hours:</strong>" in rendered
    assert "<strong>Display details:</strong>" in rendered
    assert (
        "<p style=\"margin:0 0 12px 0;\">"
        "Our standard business hours are 9:00 AM to 6:00 PM, Sunday to Friday."
        "</p>"
    ) in rendered
    assert "<strong>Our standard business hours are 9:</strong>" not in rendered
    assert "<strong>The screen ratio is 16:</strong>" not in rendered
    assert "<strong>More information is available at https:</strong>" not in rendered
    assert "9: 00" not in rendered


def test_meta_plain_text_removes_html_and_markdown_but_keeps_breaks():
    reply = "<b>Delivery:</b> **Available**\n\n- Kathmandu\n- Pokhara"
    rendered = structured_plain_text(reply)
    assert "<b>" not in rendered
    assert "**" not in rendered
    assert "\n\n" in rendered
    assert "- Kathmandu" in rendered


def test_signature_is_present_exactly_once():
    rendered = ensure_signature(
        "Hello Rupa Ma'am,\n\nYour answer.\n\nBest regards,\nOld Name Support Team",
        "Acme Repairs",
    )
    assert rendered.count("Best regards,") == 1
    assert rendered.endswith("Best regards,\nAcme Repairs Support Team")


def test_email_has_only_the_approved_support_signature():
    rendered = email_html(ensure_signature("Hello,\n\nYour answer.", "Acme Repairs"))
    assert rendered.count("Best regards,") == 1
    assert rendered.count("Acme Repairs Support Team") == 1
    assert "Automated AI Response" not in rendered


def test_blank_business_name_uses_neutral_signature():
    rendered = ensure_signature("Hello,\n\nYour answer.", "")
    assert rendered.endswith("Best regards,\nSupport Team")


def test_generic_platform_identity_is_not_used_as_name():
    assert usable_customer_name("Instagram User 17623") is None
    assert usable_customer_name("junior_jk_berlin") is None
    assert usable_customer_name("Rupa Nepali") == "Rupa Nepali"
