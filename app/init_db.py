import os
from . import db as database, models
from .core import auth
from dotenv import load_dotenv

load_dotenv()

def init_admin():
    admin_email = os.getenv("ADMIN_EMAIL", "admin@doorman.com")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD environment variable is not set. Cannot create admin user without a secure password.")

    db = database.SessionLocal()
    try:
        exists = db.query(models.User).filter(models.User.email == admin_email).first()
        if not exists:
            hashed_pw = auth.get_password_hash(admin_password)
            admin_user = models.User(
                email=admin_email,
                hashed_password=hashed_pw,
                full_name="System Admin",
                role="superuser",
                is_active=True,
                must_change_password=False
            )
            db.add(admin_user)
            db.commit()
            print(f"Admin user created: {admin_email}")
        else:
            print("Admin user already exists.")
    finally:
        db.close()

if __name__ == "__main__":
    init_admin()
