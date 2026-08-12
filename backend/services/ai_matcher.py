import sys
import os
 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from models.schemas import FoodMatchSelection
 
client = OpenAI(api_key=OPENAI_API_KEY)
 
SYSTEM_PROMPT = """\
You are matching a user's food description to an entry in a nutrition \
database. You will be given the food the user mentioned and a numbered \
list of candidate database entries.
 
Select the candidate that is genuinely the same food as what the user \
described. Differences in cooking method (raw vs cooked), cut, or minor \
descriptive detail are acceptable to match. A different food entirely - \
for example a sausage/processed product when the user meant a plain cut \
of meat, or an unrelated ingredient that just has a similar name - must \
NOT be selected.
 
If none of the candidates are genuinely the same food, return null for \
selected_fdc_id.
"""

