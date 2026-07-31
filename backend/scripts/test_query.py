import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.rag_service import rag_service

logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing rag_service.query()...")
    db = SessionLocal()
    try:
        res = await rag_service.query(
            question="What is the return policy?",
            business_id=1,
            db=db,
            conversation_id=1
        )
        print("Result:", res)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
