from app.core.database import SessionLocal
from sqlalchemy import text

def run():
    db = SessionLocal()
    try:
        db.execute(text("ALTER TABLE businesses ADD COLUMN IF NOT EXISTS ai_response_mode VARCHAR DEFAULT 'review';"))
        db.commit()
        print("Schema altered successfully!")
    except Exception as e:
        print("Error altering schema:", e)
    finally:
        db.close()

if __name__ == '__main__':
    run()
