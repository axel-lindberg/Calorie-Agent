# Given a food name, find real nutrition data for it via USDA FoodData Central.

import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from rapidfuzz import fuzz
from typing import Optional, List

from config import USDA_API_KEY
from models.schemas import NutritionData

BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# Below this score, we don't trust the result enough to auto-accept it.
CONFIDENCE_THRESHOLD = 60.0

# Bonuses/penalties layered on top of the base fuzzy score.
RAW_BONUS = 20
COOKING_PENALTY = 15
PROCESSING_PENALTY = 20

# Foundation Foods use "Energy (Atwater General/Specific Factors)" instead
# of plain "Energy" (which SR Legacy uses) — try each name in order.
NUTRIENT_NAMES = {
    "calories": ["Energy", "Energy (Atwater General Factors)", "Energy (Atwater Specific Factors)"],
    "protein": ["Protein"],
    "fat": ["Total lipid (fat)"],
    "carbs": ["Carbohydrate, by difference"],
}

COOKING_TERMS = {
    "cooked", "boiled", "fried", "grilled", "roasted", "baked",
    "steamed", "smoked", "broiled", "sauteed",
}

PROCESSING_TERMS = {
    "breaded", "battered", "nugget", "patty", "roll", "sausage",
}


def _tokenize(text: str) -> set:
    return set(re.findall(r"[a-z]+", text.lower()))

#change page_size to get more items
def _search_usda(query: str, page_size: int = 15) -> List[dict]:
    # dataType must be a list, not a comma-string — the API treats it as an
    # array param and silently ignores a comma-joined string, letting
    # Branded results slip through.
    response = requests.get(
        f"{BASE_URL}/foods/search",
        params={
            "api_key": USDA_API_KEY,
            "query": query,
            "pageSize": page_size,
            "dataType": ["Foundation", "SR Legacy"],
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("foods", [])


def _extract_nutrient(food: dict, nutrient_names: List[str]) -> Optional[float]:
    entries = food.get("foodNutrients", [])
    for name in nutrient_names:
        for entry in entries:
            if entry.get("nutrientName") == name:
                return entry.get("value")
    return None


def _to_nutrition_data(
    food: dict, confidence: float, verbose: bool = False
) -> Optional[NutritionData]:
    calories = _extract_nutrient(food, NUTRIENT_NAMES["calories"])
    protein = _extract_nutrient(food, NUTRIENT_NAMES["protein"])
    fat = _extract_nutrient(food, NUTRIENT_NAMES["fat"])
    carbs = _extract_nutrient(food, NUTRIENT_NAMES["carbs"])

    missing = [n for n, v in {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs}.items() if v is None]
    if missing:
        if verbose:
            print(f"    -> SKIPPED '{food.get('description')}' [{food.get('dataType')}]: missing {missing}")
        return None

    return NutritionData(
        fdc_id=food["fdcId"],
        matched_description=food.get("description", ""),
        match_confidence=confidence,
        calories_per_100g=max(0.0, calories),
        protein_g_per_100g=max(0.0, protein),
        carbs_g_per_100g=max(0.0, carbs),
        fat_g_per_100g=max(0.0, fat),
    )


def calculate_score(query: str, food: dict) -> float:
    description = food.get("description", "")

    query_lower = query.lower()
    description_lower = description.lower()

    score = fuzz.token_sort_ratio(query_lower, description_lower)

    query_tokens = _tokenize(query_lower)
    description_tokens = _tokenize(description_lower)

    user_specified_cooking = bool(query_tokens & COOKING_TERMS)
    if not user_specified_cooking:
        if "raw" in description_tokens or "uncooked" in description_tokens:
            score += RAW_BONUS

    for term in COOKING_TERMS & description_tokens:
        if term not in query_tokens:
            score -= COOKING_PENALTY

    for term in PROCESSING_TERMS & description_tokens:
        if term not in query_tokens:
            score -= PROCESSING_PENALTY

    return score


def lookup_nutrition(query: str, verbose: bool = False) -> Optional[NutritionData]:
    candidates = _search_usda(query)
    if not candidates:
        return None

    scored = [(calculate_score(query, food), food) for food in candidates]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    if verbose:
        for score, food in scored:
            print(f"{score:5.1f}  |  [{food.get('dataType')}]  {food.get('description', '')}")

    for score, food in scored:
        if score < CONFIDENCE_THRESHOLD:
            break
        result = _to_nutrition_data(food, confidence=score, verbose=verbose)
        if result is not None:
            return result

    return None


if __name__ == "__main__":
    print("Type a food name to look up (or 'quit' to exit):")
    while True:
        query = input("> ").strip()
        if query.lower() in ("quit", "exit"):
            break
        if not query:
            continue

        result = lookup_nutrition(query, verbose=True)
        if result is None:
            print(f"No confident match found for '{query}'.")
        else:
            print(result.model_dump_json(indent=2))