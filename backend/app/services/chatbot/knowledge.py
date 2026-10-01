PRODUCT_KNOWLEDGE = {

    "product": {

        "title": "Apexive Community",

        "content": (

            "Apexive Community is a technology-focused community platform "

            "for discussions, technical articles, projects, resources, "

            "search, and visual document comparison."

        ),

    },

    "forums": {

        "title": "Forums",

        "content": (

            "Apexive Community provides technical discussion areas "

            "covering Security, Data & Cloud, Development, and "

            "Artificial Intelligence."

        ),

    },

    "articles": {

        "title": "Articles",

        "content": (

            "The Articles area is designed for publishing and reading "

            "technical knowledge, engineering insights, tutorials, "

            "research, and community knowledge."

        ),

    },

    "projects": {

        "title": "Projects",

        "content": (

            "The Projects area allows the community to discover and "

            "present technology projects, engineering work, experiments, "

            "and product development."

        ),

    },

    "resources": {

        "title": "Resources",

        "content": (

            "The Resources area is intended for useful technical "

            "materials, references, tools, documentation, and "

            "community-contributed resources."

        ),

    },

    "clone_detector": {

        "title": "Clone Detector",

        "content": (

            "Clone Detector compares supported documents and images "

            "and identifies visually similar areas. Matching regions "

            "can be highlighted so users can review potentially "

            "duplicated or similar content."

        ),

    },

    "security_general": {

        "title": "Security",

        "content": (

            "Security-related information provided by the client "

            "assistant is limited to public product behavior and "

            "safe-use information. Confidential implementation "

            "details, credentials, secrets, and private security "

            "configuration are not exposed."

        ),

    },

}

def get_knowledge(category: str) -> str:

    item = PRODUCT_KNOWLEDGE.get(category)

    if not item:

        item = PRODUCT_KNOWLEDGE["product"]

    return f"{item['title']}: {item['content']}"