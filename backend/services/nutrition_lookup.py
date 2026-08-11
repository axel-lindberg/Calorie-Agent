# Given a food name, find real nutrition data for it via USDA FoodData Central.

import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from rapidfuzz import fuzz, utils
from typing import Optional, List

from config import USDA_API_KEY
from models.schemas import NutritionData

BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# CONFIDENCE_THRESHOLD = 40.0

NUTRIENT_NAMES = {
    "calories": ["Energy", "Energy (Atwater General Factors)", "Energy (Atwater Specific Factors)"],
    "protein": ["Protein"],
    "fat": ["Total lipid (fat)"],
    "carbs": ["Carbohydrate, by difference"],
}


def _tokenize(text: str) -> set:
    return set(re.findall(r"[a-z]+", text.lower()))

#change page_size to get more items
def _search_usda(query: str, page_size: int = 25) -> List[dict]:
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


def _to_nutrition_data(food: dict, confidence: float, verbose: bool = False) -> Optional[NutritionData]:
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
    
def _has_required_nutrients(food: dict) -> bool:
    return all (_extract_nutrient(food, NUTRIENT_NAMES[n]) is not None 
                for n in ("calories", "protein", "fat", "carbs"))
    
def _pre_filter(query: str, foods: List[dict], limit_num: int, verbose: bool = False) -> List[dict]:
    scored = []
    
    for food in foods:
        description = food.get("description", "")
        score = fuzz.token_sort_ratio(query, description, processor=utils.default_process)
        scored.append((score, food))
                 
    scored.sort(key=lambda pair: pair[0], reverse=True)
    
    if verbose:
            print(f"{score:5.1f} | {description}")
    
    hasNutrients = [(score, food) for score, food in scored if _has_required_nutrients(food)]
    return hasNutrients[:limit_num]


def lookup_nutrition(query: str, verbose = False) -> Optional[NutritionData]:
    candidates = _search_usda(query)
    if not candidates:
        return None
            
    filtered_candidates = _pre_filter(query, candidates, 10, False)
    
    if verbose:
        for score, food in filtered_candidates:
            print(f"{score:5.1f} | {food.get('description','')}")  

    #returns first result with complete nutrional data
    for score, candidate in filtered_candidates:
        result = _to_nutrition_data(candidate, confidence=score, verbose=False)
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

        result = lookup_nutrition(query, True)
      
        if result is None:
            print(f"No confident match found for '{query}'.")
        else:
            print(result.model_dump_json(indent=2))