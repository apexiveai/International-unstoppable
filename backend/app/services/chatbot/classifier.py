import re

PROTECTED_PATTERNS = [

    r"\bsource\s*code\b",

    r"\bsourcecode\b",

    r"\bapi[\s_-]?key\b",

    r"\bsecret\b",

    r"\bpassword\b",

    r"\bcredential\b",

    r"\bdatabase[\s_-]?(password|url|connection|string)\b",

    r"\bjwt[\s_-]?secret\b",

    r"\bprivate[\s_-]?key\b",

    r"\btoken\b",

    r"\benv[\s_-]?file\b",

    r"\.env\b",

    r"\bbackend[\s_-]?code\b",

    r"\bfrontend[\s_-]?code\b",

    r"\binternal[\s_-]?architecture\b",

    r"\bsecurity[\s_-]?configuration\b",

    r"\bsecurity[\s_-]?implementation\b",

    r"\badmin[\s_-]?credentials\b",

]

SECURITY_ATTACK_PATTERNS = [

    r"\bbypass\b",

    r"\bexploit\b",

    r"\bhack\b",

    r"\bpenetrat(e|ion)\b",

    r"\bbrute[\s_-]?force\b",

    r"\bdisable[\s_-]?security\b",

    r"\bget[\s_-]?around[\s_-]?security\b",

]

def classify_message(message: str) -> str:

    text = message.lower().strip()

    for pattern in PROTECTED_PATTERNS:

        if re.search(pattern, text, re.IGNORECASE):

            return "protected"

    for pattern in SECURITY_ATTACK_PATTERNS:

        if re.search(pattern, text, re.IGNORECASE):

            return "security_restricted"

    if any(

        word in text

        for word in [

            "security",

            "secure",

            "privacy",

            "data protection",

            "encryption",

        ]

    ):

        return "security_general"

    if any(

        word in text

        for word in [

            "clone detector",

            "clone",

            "similarity",

            "document comparison",

        ]

    ):

        return "clone_detector"

    if any(

        word in text

        for word in [

            "forum",

            "discussion",

            "thread",

            "reply",

        ]

    ):

        return "forums"

    if any(

        word in text

        for word in [

            "article",

            "articles",

        ]

    ):

        return "articles"

    if any(

        word in text

        for word in [

            "project",

            "projects",

        ]

    ):

        return "projects"

    if any(

        word in text

        for word in [

            "resource",

            "resources",

        ]

    ):

        return "resources"

    if any(

        word in text

        for word in [

            "apexive",

            "community",

            "platform",

            "feature",

            "features",

            "what can",

            "how does",

            "what is",

        ]

    ):

        return "product"

    return "general"