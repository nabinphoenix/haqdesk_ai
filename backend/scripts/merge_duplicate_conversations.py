"""Atomically apply the explicitly approved conversation merges."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message


MERGES = ((13, 2), (12, 3))
BACKUP_PATH = Path(__file__).resolve().parents[1] / "backups" / (
    "conversation_merge_12_to_3_13_to_2_2026-07-28.json"
)


def main():
    if not BACKUP_PATH.is_file() or BACKUP_PATH.stat().st_size == 0:
        raise RuntimeError(f"Required backup is missing or empty: {BACKUP_PATH}")

    db = SessionLocal()
    try:
        results = []
        for source_id, target_id in MERGES:
            source = (
                db.query(Conversation)
                .filter(Conversation.id == source_id)
                .with_for_update()
                .one()
            )
            target = (
                db.query(Conversation)
                .filter(Conversation.id == target_id)
                .with_for_update()
                .one()
            )
            if (
                source.business_id != target.business_id
                or source.customer_id != target.customer_id
            ):
                raise RuntimeError(
                    f"Unsafe merge {source_id}→{target_id}: "
                    "business/customer identities differ"
                )

            source_messages = (
                db.query(Message)
                .filter(Message.conversation_id == source_id)
                .order_by(Message.timestamp.asc(), Message.id.asc())
                .all()
            )
            original = {
                message.id: (message.timestamp, message.sender_type, message.sender_id)
                for message in source_messages
            }
            for message in source_messages:
                message.conversation_id = target_id

            db.flush()
            for message_id, preserved in original.items():
                message = db.query(Message).filter(Message.id == message_id).one()
                actual = (message.timestamp, message.sender_type, message.sender_id)
                if actual != preserved:
                    raise RuntimeError(
                        f"Message {message_id} metadata changed during merge"
                    )

            db.delete(source)
            results.append(
                {
                    "source": source_id,
                    "target": target_id,
                    "moved": len(source_messages),
                }
            )

        db.commit()

        for result in results:
            target_count = db.query(Message).filter(
                Message.conversation_id == result["target"]
            ).count()
            source_exists = db.query(Conversation).filter(
                Conversation.id == result["source"]
            ).count()
            print(
                f"merge={result['source']}->{result['target']} "
                f"moved={result['moved']} target_messages={target_count} "
                f"source_exists={source_exists}"
            )
        print(f"FINAL_CONVERSATION_COUNT={db.query(Conversation).count()}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
