import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def check_tables():
    print("--- Database Table Check ---")
    
    # Check buyers table
    try:
        buyers_count = db.execute(text("SELECT COUNT(*) FROM buyers")).scalar()
        print(f"Table 'buyers' count: {buyers_count}")
        if buyers_count > 0:
            sample = db.execute(text("SELECT email FROM buyers LIMIT 1")).scalar()
            print(f"Sample email from buyers: {sample}")
    except Exception as e:
        print(f"Error checking buyers: {e}")

    # Check investors table
    try:
        investors_count = db.execute(text("SELECT COUNT(*) FROM investors")).scalar()
        print(f"Table 'investors' count: {investors_count}")
        if investors_count > 0:
            sample = db.execute(text("SELECT email FROM investors LIMIT 1")).scalar()
            print(f"Sample email from investors: {sample}")
    except Exception as e:
        print(f"Error checking investors: {e}")

if __name__ == "__main__":
    check_tables()
    db.close()
