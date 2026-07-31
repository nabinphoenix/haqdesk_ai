"""Run three live LLM checks for personalized greeting behavior."""

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.prompts.customer_reply_prompt import build_system_prompt
from app.services.llm_gateway import llm_gateway
from app.services.reply_formatter import ensure_signature, usable_customer_name


CASES = [
    ("clearly_gendered", "Michael Smith", r"^Hello Michael Sir,"),
    ("ambiguous", "Alex Morgan", r"^Hello Alex Sir/Ma'am,"),
    ("generic", "Instagram User 17623", r"^(Hello|Greetings),"),
]


async def main():
    for label, display_name, expected in CASES:
        usable_name = usable_customer_name(display_name)
        prompt = build_system_prompt(
            context=(
                "TechSuru sells laptops and provides delivery in selected "
                "locations. Delivery timing and charges depend on location."
            ),
            mode="auto",
            language="english",
            sentiment="neutral",
            platform="facebook",
            customer_name=usable_name,
        )
        result = await llm_gateway.complete(
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        "Do you deliver laptops, how long does delivery take, "
                        "and are there delivery charges?"
                    ),
                },
            ],
            max_tokens=350,
        )
        reply = ensure_signature(result["content"])
        passed = bool(re.search(expected, reply))
        if label == "generic":
            passed = passed and "Instagram User" not in reply
        passed = passed and reply.endswith(
            "Best regards,\nTechSuru Support Team"
        )
        print(f"CASE={label}")
        print(f"DISPLAY_NAME={display_name}")
        print(f"USABLE_NAME={usable_name}")
        print(f"PASSED={passed}")
        print("REPLY_START")
        print(reply)
        print("REPLY_END")
        if not passed:
            raise RuntimeError(f"Live greeting verification failed: {label}")


if __name__ == "__main__":
    asyncio.run(main())
