from database import engine
from sqlalchemy import text

def add_approval_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE blog_posts ADD COLUMN is_approved BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("Successfully added is_approved column.")
        except Exception as e:
            print(f"Error or column already exists: {e}")

if __name__ == "__main__":
    add_approval_column()
