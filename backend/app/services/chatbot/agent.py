from app.services.chatbot.classifier import classify_message

from app.services.chatbot.knowledge import get_knowledge

from app.services.chatbot.output_guard import sanitize_output

from app.services.chatbot.policy import policy_response

def generate_answer(message: str) -> tuple[str, bool, str]:

    category = classify_message(message)

    restricted = policy_response(category)

    if restricted:

        return restricted, False, category

    knowledge = get_knowledge(category)

    answer = (

        f"{knowledge}\n\n"

        "If you want, I can also explain the available features "

        "and user workflow in more detail."

    )

    answer = sanitize_output(answer)

    return answer, True, category