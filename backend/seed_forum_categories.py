from app.database import SessionLocal

from app.models.category import Category

CATEGORIES = [

    {

        "name": "Security",

        "slug": "security",

        "description": "Cybersecurity, application security, identity, privacy, vulnerabilities, and security engineering.",

    },

    {

        "name": "Data & Cloud",

        "slug": "data-cloud",

        "description": "Cloud computing, databases, data engineering, DevOps, infrastructure, and distributed systems.",

    },

    {

        "name": "Development",

        "slug": "development",

        "description": "Frontend, backend, full-stack, mobile development, APIs, programming, and developer tools.",

    },

    {

        "name": "Artificial Intelligence",

        "slug": "artificial-intelligence",

        "description": "AI, machine learning, LLMs, AI agents, RAG, knowledge systems, and computer vision.",

    },

]

def main():

    db = SessionLocal()

    try:

        for data in CATEGORIES:

            existing = (

                db.query(Category)

                .filter(Category.slug == data["slug"])

                .first()

            )

            if existing:

                existing.name = data["name"]

                existing.description = data["description"]

                print(f"UPDATED: {data['name']}")

            else:

                category = Category(

                    name=data["name"],

                    slug=data["slug"],

                    description=data["description"],

                )

                db.add(category)

                print(f"CREATED: {data['name']}")

        db.commit()

        print("\nForum categories ready.")

    finally:

        db.close()

if __name__ == "__main__":

    main()