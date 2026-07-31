"""Add explicit invitation revocation state.

Safe to run repeatedly.
"""

from sqlalchemy import text

from app.core.database import engine


def run() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE invitations "
                "ADD COLUMN IF NOT EXISTS revoked BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )


if __name__ == "__main__":
    run()
    print("Invitation revocation migration complete.")
