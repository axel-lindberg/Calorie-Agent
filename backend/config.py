import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing.")

OPENAI_MODEL = "gpt-4o-mini"

USDA_API_KEY = os.getenv("USDA_API_KEY")

if USDA_API_KEY is None:
    raise ValueError("USDA_API_KEY is missing.")