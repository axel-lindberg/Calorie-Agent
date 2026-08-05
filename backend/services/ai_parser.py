"""
Stage 1 of the pipeline: turn free-text input into structured food items.
"""

import sys
import os
import json

# Allow running this file directly (`python services/ai_parser.py`) as well
# as importing it as part of the backend package.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from models.schemas import ParsedMeal

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """\
You are a nutrition-logging assistant. The user will describe what they ate \
in free text. Extract every distinct food item mentioned, with:

- raw_name: the food as the user described it
- canonical_name: a generic, brand-free name suitable for searching a \
  nutrition database (e.g. "toast" -> "bread, white, toasted", \
  "a coke" -> "cola, carbonated beverage")
- quantity: a numeric quantity (estimate a sensible default if not stated, \
  e.g. "an egg" -> 1)
- unit: the unit for that quantity (e.g. "large", "slice", "cup", "g"). \
  If nothing sensible applies, use "serving".

Only extract actual food/drink items. Ignore filler words.
"""


def parse_meal_text(text: str) -> ParsedMeal:
    """
    Calls OpenAI to convert a free-text meal description into a ParsedMeal.

    Uses structured outputs (response_format=ParsedMeal) so the API response
    is guaranteed to match our Pydantic schema — no manual JSON parsing or
    prompt-begging for "respond only in JSON" needed.
    """
    completion = client.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format=ParsedMeal,
    )

    parsed = completion.choices[0].message.parsed

    if parsed is None:
        raise ValueError("Model did not return a parseable result.")

    return parsed


if __name__ == "__main__":
    print("Type a meal description (or 'quit' to exit):")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        result = parse_meal_text(user_input)
        print(json.dumps(result.model_dump(), indent=2))