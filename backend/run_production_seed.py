
import os
from getpass import getpass
from decimal import Decimal

# Set the production DATABASE_URL BEFORE importing app.database.
database_url = getpass("Paste the NEW Render External Database URL: ").strip()
if not database_url:
    raise SystemExit("ERROR: DATABASE_URL is required.")

os.environ["DATABASE_URL"] = database_url

from app.database import engine, SessionLocal
from app.models.subscription import SubscriptionPlan

EXPECTED_DATABASE = "apexive_admin_eisn"

if engine.url.database != EXPECTED_DATABASE:
    raise SystemExit(
        f"SAFETY STOP: Connected database is {engine.url.database!r}, "
        f"not {EXPECTED_DATABASE!r}. No changes made."
    )

if not engine.url.host or engine.url.host.lower() in {
    "localhost", "127.0.0.1", "::1"
}:
    raise SystemExit("SAFETY STOP: This does not look like a remote database.")

print("\nProduction connection verified.")
print("Database:", engine.url.database)
print("Host:", engine.url.host)
print("\nThis script will create/update only two plans.")
print("It will NOT deactivate other subscription plans.")

confirmation = input(
    "\nType SEED_PRODUCTION to continue: "
).strip()

if confirmation != "SEED_PRODUCTION":
    raise SystemExit("Cancelled. No changes made.")

plans = [
    {
        "code": "TRADEMARK_CONFLICT",
        "product_key": "trademark",
        "name": "Trademark Conflict",
        "description": "AI-powered trademark conflict detection and analysis.",
        "monthly_price": Decimal("7000000.00"),
        "currency": "MMK",
        "billing_cycle": "monthly",
    },
    {
        "code": "AUTONOMOUS_WORKFORCE",
        "product_key": "workforce",
        "name": "Autonomous Workforce",
        "description": (
            "Governed autonomous enterprise AI workforce "
            "and workflow execution."
        ),
        "monthly_price": Decimal("299.00"),
        "currency": "USD",
        "billing_cycle": "monthly",
    },
]

db = SessionLocal()

try:
    for data in plans:
        existing = (
            db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.product_key == data["product_key"]
            )
            .first()
        )

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            existing.is_active = True
            print("UPDATED:", data["product_key"])
        else:
            db.add(SubscriptionPlan(**data, is_active=True))
            print("CREATED:", data["product_key"])

    db.commit()
    print("\nSUCCESS: Production subscription plans seeded.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
    engine.dispose()
