# Given a food name, find real nutrition data for it.

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from rapidfuzz import fuzz
from typing import Optional, List

from config import USDA_API_KEY
from models.schemas import NutritionData

BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# fuzzy-match score (tweak this value)
CONFIDENCE_THRESHOLD = 55.0

NUTRIENT_NAMES = {
    "calories": "Energy",
    "protein": "Protein",
    "fat": "Total lipid (fat)",
    "carbs": "Carbohydrate, by difference",
}


def _search_usda(query: str, page_size: int = 5) -> List[dict]:
    response = requests.get(
        f"{BASE_URL}/foods/search",
        params={
            "api_key": USDA_API_KEY,
            "query": query,
            "pageSize": page_size,
            "dataType": "Foundation,SR Legacy",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("foods", [])


def _extract_nutrient(food: dict, nutrient_name: str) -> Optional[float]:
    # Pull a single nutrient's amount (per 100g) out of a USDA food record.
    for entry in food.get("foodNutrients", []):
        if entry.get("nutrientName") == nutrient_name:
            return entry.get("value")
    return None


def _to_nutrition_data(food: dict, confidence: float) -> Optional[NutritionData]:
    calories = _extract_nutrient(food, NUTRIENT_NAMES["calories"])
    protein = _extract_nutrient(food, NUTRIENT_NAMES["protein"])
    fat = _extract_nutrient(food, NUTRIENT_NAMES["fat"])
    carbs = _extract_nutrient(food, NUTRIENT_NAMES["carbs"])

    if None in (calories, protein, fat, carbs):
        return None

    return NutritionData(
        fdc_id=food["fdcId"],
        matched_description=food.get("description", ""),
        match_confidence=confidence,
        calories_per_100g=calories,
        protein_g_per_100g=protein,
        carbs_g_per_100g=carbs,
        fat_g_per_100g=fat,
    )


def lookup_nutrition(query: str) -> Optional[NutritionData]:
    
    # Searches USDA for `query`, fuzzy-matches candidates against it
    
    candidates = _search_usda(query)
    if not candidates:
        return None

    # Score each candidate's description against our query text.
    scored = [
        (fuzz.token_sort_ratio(query.lower(), food.get("description", "").lower()), food)
        for food in candidates
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    for score, food in scored:
        if score < CONFIDENCE_THRESHOLD:
            break  # remaining candidates score even lower, no point checking
        result = _to_nutrition_data(food, confidence=score)
        if result is not None:
            return result

    return None


if __name__ == "__main__":
    # Manual test loop, same pattern as ai_parser.py's __main__.
    # Try things like "toast", "chicken breast", "banana".
    print("Type a food name to look up (or 'quit' to exit):")
    while True:
        query = input("> ").strip()
        if query.lower() in ("quit", "exit"):
            break
        if not query:
            continue

        result = lookup_nutrition(query)
        if result is None:
            print(f"No confident match found for '{query}'.")
        else:
            print(result.model_dump_json(indent=2))