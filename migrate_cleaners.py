from sqlalchemy import inspect, text

from database import engine


def ensure_cleaner_hourly_rate_column():
    inspector = inspect(engine)
    if not inspector.has_table("cleaners"):
        print("cleaners table does not exist; skipping hourly_rate migration.")
    elif _column_exists(inspector, "cleaners", "hourly_rate"):
        print("cleaners hourly_rate column already exists.")
    else:
        _add_column("cleaners", "hourly_rate", "NUMERIC(10, 2)")

    _ensure_column(
        inspector,
        "concierge_properties",
        "airbnb_cleaning_fee",
        "NUMERIC(10, 2)",
    )
    _ensure_column(
        inspector,
        "concierge_properties",
        "max_cleaning_duration",
        "NUMERIC(4, 1)",
    )
    _ensure_column(
        inspector,
        "cleaning_assignments",
        "hourly_rate",
        "NUMERIC(10, 2)",
    )
    _ensure_column(
        inspector,
        "cleaning_assignments",
        "max_cleaning_duration",
        "NUMERIC(4, 1)",
    )
    _ensure_column(
        inspector,
        "cleaning_assignments",
        "airbnb_cleaning_fee",
        "NUMERIC(10, 2)",
    )
    _populate_cleaning_assignment_snapshots()


def _column_exists(inspector, table_name, column_name):
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _ensure_column(inspector, table_name, column_name, column_type):
    if not inspector.has_table(table_name):
        print(f"{table_name} table does not exist; skipping {column_name} migration.")
        return
    if _column_exists(inspector, table_name, column_name):
        print(f"{table_name} {column_name} column already exists.")
        return
    _add_column(table_name, column_name, column_type)


def _add_column(table_name, column_name, column_type):
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
        conn.commit()
        print(f"Successfully added {column_name} column to {table_name}.")


def _populate_cleaning_assignment_snapshots():
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE cleaning_assignments AS ca
            SET hourly_rate = c.hourly_rate
            FROM cleaners AS c
            WHERE ca.cleaner_id = c.id AND ca.hourly_rate IS NULL
        """))
        conn.execute(text("""
            UPDATE cleaning_assignments AS ca
            SET max_cleaning_duration = cp.max_cleaning_duration
            FROM concierge_properties AS cp
            WHERE ca.property_id = cp.id AND ca.max_cleaning_duration IS NULL
        """))
        conn.execute(text("""
            UPDATE cleaning_assignments AS ca
            SET airbnb_cleaning_fee = cp.airbnb_cleaning_fee
            FROM concierge_properties AS cp
            WHERE ca.property_id = cp.id AND ca.airbnb_cleaning_fee IS NULL
        """))
        conn.commit()
        print("Successfully populated cleaning assignment snapshots.")


if __name__ == "__main__":
    ensure_cleaner_hourly_rate_column()
