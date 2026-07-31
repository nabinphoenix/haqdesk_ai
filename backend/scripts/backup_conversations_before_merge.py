"""Read-only backup and duplicate audit for the approved conversation merge."""

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message


BACKUP_PATH = Path(__file__).resolve().parents[1] / "backups" / (
    "conversation_merge_12_to_3_13_to_2_2026-07-28.json"
)
SOURCE_IDS = (12, 13)


def serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def row_dict(row):
    return {
        column.name: serialize(getattr(row, column.name))
        for column in row.__table__.columns
    }


def main():
    db = SessionLocal()
    try:
        conversations = (
            db.query(Conversation)
            .filter(Conversation.id.in_(SOURCE_IDS))
            .order_by(Conversation.id)
            .all()
        )
        if {conversation.id for conversation in conversations} != set(SOURCE_IDS):
            raise RuntimeError("Both source conversations 12 and 13 must exist")

        exported = []
        for conversation in conversations:
            customer = db.query(Customer).filter(
                Customer.id == conversation.customer_id
            ).one()
            messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation.id)
                .order_by(Message.timestamp.asc(), Message.id.asc())
                .all()
            )
            exported.append(
                {
                    "conversation": row_dict(conversation),
                    "customer": row_dict(customer),
                    "message_count": len(messages),
                    "messages": [row_dict(message) for message in messages],
                }
            )

        # A PSID split means the same business/platform/platform_user_id has
        # conversations attached through more than one customer record.
        grouped = {}
        customers = db.query(Customer).order_by(Customer.id).all()
        for customer in customers:
            key = (
                customer.business_id,
                (customer.platform or "").lower(),
                customer.platform_user_id,
            )
            item = grouped.setdefault(
                key,
                {
                    "business_id": customer.business_id,
                    "platform": customer.platform,
                    "platform_user_id": customer.platform_user_id,
                    "customers": [],
                    "conversation_ids": [],
                },
            )
            item["customers"].append(
                {"id": customer.id, "display_name": customer.display_name}
            )
            item["conversation_ids"].extend(
                conversation_id
                for (conversation_id,) in db.query(Conversation.id)
                .filter(Conversation.customer_id == customer.id)
                .order_by(Conversation.id)
                .all()
            )

        psid_splits = [
            item
            for item in grouped.values()
            if len(item["customers"]) > 1 and len(item["conversation_ids"]) > 1
        ]

        payload = {
            "backup_created_at": datetime.now().astimezone().isoformat(),
            "purpose": "Pre-merge backup for conversation 13→2 and 12→3",
            "source_conversations": exported,
            "whole_table_psid_split_audit": {
                "customer_count": len(customers),
                "split_issue_count": len(psid_splits),
                "issues": psid_splits,
            },
        }
        BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(f"BACKUP_PATH={BACKUP_PATH}")
        for entry in exported:
            print(
                f"conversation={entry['conversation']['id']} "
                f"messages={entry['message_count']}"
            )
        print(f"PSID_SPLIT_ISSUES={len(psid_splits)}")
        for issue in psid_splits:
            print(json.dumps(issue, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
