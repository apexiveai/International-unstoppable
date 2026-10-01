PROTECTED_RESPONSE = (

    "I can explain Apexive Community's public features and capabilities, "

    "but I can't provide source code, credentials, API keys, passwords, "

    "private infrastructure information, or confidential internal security details."

)

SECURITY_RESTRICTED_RESPONSE = (

    "I can provide general information about security and safe use of "

    "Apexive Community, but I can't provide instructions for bypassing, "

    "compromising, or disabling security controls."

)

def policy_response(category: str) -> str | None:

    if category == "protected":

        return PROTECTED_RESPONSE

    if category == "security_restricted":

        return SECURITY_RESTRICTED_RESPONSE

    return None