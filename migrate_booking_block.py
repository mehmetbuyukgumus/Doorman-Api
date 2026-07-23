import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to local compose default
    DATABASE_URL = "postgresql://doorman_user:d0874d1fd7dff3edbae1b2d58bc96644@localhost:5432/doorman_db"

engine = create_engine(DATABASE_URL)

def run_migration():
    print(f"Connecting to database to check concierge_bookings columns...")
    with engine.connect() as conn:
        try:
            # Check if is_block column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='concierge_bookings' AND column_name='is_block'"))
            exists = result.fetchone()
            if not exists:
                print("Column 'is_block' does not exist in 'concierge_bookings'. Adding column...")
                conn.execute(text("ALTER TABLE concierge_bookings ADD COLUMN is_block BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("Column 'is_block' successfully added to 'concierge_bookings'.")
            else:
                print("Column 'is_block' already exists in 'concierge_bookings'.")
        except Exception as e:
            print(f"Error executing migration: {e}")

if __name__ == "__main__":
    run_migration()
