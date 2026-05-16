from skills import SKILLS_DB

REQ = {
    "skill_id", "profile_type", "name", "goal", "when_to_use", "real_life_example",
    "steps", "minimum_action", "after_question", "if_boring_response", "if_hard_response",
    "if_skeptic_response", "if_failed_response", "coach_feedback", "trainer_variants",
}


def test_all_skills_have_tz_schema_fields():
    for sid, s in SKILLS_DB.items():
        missing = REQ - set(s.keys())
        assert not missing, f"{sid} missing {missing}"


def test_trainer_variants_are_full_text_blocks():
    for sid, s in SKILLS_DB.items():
        tv = s["trainer_variants"]
        assert set(tv.keys()) == {"marsha", "skinny", "beck"}
        for key in ("marsha", "skinny", "beck"):
            assert isinstance(tv[key], str) and len(tv[key]) > 30, f"{sid}:{key} too short"

