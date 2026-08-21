CREATE TABLE IF NOT EXISTS meals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,  -- single-user for now
    raw_text TEXT NOT NULL,              -- user input
    logged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meal_items (
    id SERIAL PRIMARY KEY,
    meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    raw_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    grams REAL,
    calories REAL,
    protein_g REAL,
    carbs_g REAL,
    fat_g REAL,
    fdc_id INTEGER,              -- USDA match, nullable if no match found
    match_confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_meals_user_logged_at ON meals (user_id, logged_at);