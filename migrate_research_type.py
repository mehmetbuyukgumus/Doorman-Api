import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to local compose default if running manually outside container
    DATABASE_URL = "postgresql://doorman_user:d0874d1fd7dff3edbae1b2d58bc96644@localhost:5432/doorman_db"

engine = create_engine(DATABASE_URL)

def run_migration():
    print(f"Connecting to database to check research_listings columns...")
    with engine.connect() as conn:
        try:
            # Check if property_type column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='research_listings' AND column_name='property_type'"))
            exists = result.fetchone()
            if not exists:
                print("Column 'property_type' does not exist in 'research_listings'. Adding column...")
                conn.execute(text("ALTER TABLE research_listings ADD COLUMN property_type VARCHAR DEFAULT 'apartment_sale'"))
                conn.commit()
                print("Column 'property_type' successfully added to 'research_listings'.")
            else:
                print("Column 'property_type' already exists in 'research_listings'.")
        except Exception as e:
            print(f"Error executing migration: {e}")

if __name__ == "__main__":
    run_migration()
