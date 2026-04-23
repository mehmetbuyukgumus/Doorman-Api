import os
import database, models, auth
from dotenv import load_dotenv

load_dotenv()

def reset_and_init():
    admin_email = os.getenv("ADMIN_EMAIL", "admin@doorman.com")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD environment variable is not set. Cannot create admin user without a secure password.")

    print("Dropping all tables...")
    database.Base.metadata.drop_all(bind=database.engine)
    print("Creating all tables...")
    database.Base.metadata.create_all(bind=database.engine)
    
    db = database.SessionLocal()
    try:
        hashed_pw = auth.get_password_hash(admin_password)
        admin_user = models.User(
            email=admin_email,
            hashed_password=hashed_pw,
            full_name="System Admin",
            role="superuser",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Database reset and admin user created: {admin_email}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_and_init()
