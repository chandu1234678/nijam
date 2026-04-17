from database import engine
import sqlalchemy as sa

with engine.begin() as conn:
    conn.execute(sa.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS tier VARCHAR DEFAULT 'free'"))
    print("Tier column added successfully")
