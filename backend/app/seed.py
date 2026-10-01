from sqlalchemy import select

from app.auth import hash_password

from app.database import SessionLocal

from app.models import Category, Thread, User

categories = [

    {

        "name": "Artificial Intelligence",

        "slug": "artificial-intelligence",

        "description": "AI agents, LLMs, machine learning and automation.",

    },

    {

        "name": "Development",

        "slug": "development",

        "description": "Web, mobile, backend and software engineering.",

    },

    {

        "name": "Data & Cloud",

        "slug": "data-cloud",

        "description": "Databases, cloud infrastructure and distributed systems.",

    },

    {

        "name": "Security",

        "slug": "security",

        "description": "Cybersecurity, application security and privacy.",

    },

    {
        "name": "Telecom & Networking",
        "slug": "telecom-networking",
        "description": "Core networks, radio access, IP transport, operations, security, and telecom power.",
    },

]

telecom_subcategories = [
    ("Core Network", "core-network", [
        ("EPC / 4G Core", "epc-4g-core"),
        ("5G Core", "5g-core"),
        ("IMS", "ims"),
        ("Signaling", "signaling"),
    ]),
    ("Radio Access Network", "radio-access-network", [
        ("2G / GSM", "2g-gsm"),
        ("3G / UMTS", "3g-umts"),
        ("4G / LTE", "4g-lte"),
        ("5G / NR", "5g-nr"),
    ]),
    ("IP & Transport", "ip-transport", [
        ("IP Networking", "ip-networking"),
        ("MPLS", "mpls"),
        ("Microwave", "microwave"),
        ("Fiber", "fiber"),
        ("SDN / SD-WAN", "sdn-sd-wan"),
    ]),
    ("Network Operations", "network-operations", [
        ("NOC", "noc"),
        ("Monitoring", "monitoring"),
        ("Troubleshooting", "troubleshooting"),
        ("Performance", "performance"),
        ("Network Automation", "network-automation"),
    ]),
    ("Telecom Security", "telecom-security", [
        ("Network Security", "network-security"),
        ("Signaling Security", "signaling-security"),
        ("4G / 5G Security", "4g-5g-security"),
        ("Fraud & Abuse", "fraud-abuse"),
    ]),
    ("Telecom Power", "telecom-power", [
        ("Rectifier", "rectifier"),
        ("Battery", "battery"),
        ("Generator", "generator"),
        ("Solar", "solar"),
        ("Site Power", "site-power"),
    ]),
]

threads = [

    {

        "title": "How are you building production AI agents?",

        "slug": "how-are-you-building-production-ai-agents",

        "content": "Share your architecture, lessons and production experience building AI agents.",

        "category_slug": "artificial-intelligence",

    },

    {

        "title": "Best architecture for a scalable Next.js application",

        "slug": "best-architecture-for-scalable-nextjs",

        "content": "Discuss scalable Next.js architectures for modern applications.",

        "category_slug": "development",

    },

    {

        "title": "PostgreSQL vs distributed databases for SaaS",

        "slug": "postgresql-vs-distributed-databases",

        "content": "What database architecture are you using for your SaaS products?",

        "category_slug": "data-cloud",

    },

    {

        "title": "What does your production deployment stack look like?",

        "slug": "production-deployment-stack",

        "content": "Share your deployment, CI/CD and infrastructure stack.",

        "category_slug": "security",

    },

]

def seed():

    db = SessionLocal()

    try:

        # --------------------------------------------------

        # Seed user

        # --------------------------------------------------

        user = db.scalar(

            select(User).where(

                User.username == "apexive"

            )

        )

        if not user:

            user = User(

                username="apexive",

                email="admin@apexive.ai",

                password_hash=hash_password(

                    "ChangeThisPassword123!"

                ),

                display_name="Apexive",

                bio="Apexive Community administrator.",

                is_active=True,

                is_admin=True,

            )

            db.add(user)

            db.flush()

        # --------------------------------------------------

        # Categories

        # --------------------------------------------------

        category_map = {}

        for item in categories:

            category = db.scalar(

                select(Category).where(

                    Category.slug == item["slug"]

                )

            )

            if not category:

                category = Category(**item)

                db.add(category)

                db.flush()

            category_map[item["slug"]] = category

        telecom = category_map["telecom-networking"]
        for section_name, section_slug, children in telecom_subcategories:
            section = db.scalar(select(Category).where(Category.slug == section_slug))
            if not section:
                section = Category(
                    name=section_name,
                    slug=section_slug,
                    description=f"{section_name} topics in Telecom & Networking.",
                    parent_id=telecom.id,
                )
                db.add(section)
                db.flush()
            for child_name, child_slug in children:
                child = db.scalar(select(Category).where(Category.slug == child_slug))
                if not child:
                    db.add(Category(
                        name=child_name,
                        slug=child_slug,
                        description=f"{child_name} discussions in {section_name}.",
                        parent_id=section.id,
                    ))

        # --------------------------------------------------

        # Threads

        # --------------------------------------------------

        for item in threads:

            existing = db.scalar(

                select(Thread).where(

                    Thread.slug == item["slug"]

                )

            )

            if existing:

                continue

            category = category_map[

                item["category_slug"]

            ]

            thread = Thread(

                title=item["title"],

                slug=item["slug"],

                content=item["content"],

                category_id=category.id,

                author_id=user.id,

            )

            db.add(thread)

        db.commit()

        print(
            "Apexive Community seed completed successfully."

        )

    finally:

        db.close()

if __name__ == "__main__":

    seed()