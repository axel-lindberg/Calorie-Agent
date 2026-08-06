import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Create a .env file in backend/ with "
        "OPENAI_API_KEY=sk-your-key-here, or set it as an environment variable."
    )

OPENAI_MODEL = "gpt-4o-mini"

USDA_API_KEY = os.getenv("USDA_API_KEY")