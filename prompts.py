def get_analyze_state_prompt(user_text: str, current_state: dict | None = None) -> str:
    state = current_state or {}
    return (
        "Ты поведенческий анализатор для ADHD-практики. Верни только JSON без markdown.\n"
        "Не ставь диагнозов, не обещай лечение, не пиши свободный ответ пользователю.\n"
        "Максимум 1 уточняющий вопрос. short_analysis <= 3 коротких предложений. long_analysis <= 6 строк.\n"
        "Если есть кризис: mode='crisis', skill='crisis_grounding', risk='high'.\n"
        "Текущий state: "
        f"{state}\n"
        "Текст пользователя: "
        f"{user_text}\n"
        "Схема JSON:"
        "{"
        "\"problem\":\"...\",\"emotion\":\"...\",\"pattern\":\"...\","
        "\"energy\":\"very_low|low|medium|high|unknown\","
        "\"mode\":\"analysis|action|training|crisis\",\"skill\":\"...\","
        "\"risk\":\"low|medium|high\",\"needs_clarification\":true|false,"
        "\"clarifying_question\":\"...\"|null,\"short_analysis\":\"...\",\"long_analysis\":\"...\""
        "}"
    )


def get_select_skill_prompt(pattern: str, energy: str, available_skills: list[str]) -> str:
    return (
        "Выбери ОДИН лучший навык на сегодня. Верни только JSON: "
        "{\"skill\":\"...\",\"reason\":\"...\"}. "
        f"pattern={pattern}; energy={energy}; available_skills={available_skills}"
    )


def get_crisis_check_prompt(user_text: str) -> str:
    return (
        "Проверь текст на кризис. Верни только JSON: "
        "{\"crisis\":true|false,\"risk\":\"low|medium|high\",\"reason\":\"...\"}. "
        f"text={user_text}"
    )
