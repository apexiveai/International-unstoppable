from datetime import datetime

from app.database import SessionLocal

from app.models import User

from app.auth import hash_password

def seed_admin():

    db = SessionLocal()

    try:

        existing = db.query(User).filter(User.username == "apexive").first()

        if existing:

            existing.is_admin = True

            existing.is_active = True

            if hasattr(existing, "email_verified_at") and existing.email_verified_at is None:

                existing.email_verified_at = datetime.utcnow()

            db.commit()

            print("Admin user already exists.")

            print(f"Username: {existing.username}")

            print(f"Email: {existing.email}")

            print("Admin: True")

            return

        admin = User(

            username="apexive",

            email="admin@apexive.ai",

            password_hash=hash_password("ChangeThisPassword123!"),

            display_name="Apexive",

            bio="Apexive Community administrator.",

            is_active=True,

            is_admin=True,

            email_verified_at=datetime.utcnow(),

        )

        db.add(admin)

        db.commit()

        db.refresh(admin)

        print("========================================")

        print("Apexive Community admin created")

        print("========================================")

        print(f"ID:       {admin.id}")

        print(f"Username: {admin.username}")

        print(f"Email:    {admin.email}")

        print("Password: ChangeThisPassword123!")

        print("Admin:    True")

        print("Verified: True")

        print("========================================")

    finally:

        db.close()

if __name__ == "__main__":

    seed_admin()