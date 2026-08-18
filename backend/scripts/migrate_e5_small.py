"""
Migration Script: BAAI/bge-m3 (1024-dim) → intfloat/multilingual-e5-small (384-dim)

This script handles the one-time migration needed when switching embedding models.
Since vector dimensions changed (1024 → 384), existing Qdrant collections are
incompatible and must be deleted. Documents must then be re-ingested via the API.

Usage:
    cd backend
    python scripts/migrate_e5_small.py
"""
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.rag_service import rag_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("migrate_e5_small")


def main():
    print("=" * 70)
    print("  HAQDESK AI — Embedding Model Migration")
    print(f"  Old: BAAI/bge-m3 (1024-dim)")
    print(f"  New: {settings.EMBEDDING_MODEL} ({settings.EMBEDDING_DIM}-dim)")
    print("=" * 70)

    # Step 1: Connect to Qdrant
    print("\n[1/3] Connecting to Qdrant...")
    try:
        collections = rag_service.qdrant.get_collections().collections
        collection_names = [c.name for c in collections]
        print(f"  Found {len(collection_names)} collection(s): {collection_names}")
    except Exception as e:
        logger.error(f"  Failed to connect to Qdrant: {e}")
        sys.exit(1)

    # Step 2: Delete old collections with the haqdesk prefix
    prefix = settings.QDRANT_COLLECTION_PREFIX.strip().strip("_")
    old_collections = [c for c in collection_names if c.startswith(prefix)]

    if not old_collections:
        print(f"\n[2/3] No collections with prefix '{prefix}' found. Nothing to delete.")
    else:
        print(f"\n[2/3] Deleting {len(old_collections)} old collection(s)...")
        for coll_name in old_collections:
            try:
                # Check current dimension
                info = rag_service.qdrant.get_collection(coll_name)
                vectors = info.config.params.vectors
                current_dim = vectors.size if hasattr(vectors, "size") else "unknown"

                rag_service.qdrant.delete_collection(coll_name)
                print(f"  ✓ Deleted '{coll_name}' (was {current_dim}-dim)")
            except Exception as e:
                logger.error(f"  ✗ Failed to delete '{coll_name}': {e}")

        # Clear the in-memory cache
        rag_service._initialized_collections.clear()

    # Step 3: Validate new model loads and produces correct dimensions
    print(f"\n[3/3] Validating new embedding model...")
    try:
        test_embedding = rag_service.embed_text("test embedding validation")
        actual_dim = len(test_embedding)
        expected_dim = settings.EMBEDDING_DIM

        if actual_dim == expected_dim:
            print(f"  ✓ Model '{settings.EMBEDDING_MODEL}' produces {actual_dim}-dim vectors (expected {expected_dim})")
        else:
            logger.error(
                f"  ✗ Dimension mismatch! Model produces {actual_dim}-dim but "
                f"EMBEDDING_DIM is set to {expected_dim}. Update your .env!"
            )
            sys.exit(1)
    except Exception as e:
        logger.error(f"  ✗ Failed to load embedding model: {e}")
        sys.exit(1)

    # Summary
    print("\n" + "=" * 70)
    print("  MIGRATION COMPLETE")
    print("=" * 70)
    print("""
Next steps:
  1. Start the backend server: uvicorn app.main:app --reload
  2. Re-upload all knowledge documents through the API or admin UI.
     Each document will be automatically chunked and embedded with the
     new model (intfloat/multilingual-e5-small, 384-dim).
  3. Verify retrieval quality with: python scripts/eval_retrieval.py
""")


if __name__ == "__main__":
    main()
