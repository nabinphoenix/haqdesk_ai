import json

import httpx
import pytest

from app.services.messaging_service import MessageDeliveryError, _validated_meta_response


def make_response(status_code, body):
    return httpx.Response(
        status_code,
        content=json.dumps(body).encode(),
        request=httpx.Request("POST", "https://graph.facebook.com/me/messages"),
    )


def test_meta_response_requires_message_id_for_messenger():
    with pytest.raises(MessageDeliveryError):
        _validated_meta_response("facebook", make_response(200, {"recipient_id": "1"}))


def test_meta_response_raises_with_graph_error_body():
    body = {"error": {"message": "Invalid OAuth access token.", "code": 190}}
    with pytest.raises(MessageDeliveryError) as exc:
        _validated_meta_response("facebook", make_response(400, body))
    assert exc.value.status_code == 400
    assert exc.value.response_body == body


def test_meta_response_returns_confirmed_message():
    body = {"recipient_id": "1", "message_id": "mid.123"}
    assert _validated_meta_response("facebook", make_response(200, body)) == body
