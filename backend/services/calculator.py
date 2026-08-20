# Convert a matched item's quantity/unit into grams, then scale its
# per-100g nutrition data to the actual amount consumed.

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from models.schemas import MatchedItem, CalculatedItem, GramEstimate

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """\
You are estimating the weight, in grams, of a quantity of food.

You will be given a food name, a quantity, and a unit (e.g. "2 large" for \
eggs, "1 slice" for bread, "1 cup" for rice). Estimate the total weight in \
grams that this quantity/unit represents for this specific food, using \
typical real-world serving sizes.

Be specific to the food: a "slice" of bread and a "slice" of pizza are not \
the same weight, and a "cup" of leafy greens and a "cup" of rice are not \
the same weight either.
"""

# Units we can convert without an LLM call.
_DIRECT_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
}


def estimate_grams(canonical_name: str, quantity: float, unit: str, verbose: bool = False) -> Optional[float]:
    direct_factor = _DIRECT_GRAMS.get(unit.strip().lower())
    if direct_factor is not None:
        return quantity * direct_factor

    completion = client.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f'Food: "{canonical_name}"\nQuantity: {quantity}\nUnit: "{unit}"',
            },
        ],
        response_format=GramEstimate,
    )

    result = completion.choices[0].message.parsed

    if result is None or result.grams <= 0:
        if verbose:
            print(f"    -> LLM gave no usable gram estimate for '{canonical_name}' ({quantity} {unit})")
        return None

    if verbose:
        print(f"    -> estimated {result.grams:.1f}g for '{canonical_name}' ({quantity} {unit}): {result.reasoning}")

    return result.grams


def calculate_item(item: MatchedItem, verbose: bool = False) -> CalculatedItem:
    if item.nutrition is None:
        return CalculatedItem(raw_name=item.raw_name, canonical_name=item.canonical_name)

    grams = estimate_grams(item.canonical_name, item.quantity, item.unit, verbose=verbose)
    if grams is None:
        return CalculatedItem(
            raw_name=item.raw_name,
            canonical_name=item.canonical_name,
            nutrition=item.nutrition,
        )

    factor = grams / 100.0
    n = item.nutrition

    return CalculatedItem(
        raw_name=item.raw_name,
        canonical_name=item.canonical_name,
        grams=grams,
        calories=n.calories_per_100g * factor,
        protein_g=n.protein_g_per_100g * factor,
        carbs_g=n.carbs_g_per_100g * factor,
        fat_g=n.fat_g_per_100g * factor,
        nutrition=n,
    )


if __name__ == "__main__":
    from models.schemas import NutritionData

    print("Type: <canonical_name>, <quantity>, <unit> (or 'quit' to exit):")
    while True:
        line = input("> ").strip()
        if line.lower() in ("quit", "exit"):
            break
        if not line:
            continue

        try:
            name, qty, unit = [p.strip() for p in line.split(",")]
            grams = estimate_grams(name, float(qty), unit, verbose=True)
            print(f"-> {grams}g" if grams else "-> could not estimate")
        except ValueError:
            print("format: canonical_name, quantity, unit")