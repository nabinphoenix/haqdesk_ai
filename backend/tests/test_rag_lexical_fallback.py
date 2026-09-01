from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.business import Business
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.services.rag_service import RAGService


def test_retrieval_falls_back_to_tenant_faq_rows_when_qdrant_is_unavailable():
    engine = create_engine("sqlite:///:memory:")
    Business.__table__.create(engine)
    KnowledgeDocument.__table__.create(engine)
    KnowledgeChunk.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        first = Business(id=1, name="First Business")
        second = Business(id=2, name="Second Business")
        first_doc = KnowledgeDocument(
            id=10,
            business_id=1,
            filename="first.txt",
            status="ready",
        )
        second_doc = KnowledgeDocument(
            id=20,
            business_id=2,
            filename="second.txt",
            status="ready",
        )
        session.add_all([first, second, first_doc, second_doc])
        session.flush()
        session.add_all([
            KnowledgeChunk(
                business_id=1,
                document_id=10,
                content=(
                    "Q: Can customers test a product before buying?\n"
                    "A: Customers may inspect and test selected products before purchase."
                ),
            ),
            KnowledgeChunk(
                business_id=2,
                document_id=20,
                content="Q: Can customers test a product?\nA: This is private to the second business.",
            ),
        ])
        session.commit()

        service = RAGService()
        service._collection_exists = lambda _business_id: False
        chunks = service.retrieve_chunks(
            "Can customers test a product before buying?",
            business_id=1,
            db=session,
        )

        assert chunks
        assert chunks[0]["filename"] == "first.txt"
        assert "inspect and test selected products" in chunks[0]["content"]
        assert all(chunk["filename"] != "second.txt" for chunk in chunks)
    finally:
        session.close()
