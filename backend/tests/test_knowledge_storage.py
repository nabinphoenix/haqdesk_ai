import uuid

from app.core.config import settings
from app.routers.knowledge import knowledge_storage_path


def test_knowledge_file_path_is_business_scoped_and_configurable(
    monkeypatch, tmp_path
):
    business_id = uuid.uuid4().int
    document_id = uuid.uuid4().int
    monkeypatch.setattr(settings, "KNOWLEDGE_UPLOAD_ROOT", str(tmp_path))

    path = knowledge_storage_path(business_id, document_id, "policy.pdf")
    path.parent.mkdir(parents=True)
    path.write_bytes(b"original document bytes")

    assert path.parent == tmp_path / str(business_id)
    assert path.name == f"{document_id}_policy.pdf"
    assert path.read_bytes() == b"original document bytes"
