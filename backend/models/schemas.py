# Data shapes shared across the pipeline.


from pydantic import BaseModel, Field
from typing import List


class FoodItem(BaseModel):
    raw_name: str = Field(description="The food name as mentioned by the user")

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
    
class NutritionData(BaseModel):
    # Nutrient values for a matched food, always per 100g.
 
    fdc_id: int
    matched_description: str  # the actual USDA food name we matched to
    match_confidence: float  # 0-100 fuzzy match score, for debugging/thresholding
 
    calories_per_100g: float
    protein_g_per_100g: float
    carbs_g_per_100g: float
    fat_g_per_100g: float