import re

FORBIDDEN_OUTPUT_PATTERNS = [

    r"api[_-]?key\s*[:=]\s*\S+",

    r"password\s*[:=]\s*\S+",

    r"jwt[_-]?secret\s*[:=]\s*\S+",

    r"database[_-]?url\s*[:=]\s*\S+",

    r"postgresql://\S+",

    r"mysql://\S+",

    r"mongodb://\S+",

    r"-----BEGIN .* PRIVATE KEY-----",

]

def sanitize_output(answer: str) -> str:

    for pattern in FORBIDDEN_OUTPUT_PATTERNS:

        if re.search(pattern, answer, re.IGNORECASE):

            return (

                "I can provide public product information, but I can't "

                "provide confidential credentials, secrets, or private "

                "infrastructure information."

            )

    return answer