"""
Data shapes shared across the pipeline.

Defining these as Pydantic models (rather than raw dicts) gives us two things:
1. Automatic validation — if the AI returns something malformed, we find out
   immediately instead of it silently breaking a later step.
2. We can hand this same schema straight to OpenAI's structured output feature,
   so the model is constrained to return exactly this shape.
"""

from pydantic import BaseModel, Field
from typing import List


class FoodItem(BaseModel):
    # The food name exactly as the user said it, e.g. "toast"
    raw_name: str = Field(description="The food name as mentioned by the user")

    # A normalized, generic name we'll use to search the nutrition database.
    # e.g. "toast" -> "bread, white, toasted"
    canonical_name: str = Field(
        description=(
            "A generic, canonical form of this food suitable for looking up "
            "in a nutrition database. Prefer common generic names over brand "
            "names unless the user specified a brand."
        )
    )

    quantity: float = Field(description="Numeric quantity, e.g. 2, 1, 0.5")
    unit: str = Field(
        description=(
            "Unit for the quantity, e.g. 'large', 'slice', 'cup', 'g', 'piece'. "
            "If the user gave no unit, use 'serving'."
        )
    )


class ParsedMeal(BaseModel):
    items: List[FoodItem]