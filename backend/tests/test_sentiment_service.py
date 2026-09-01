import pytest

from app.services.sentiment_service import detect_sentiment


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("malai hajur ko service naramaro lagyo", "negative"),
        ("yo service naramro cha", "negative"),
        ("service ramro chaina", "negative"),
        ("ma santushta chaina", "negative"),
        ("service ekdam ramro cha", "positive"),
        ("tapai ko sewa dami cha", "positive"),
        ("ma santushta chu, dhanyabad", "positive"),
    ],
)
def test_explicit_romanized_nepali_sentiment(message, expected):
    """Explicit lexicon matches must not need the model to classify correctly."""
    assert detect_sentiment(message) == expected

@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("hajur ko service dami xa", "positive"),
        ("malai yo product man paryo", "positive"),
        ("service thik thak xa", "neutral"),
        ("khasai ramro pani haina, naramro pani haina", "neutral"),
        ("Hello mailai yo Techsuru business owner ko contact detail chaiyeko thiyo?", "neutral"),
        ("yo app chalna sajilo xa", "positive"),
        ("malai service ramro lagena", "negative"),
        ("hajur ko response dherai dhilo xa", "negative"),
        ("sabai kura thik xa tara ali sudhar garnu parxa", "neutral"),
        ("ma yo service bata santushta chu", "positive"),
        ("ma yo service bata santushta chaina", "negative"),
        ("support team le ramro madat garyo", "positive"),
        ("support team le samasya samadhan garena", "negative"),
        ("product thikai xa, khasai kei problem chaina", "neutral"),
        ("yo service ta babal raixa", "positive"),
        ("paisa anusar ko quality xaina", "negative"),
        ("malai thaha xaina yo ramro ho ki haina", "neutral"),
        ("man pareko xa, feri pani prayog garxu", "positive"),
        ("maan pareko xaina, feri prayog gardina", "negative"),
        ("khai yo service ko barema kehi bhanna sakdina", "neutral"),
        ("ramro bhanera liyeko thiye tara nirash vayen", "negative"),
    ],
)
def test_supplied_romanized_nepali_ground_truth(message, expected):
    assert detect_sentiment(message) == expected
