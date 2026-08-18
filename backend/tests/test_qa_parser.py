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
