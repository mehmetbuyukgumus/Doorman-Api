"""
migrate_all.py - Comprehensive safe migration script for production deployments.

This script is idempotent: it checks column/table existence before applying
any ALTER TABLE statement. Running it multiple times is safe.

Called automatically from main.py at startup via ensure_all_migrations().
"""
from sqlalchemy import inspect, text
from database import engine
import logging

logger = logging.getLogger(__name__)


def _log(msg: str):
    """Always-visible output for startup migration steps."""
    print(msg, flush=True)
    logger.info(msg)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _table_exists(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def _ensure_column(inspector, table_name: str, column_name: str, column_type: str):
    if not _table_exists(inspector, table_name):
        _log(f"⚠️  Table '{table_name}' does not exist; skipping column '{column_name}'.")
        return
    if _column_exists(inspector, table_name, column_name):
        # Already exists – silently skip
        return
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
        conn.commit()
    _log(f"✅ Added column '{column_name}' to '{table_name}'.")


def _ensure_table(inspector, table_name: str, create_sql: str):
    if _table_exists(inspector, table_name):
        # Already exists – silently skip
        return
    with engine.connect() as conn:
        conn.execute(text(create_sql))
        conn.commit()
    _log(f"✅ Created table '{table_name}'.")


# ─── Individual migration steps ───────────────────────────────────────────────

def _migrate_blog_posts(inspector):
    """is_approved column – added after initial schema."""
    _ensure_column(inspector, "blog_posts", "is_approved", "BOOLEAN DEFAULT FALSE")


def _migrate_research_listings(inspector):
    """property_type column – added after initial schema."""
    _ensure_column(
        inspector, "research_listings", "property_type",
        "VARCHAR DEFAULT 'apartment_sale'"
    )


def _migrate_concierge_properties(inspector):
    """airbnb_cleaning_fee and max_cleaning_duration – added for cleaning module."""
    _ensure_column(inspector, "concierge_properties", "airbnb_cleaning_fee", "NUMERIC(10, 2)")
    _ensure_column(inspector, "concierge_properties", "max_cleaning_duration", "NUMERIC(4, 1)")


def _migrate_concierge_bookings(inspector):
    """is_block column – added for calendar blocking feature."""
    _ensure_column(inspector, "concierge_bookings", "is_block", "BOOLEAN DEFAULT FALSE")
    # Ensure notes column (some older schemas may be missing it)
    _ensure_column(inspector, "concierge_bookings", "notes", "TEXT")
    # Owner-only deduction (e.g. damages, extra cleaning) — never reduces Doorman's commission.
    _ensure_column(inspector, "concierge_bookings", "other_fee", "NUMERIC(10, 2) DEFAULT 0.0")
    _ensure_column(inspector, "concierge_bookings", "other_fee_note", "TEXT")


def _migrate_cleaners(inspector):
    """hourly_rate column – added for financial tracking."""
    _ensure_column(inspector, "cleaners", "hourly_rate", "NUMERIC(10, 2)")


def _migrate_cleaning_assignments(inspector):
    """Snapshot columns for financial calculations."""
    _ensure_column(inspector, "cleaning_assignments", "hourly_rate", "NUMERIC(10, 2)")
    _ensure_column(inspector, "cleaning_assignments", "max_cleaning_duration", "NUMERIC(4, 1)")
    _ensure_column(inspector, "cleaning_assignments", "airbnb_cleaning_fee", "NUMERIC(10, 2)")


def _migrate_cleaner_transactions(inspector):
    """Full table creation if it doesn't exist (created after initial schema)."""
    _ensure_table(inspector, "cleaner_transactions", """
        CREATE TABLE cleaner_transactions (
            id SERIAL PRIMARY KEY,
            cleaner_id INTEGER NOT NULL REFERENCES cleaners(id) ON DELETE CASCADE,
            property_id INTEGER REFERENCES concierge_properties(id) ON DELETE SET NULL,
            amount NUMERIC(10, 2) NOT NULL,
            type VARCHAR NOT NULL,
            transaction_date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
    """)
    # If table already existed but was created without some columns, ensure them too
    _ensure_column(inspector, "cleaner_transactions", "cleaner_id", "INTEGER")
    _ensure_column(inspector, "cleaner_transactions", "property_id", "INTEGER")
    _ensure_column(inspector, "cleaner_transactions", "amount", "NUMERIC(10, 2)")
    _ensure_column(inspector, "cleaner_transactions", "type", "VARCHAR")
    _ensure_column(inspector, "cleaner_transactions", "transaction_date", "DATE")
    _ensure_column(inspector, "cleaner_transactions", "description", "TEXT")


def _migrate_concierge_reports(inspector):
    """Full table creation if it doesn't exist."""
    _ensure_table(inspector, "concierge_reports", """
        CREATE TABLE concierge_reports (
            id SERIAL PRIMARY KEY,
            property_id INTEGER NOT NULL REFERENCES concierge_properties(id) ON DELETE CASCADE,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            status VARCHAR DEFAULT 'not_sent',
            last_sent_at TIMESTAMP WITH TIME ZONE
        )
    """)


def _migrate_long_term_rentals(inspector):
    """Long-term rental workflow tables."""
    _ensure_table(inspector, "long_term_rental_properties", """
        CREATE TABLE long_term_rental_properties (
            id SERIAL PRIMARY KEY,
            title VARCHAR NOT NULL,
            address VARCHAR,
            owner_name VARCHAR,
            owner_email VARCHAR,
            monthly_rent NUMERIC(10, 2),
            management_fee_percent NUMERIC(5, 2),
            charges NUMERIC(10, 2),
            deposit NUMERIC(10, 2),
            status VARCHAR NOT NULL DEFAULT 'available',
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
    """)
    _ensure_column(inspector, "long_term_rental_properties", "management_fee_percent", "NUMERIC(5, 2)")
    _ensure_table(inspector, "long_term_rental_processes", """
        CREATE TABLE long_term_rental_processes (
            id SERIAL PRIMARY KEY,
            property_id INTEGER NOT NULL REFERENCES long_term_rental_properties(id) ON DELETE CASCADE,
            status VARCHAR NOT NULL DEFAULT 'visits',
            selected_candidate_id INTEGER,
            lease_start_date DATE,
            lease_end_date DATE,
            contract_signed_at DATE,
            ended_at DATE,
            end_reason TEXT,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
    """)
    _ensure_table(inspector, "long_term_rental_candidates", """
        CREATE TABLE long_term_rental_candidates (
            id SERIAL PRIMARY KEY,
            process_id INTEGER NOT NULL REFERENCES long_term_rental_processes(id) ON DELETE CASCADE,
            full_name VARCHAR NOT NULL,
            email VARCHAR,
            phone VARCHAR,
            visit_date DATE,
            visit_time VARCHAR,
            status VARCHAR NOT NULL DEFAULT 'visit_planned',
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
    """)
    _ensure_column(inspector, "long_term_rental_candidates", "visit_time", "VARCHAR")
    _ensure_table(inspector, "long_term_rental_payments", """
        CREATE TABLE long_term_rental_payments (
            id SERIAL PRIMARY KEY,
            process_id INTEGER NOT NULL REFERENCES long_term_rental_processes(id) ON DELETE CASCADE,
            due_date DATE NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'pending',
            paid_at DATE,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
    """)
    _ensure_table(inspector, "long_term_rental_documents", """
        CREATE TABLE long_term_rental_documents (
            id SERIAL PRIMARY KEY,
            process_id INTEGER REFERENCES long_term_rental_processes(id) ON DELETE CASCADE,
            property_id INTEGER REFERENCES long_term_rental_properties(id) ON DELETE CASCADE,
            candidate_id INTEGER REFERENCES long_term_rental_candidates(id) ON DELETE SET NULL,
            file_key VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            mime_type VARCHAR,
            size INTEGER,
            category VARCHAR NOT NULL DEFAULT 'other',
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
    """)
    _ensure_column(inspector, "long_term_rental_documents", "candidate_id", "INTEGER")
    _ensure_column(inspector, "long_term_rental_documents", "description", "TEXT")
    _ensure_column(
        inspector, "long_term_rental_documents", "property_id",
        "INTEGER REFERENCES long_term_rental_properties(id) ON DELETE CASCADE"
    )
    _migrate_long_term_rental_property_documents(inspector)


def _migrate_long_term_rental_property_documents(inspector):
    """Apartment documents (DPE, inventory, etc.) belong to the apartment, not a
    single rental process. Allow process_id to be null and move any existing
    'listing' category documents from their process onto the apartment itself."""
    if not _table_exists(inspector, "long_term_rental_documents"):
        return
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE long_term_rental_documents ALTER COLUMN process_id DROP NOT NULL"
            ))
            result = conn.execute(text("""
                UPDATE long_term_rental_documents AS d
                SET property_id = p.property_id, process_id = NULL
                FROM long_term_rental_processes AS p
                WHERE d.process_id = p.id AND d.category = 'listing' AND d.property_id IS NULL
            """))
            conn.commit()
            if result.rowcount:
                _log(f"✅ Moved {result.rowcount} apartment document(s) from process to apartment level.")
    except Exception as exc:
        _log(f"⚠️  Failed to migrate long-term rental property documents: {exc}")


def _populate_cleaning_assignment_snapshots():
    """Back-fill snapshot columns for existing cleaning_assignments rows."""
    try:
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
        _log("✅ Back-filled cleaning_assignments snapshot columns.")
    except Exception as exc:
        _log(f"⚠️  Failed to back-fill cleaning assignment snapshots: {exc}")


def _normalize_blocked_concierge_bookings():
    """Keep calendar blocks distinct from revenue reservations."""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE concierge_bookings
                SET
                    source = 'block',
                    platform = NULL,
                    price = 0,
                    platform_fee = 0,
                    commission_rate = 0,
                    owner_payout = 0,
                    doorman_commission = 0,
                    guest_name = 'Blocked',
                    summary = COALESCE(NULLIF(summary, ''), 'Blocked Period')
                WHERE is_block = TRUE
            """))
            conn.commit()
        _log("✅ Normalized blocked concierge bookings.")
    except Exception as exc:
        _log(f"⚠️  Failed to normalize blocked concierge bookings: {exc}")


# ─── Entry point ──────────────────────────────────────────────────────────────

def ensure_all_migrations():
    """
    Run all schema migrations in safe, idempotent order.
    Intended to be called once at application startup (before the FastAPI app is created).
    """
    _log("🔄 Running schema migrations...")
    try:
        inspector = inspect(engine)

        _migrate_blog_posts(inspector)
        _migrate_research_listings(inspector)
        _migrate_concierge_properties(inspector)
        _migrate_concierge_bookings(inspector)
        _migrate_cleaners(inspector)
        _migrate_cleaning_assignments(inspector)
        _migrate_cleaner_transactions(inspector)
        _migrate_concierge_reports(inspector)
        _migrate_long_term_rentals(inspector)
        _populate_cleaning_assignment_snapshots()
        _normalize_blocked_concierge_bookings()

        _log("✅ All schema migrations completed successfully.")
    except Exception as exc:
        _log(f"❌ Migration failed: {exc}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_all_migrations()
