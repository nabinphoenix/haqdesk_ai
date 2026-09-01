from app.services.qa_parser import parse_qa_pairs


def test_parser_preserves_business_name_in_legitimate_content():
    text = """Q1) What does Acme Repairs offer?
A) Acme Repairs services musical instruments.
Q2) Does Acme Repairs offer warranties?
A) Warranty terms are listed on the invoice."""

    pairs = parse_qa_pairs(text)

    assert len(pairs) == 2
    assert "Acme Repairs" in pairs[0]["question"]
    assert "Acme Repairs" in pairs[0]["answer"]


def test_parser_removes_only_generic_full_line_document_noise():
    text = """Q1) Page 2
Contents
What is the delivery time?
A) Delivery normally takes two days."""

    pairs = parse_qa_pairs(text)

    assert len(pairs) == 1
    assert pairs[0]["question"] == "What is the delivery time?"


def test_parser_keeps_lowercase_a_inside_question():
    text = """Q6) Can customers test a product before buying?
A) Customers may inspect and test selected products before purchase, depending on product type, branch policy, and availability."""

    pairs = parse_qa_pairs(text)

    assert len(pairs) == 1
    assert pairs[0]["question"] == "Can customers test a product before buying?"
    assert "inspect and test selected products" in pairs[0]["answer"]


def test_parser_removes_section_heading_from_answer():
    text = """Q1) What contact details should the AI assistant provide?
A) Provide the support phone number.
17. Default Fallback Answers
Q2) Is this product available right now?
A) Contact support to confirm current stock."""

    pairs = parse_qa_pairs(text)

    assert len(pairs) == 2
    assert "17. Default Fallback Answers" not in pairs[0]["answer"]
