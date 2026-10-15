
import os
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

load_dotenv()

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not configured.")

test_url = make_url(database_url).set(
    database="apexive_migration_test"
)

engine = create_engine(test_url, pool_pre_ping=True)

PLANS = [
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
        "description": "Governed autonomous enterprise AI workforce and workflow execution.",
        "monthly_price": Decimal("299.00"),
        "currency": "USD",
        "billing_cycle": "monthly",
    },
]


def seed():
    with engine.begin() as connection:
        db_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if db_name != "apexive_migration_test":
            raise RuntimeError(
                f"Wrong database: {db_name}. Nothing was seeded."
            )

        columns = {
            column["name"]
            for column in __import__("sqlalchemy").inspect(
                connection
            ).get_columns("subscription_plans")
        }

        required = {
            "code",
            "product_key",
            "name",
            "description",
            "monthly_price",
            "currency",
            "billing_cycle",
            "is_active",
        }

        if not required.issubset(columns):
            raise RuntimeError(
                f"Missing subscription plan columns: {required - columns}"
            )

        print("Verified database:", db_name)

    # Use the current ORM only after checking the test database schema.
    from app.models.subscription import SubscriptionPlan

    with Session(engine) as db:
        for data in PLANS:
            existing = (
                db.query(SubscriptionPlan)
                .filter(
                    SubscriptionPlan.product_key == data["product_key"]
                )
                .first()
            )

            if existing:
                existing.code = data["code"]
                existing.name = data["name"]
                existing.description = data["description"]
                existing.monthly_price = data["monthly_price"]
                existing.currency = data["currency"]
                existing.billing_cycle = data["billing_cycle"]
                existing.is_active = True
                print("UPDATED:", data["product_key"])
            else:
                db.add(
                    SubscriptionPlan(
                        **data,
                        is_active=True,
                    )
                )
                print("CREATED:", data["product_key"])

        db.commit()

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT product_key, name, monthly_price, currency, "
                "billing_cycle, is_active "
                "FROM subscription_plans "
                "WHERE product_key IN ('trademark', 'workforce') "
                "ORDER BY product_key"
            )
        )
        print("\nVerified plans:")
        for row in rows:
            print(dict(row._mapping))


if __name__ == "__main__":
    try:
        seed()
    finally:
        engine.dispose()
