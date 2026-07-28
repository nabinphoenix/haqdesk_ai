"""
Dump all 119 Q&A chunks from Qdrant to inspect for near-domain confusable pairs.
"""
import sys
import io
import os

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
logging.basicConfig(level=logging.WARNING)

from app.services.rag_service import rag_service
from app.core.config import settings

# Force Qdrant init
_ = rag_service.qdrant

# Scroll all points from the collection
all_points, _ = rag_service.qdrant.scroll(
    collection_name=settings.QDRANT_COLLECTION_NAME,
    limit=200,
    with_payload=True,
    with_vectors=False,
)

print(f"Total chunks: {len(all_points)}\n")

for i, point in enumerate(all_points):
    content = point.payload.get("content", "")
    page = point.payload.get("page_number", "?")
    # Show first 200 chars of each chunk
    preview = content[:250].replace('\n', ' | ')
    print(f"[{i+1:3d}] (pg {page:>2}) {preview}")
    print()
