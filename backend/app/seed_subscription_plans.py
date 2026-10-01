from decimal import Decimal

from app.database import SessionLocal

from app.models.subscription import SubscriptionPlan

PLANS = [

    {

        "product_key": "trademark",

        "name": "Trademark Conflict",

        "description": "AI-powered trademark conflict detection and analysis.",

        "monthly_price": Decimal("249.00"),

        "currency": "USD",

        "billing_cycle": "monthly",

    },

    {

        "product_key": "network",

        "name": "Network Design & Quotation",

        "description": "Network planning, VLAN, IP planning, ACL, Cisco configuration and quotation.",

        "monthly_price": Decimal("199.00"),

        "currency": "USD",

        "billing_cycle": "monthly",

    },

    {

        "product_key": "workforce",

        "name": "Autonomous Workforce",

        "description": "Governed autonomous enterprise AI workforce and workflow execution.",

        "monthly_price": Decimal("299.00"),

        "currency": "USD",

        "billing_cycle": "monthly",

    },

    {

        "product_key": "trademark_workforce",

        "name": "Trademark + Workforce",

        "description": "Trademark Conflict and Autonomous Workforce combined subscription.",

        "monthly_price": Decimal("499.00"),

        "currency": "USD",

        "billing_cycle": "monthly",

    },

    {

        "product_key": "telecom",

        "name": "Telecom Network",

        "description": "Telecom network engineering and operational intelligence platform.",

        "monthly_price": Decimal("399.00"),

        "currency": "USD",

        "billing_cycle": "monthly",

    },

]

def seed():

    db = SessionLocal()

    try:

        for data in PLANS:

            existing = (

                db.query(SubscriptionPlan)

                .filter(

                    SubscriptionPlan.product_key

                    == data["product_key"]

                )

                .first()

            )

            if existing:

                existing.name = data["name"]

                existing.description = data["description"]

                existing.monthly_price = data["monthly_price"]

                existing.currency = data["currency"]

                existing.billing_cycle = data["billing_cycle"]

                existing.is_active = True

                print(

                    f"UPDATED: {data['product_key']}"

                )

                continue

            plan = SubscriptionPlan(

                **data,

                is_active=True,

            )

            db.add(plan)

            print(

                f"CREATED: {data['product_key']}"

            )

        db.commit()

        print()

        print("Subscription plans seeded successfully.")

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()

if __name__ == "__main__":

    seed()