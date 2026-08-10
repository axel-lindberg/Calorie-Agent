import json 
from typing import List

from services.ai_parser import parse_meal_text
from services.nutrition_lookup import lookup_nutrition
from models.schemas import MatchedItem

def parse_and_lookup(text: str, verbose: bool = False) -> List[MatchedItem]:
    parsed = parse_meal_text(text)
    
    results = []
    for item in parsed.items:
        nutrition = lookup_nutrition(item.canonical_name, verbose=verbose)
        
        results.append(
            MatchedItem(
                raw_name=item.raw_name,
                canonical_name=item.canonical_name,
                quantity=item.quantity,
                unit=item.unit,
                nutrition=nutrition,
            )
        )
    
    return results

if __name__ == "__main__":
    print("Describe a meal (or 'quit' to exit):")
    while True:
        text = input("> ").strip()
        if text.lower() in ("quit", "exit"):
            break
        if not text:
            continue
 
        results = parse_and_lookup(text, verbose=True)
        print(json.dumps([r.model_dump() for r in results], indent=2))
 
        for r in results:
            if r.nutrition is None:
                print(f"no confident nutrition match for '{r.raw_name}' ({r.canonical_name})")