from sqlalchemy import inspect, text

from database import engine


def ensure_cleaner_hourly_rate_column():
    inspector = inspect(engine)
    if not inspector.has_table("cleaners"):
        print("cleaners table does not exist; skipping hourly_rate migration.")
        return

    columns = {column["name"] for column in inspector.get_columns("cleaners")}
    if "hourly_rate" in columns:
        print("cleaners hourly_rate column already exists.")
        return

    with engine.connect() as conn:
        conn.execute(
            text("ALTER TABLE cleaners ADD COLUMN hourly_rate NUMERIC(10, 2)")
        )
        conn.commit()
        print("Successfully added hourly_rate column to cleaners.")


if __name__ == "__main__":
    ensure_cleaner_hourly_rate_column()
