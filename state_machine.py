from __future__ import annotations

from enum import Enum


class BotState(str, Enum):
    ONBOARDING = "onboarding"
    MORNING_CHECKIN = "morning_checkin"
    ANALYSIS = "analysis"
    DETAILS = "details"
    ACTION = "action"
    WAITING_RESULT = "waiting_result"
    ACTION_FAILED_REASON = "action_failed_reason"
    REFLECTION = "reflection"
    EVENING = "evening"
    OFFER = "offer"
    FREE_MODE = "free_mode"
    PAID_MODE = "paid_mode"
    CRISIS = "crisis"


ALLOWED_TRANSITIONS = {
    BotState.ONBOARDING: {BotState.ANALYSIS},
    BotState.MORNING_CHECKIN: {BotState.ANALYSIS, BotState.ACTION},
    BotState.ANALYSIS: {BotState.DETAILS, BotState.ACTION, BotState.CRISIS},
    BotState.DETAILS: {BotState.ACTION, BotState.CRISIS},
    BotState.ACTION: {BotState.WAITING_RESULT, BotState.CRISIS},
    BotState.WAITING_RESULT: {BotState.REFLECTION, BotState.ACTION_FAILED_REASON, BotState.CRISIS},
    BotState.ACTION_FAILED_REASON: {BotState.ACTION, BotState.CRISIS},
    BotState.REFLECTION: {BotState.ACTION, BotState.EVENING, BotState.CRISIS},
    BotState.EVENING: {BotState.MORNING_CHECKIN, BotState.OFFER, BotState.CRISIS},
    BotState.OFFER: {BotState.FREE_MODE, BotState.PAID_MODE, BotState.CRISIS},
    BotState.FREE_MODE: {BotState.ACTION, BotState.ANALYSIS, BotState.CRISIS},
    BotState.PAID_MODE: {BotState.ACTION, BotState.ANALYSIS, BotState.CRISIS},
    BotState.CRISIS: {BotState.ACTION, BotState.ANALYSIS},
}


def is_transition_allowed(current_state: str, next_state: str) -> bool:
    try:
        src = BotState(current_state)
        dst = BotState(next_state)
    except ValueError:
        return False
    return dst in ALLOWED_TRANSITIONS.get(src, set())


def next_day_state(day: int) -> BotState:
    return BotState.OFFER if int(day or 1) == 3 else BotState.MORNING_CHECKIN
