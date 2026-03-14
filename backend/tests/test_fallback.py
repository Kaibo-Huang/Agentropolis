"""
Tests for src/agents/fallback.py — Deterministic fallback action generator.
"""

import pytest
from datetime import datetime, timezone

from src.agents.fallback import generate_fallback_actions
from src.agents.schemas import ArchetypeResponse


def _dt(hour: int, minute: int = 0) -> datetime:
    """Convenience: create a timezone-aware datetime for a given hour."""
    return datetime(2025, 1, 15, hour, minute, tzinfo=timezone.utc)


class TestFallbackActionsReturnType:
    """generate_fallback_actions always returns a valid ArchetypeResponse."""

    @pytest.mark.parametrize("hour", range(24))
    def test_returns_archetype_response_for_every_hour(self, hour):
        result = generate_fallback_actions(_dt(hour))
        assert isinstance(result, ArchetypeResponse)

    @pytest.mark.parametrize("hour", range(24))
    def test_tweet_is_always_none(self, hour):
        result = generate_fallback_actions(_dt(hour))
        assert result.tweet is None

    @pytest.mark.parametrize("hour", range(24))
    def test_actions_list_is_nonempty(self, hour):
        result = generate_fallback_actions(_dt(hour))
        assert len(result.actions) >= 1

    @pytest.mark.parametrize("hour", range(24))
    def test_all_actions_have_positive_duration(self, hour):
        result = generate_fallback_actions(_dt(hour))
        for action in result.actions:
            assert action.duration > 0, (
                f"Hour {hour}: action '{action.action_type}' has non-positive duration {action.duration}"
            )

    @pytest.mark.parametrize("hour", range(24))
    def test_all_actions_have_nonempty_thinking(self, hour):
        result = generate_fallback_actions(_dt(hour))
        for action in result.actions:
            assert action.thinking.strip() != ""


class TestFallbackActionsByTimeSlot:
    """Verify the correct action type is chosen for each time-of-day bucket."""

    @pytest.mark.parametrize("hour", [0, 1, 2, 3, 4, 5])
    def test_midnight_to_6am_is_sleep(self, hour):
        result = generate_fallback_actions(_dt(hour))
        assert result.actions[0].action_type == "sleep"

    def test_6am_includes_eat_and_commute(self):
        result = generate_fallback_actions(_dt(6))
        types = [a.action_type for a in result.actions]
        assert "eat" in types
        assert "commute" in types

    @pytest.mark.parametrize("hour", [7, 8, 9, 10, 11])
    def test_morning_work_hours(self, hour):
        result = generate_fallback_actions(_dt(hour))
        assert result.actions[0].action_type == "work"

    def test_noon_is_lunch(self):
        result = generate_fallback_actions(_dt(12))
        assert result.actions[0].action_type == "eat"

    @pytest.mark.parametrize("hour", [13, 14, 15, 16])
    def test_afternoon_work_hours(self, hour):
        result = generate_fallback_actions(_dt(hour))
        assert result.actions[0].action_type == "work"

    def test_5pm_is_commute_home(self):
        result = generate_fallback_actions(_dt(17))
        assert result.actions[0].action_type == "commute"

    def test_6pm_is_dinner(self):
        result = generate_fallback_actions(_dt(18))
        assert result.actions[0].action_type == "eat"

    @pytest.mark.parametrize("hour", [19, 20, 21])
    def test_evening_is_socialize(self, hour):
        result = generate_fallback_actions(_dt(hour))
        assert result.actions[0].action_type == "socialize"

    @pytest.mark.parametrize("hour", [22, 23])
    def test_late_night_is_sleep(self, hour):
        result = generate_fallback_actions(_dt(hour))
        assert result.actions[0].action_type == "sleep"


class TestFallbackDurations:
    """Duration values must be consistent with the time slot."""

    def test_midnight_sleep_duration_is_6_minus_hour(self):
        # At hour 0, should sleep for 6.0 - 0 = 6 hours
        result = generate_fallback_actions(_dt(0))
        assert result.actions[0].duration == 6.0

    def test_2am_sleep_duration_is_4(self):
        result = generate_fallback_actions(_dt(2))
        assert result.actions[0].duration == 4.0

    def test_morning_work_duration_capped_at_5(self):
        # At hour 7, work should be min(5, 12-7) = 5
        result = generate_fallback_actions(_dt(7))
        assert result.actions[0].duration == 5.0

    def test_afternoon_work_duration_capped_at_4(self):
        # At hour 13, work should be min(4, 17-13) = 4
        result = generate_fallback_actions(_dt(13))
        assert result.actions[0].duration == 4.0

    def test_late_afternoon_work_shorter(self):
        # At hour 16, work should be min(4, 17-16) = 1
        result = generate_fallback_actions(_dt(16))
        assert result.actions[0].duration == 1.0

    def test_evening_socialize_duration_capped(self):
        # At hour 19, socialize should be min(3, 22-19) = 3
        result = generate_fallback_actions(_dt(19))
        assert result.actions[0].duration == 3.0

    def test_evening_socialize_shorter_near_bedtime(self):
        # At hour 21, socialize should be min(3, 22-21) = 1
        result = generate_fallback_actions(_dt(21))
        assert result.actions[0].duration == 1.0
