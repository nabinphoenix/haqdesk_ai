"""
Migration Script: BAAI/bge-m3 (1024-dim) -> intfloat/multilingual-e5-large (1024-dim)

This script validates the loading of the multilingual-e5-large embedding model.
Since both models produce 1024-dimensional vectors, collections do not strictly need recreation,
but this script runs validation checks to ensure correctness.

Usage:
    cd backend
    python scripts/migrate_e5_large.py
"""
import sys
import io
import os
import logging

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.rag_service import rag_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("migrate_e5_large")


def main():
    print("=" * 70)
    print("  HAQDESK AI — Embedding Model Validation")
    print(f"  Old/Existing: 1024-dim")
    print(f"  New: {settings.EMBEDDING_MODEL} ({settings.EMBEDDING_DIM}-dim)")
    print("=" * 70)

    # Step 1: Connect to Qdrant
    print("\n[1/2] Connecting to Qdrant...")
    try:
        collections = rag_service.qdrant.get_collections().collections
        collection_names = [c.name for c in collections]
        print(f"  Found {len(collection_names)} collection(s): {collection_names}")
    except Exception as e:
        logger.error(f"  Failed to connect to Qdrant: {e}")
        sys.exit(1)

    # Step 2: Validate new model loads and produces correct dimensions
    print(f"\n[2/2] Validating embedding model...")
    try:
        test_embedding = rag_service.embed_text("test embedding validation")
        actual_dim = len(test_embedding)
        expected_dim = settings.EMBEDDING_DIM

        if actual_dim == expected_dim:
            print(f"  [OK] Model '{settings.EMBEDDING_MODEL}' produces {actual_dim}-dim vectors (expected {expected_dim})")
        else:
            logger.error(
                f"  [FAIL] Dimension mismatch! Model produces {actual_dim}-dim but "
                f"EMBEDDING_DIM is set to {expected_dim}. Update your .env!"
            )
            sys.exit(1)
    except Exception as e:
        logger.error(f"  [FAIL] Failed to load embedding model: {e}")
        sys.exit(1)

    # Summary
    print("\n" + "=" * 70)
    print("  VALIDATION COMPLETE")
    print("=" * 70)
    print("""
Your vector store uses 1024 dimensions.
Since both BAAI/bge-m3 and multilingual-e5-large use 1024 dimensions,
re-indexing is optional. However, for maximum search precision and alignment with
E5's prefix template (query: / passage:), it is highly recommended to re-ingest documents.
""")


if __name__ == "__main__":
    main()
