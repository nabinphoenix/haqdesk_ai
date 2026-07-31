import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.messaging_service import MessagingService

async def main():
    service = MessagingService()
    psid = "26888499590807520" # Jagadish Kharel Facebook PSID
    token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
    
    print(f"Testing direct Facebook Messenger send to PSID {psid}...")
    result = await service.send_facebook_message(
        access_token=token,
        recipient_id=psid,
        message_text="Hello Jagadish! This is a direct test message from HaqDesk AI backend."
    )
    print("Meta API Response:", result)

if __name__ == "__main__":
    asyncio.run(main())
