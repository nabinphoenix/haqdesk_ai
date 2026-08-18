from app.core.config import settings
from app.services.credential_service import get_sandbox_channel_credentials


def test_global_channel_credentials_require_explicit_sandbox_opt_in(monkeypatch):
    monkeypatch.setattr(
        settings, "ALLOW_GLOBAL_CHANNEL_CREDENTIALS_IN_SANDBOX", False
    )
    monkeypatch.setattr(settings, "WHATSAPP_ACCESS_TOKEN", "placeholder-token")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "placeholder-number")

    assert get_sandbox_channel_credentials("whatsapp") is None


def test_explicit_sandbox_opt_in_can_use_placeholder_credentials(monkeypatch):
    monkeypatch.setattr(
        settings, "ALLOW_GLOBAL_CHANNEL_CREDENTIALS_IN_SANDBOX", True
    )
    monkeypatch.setattr(settings, "WHATSAPP_ACCESS_TOKEN", "placeholder-token")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "placeholder-number")

    assert get_sandbox_channel_credentials("whatsapp") == {
        "access_token": "placeholder-token",
        "metadata": {"phone_number_id": "placeholder-number"},
    }
