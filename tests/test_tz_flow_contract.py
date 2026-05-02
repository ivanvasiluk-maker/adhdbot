from texts import (
    morning_checkin_text,
    evening_close_question,
    build_payment_offer,
    skill_card_text,
    kb_morning_checkin,
    kb_evening_close,
    kb_training_run,
)
from skills import SKILLS_DB


def _kb_texts(kb):
    return [b.text for row in kb.keyboard for b in row]


def test_morning_prompt_contract():
    txt = morning_checkin_text("marsha", "Аня")
    assert "Доброе утро, Аня." in txt
    assert "Как ты сейчас?" in txt


def test_evening_prompt_contract():
    assert evening_close_question("marsha") == "Как прошёл день?"


def test_payment_offer_contract():
    txt = build_payment_offer({})
    assert "мы уже разобрали" in txt
    assert "ты уже сделал(а) первые шаги" in txt
    assert "Дальше есть два варианта" in txt


def test_training_keyboard_contract():
    labels = _kb_texts(kb_training_run)
    assert "✅ Сделал(а)" in labels
    assert "↩️ Вернулся(лась)" in labels
    assert "🤔 Не понял зачем" in labels
    assert "🆘 Кризис" in labels


def test_morning_evening_keyboards_contract():
    m = set(_kb_texts(kb_morning_checkin))
    assert {"нормально", "тревожно", "нет сил", "отвлекаюсь", "не хочу начинать"}.issubset(m)

    e = set(_kb_texts(kb_evening_close))
    assert {"✅ сделал", "😐 частично", "❌ не сделал", "↩️ срывался, но возвращался"}.issubset(e)


def test_skill_card_contains_required_sections():
    sample = next(iter(SKILLS_DB.values()))
    text = skill_card_text(sample, target="не пишу текст")
    for marker in ["📌 На чём тренируемся:", "🧩 Навык:", "Сделай:", "Минимум:", "Всё."]:
        assert marker in text

