"""
Tests for src/agents/schemas.py — Pydantic schema validation.
"""

import pytest
from pydantic import ValidationError

from src.agents.schemas import (
    ArchetypeAction,
    ArchetypeResponse,
    FollowerVariation,
    FollowerVariationBatch,
)


class TestArchetypeAction:
    """ArchetypeAction validates action_type, duration, and thinking."""

    def test_valid_action_work(self):
        from src.agents.schemas import ActionParams
        action = ArchetypeAction(
            action_type="work",
            duration=8.0,
            thinking="Grinding through the morning.",
        )
        assert action.action_type == "work"
        assert action.duration == 8.0
        assert action.action_params == ActionParams()

    def test_valid_action_sleep(self):
        action = ArchetypeAction(
            action_type="sleep",
            duration=7.5,
            thinking="Sleeping.",
        )
        assert action.action_type == "sleep"

    def test_all_valid_action_types(self):
        valid_types = [
            "work", "commute", "eat", "sleep", "shop",
            "exercise", "socialize", "post", "attend_event", "visit_family",
        ]
        for atype in valid_types:
            action = ArchetypeAction(action_type=atype, duration=1.0, thinking="ok")
            assert action.action_type == atype

    def test_invalid_action_type_raises(self):
        with pytest.raises(ValidationError):
            ArchetypeAction(action_type="fly", duration=1.0, thinking="ok")

    def test_thinking_max_length_enforced(self):
        with pytest.raises(ValidationError):
            ArchetypeAction(
                action_type="work",
                duration=1.0,
                thinking="x" * 201,  # exceeds max_length=200
            )

    def test_thinking_at_max_length_allowed(self):
        action = ArchetypeAction(
            action_type="eat",
            duration=0.5,
            thinking="y" * 200,
        )
        assert len(action.thinking) == 200

    def test_action_params_defaults_to_empty_dict(self):
        from src.agents.schemas import ActionParams
        action = ArchetypeAction(action_type="shop", duration=2.0, thinking="Buying stuff.")
        assert action.action_params == ActionParams()

    def test_action_params_accepts_dict(self):
        action = ArchetypeAction(
            action_type="shop",
            duration=1.0,
            thinking="Buying groceries.",
            action_params={"location": "Kensington Market"},
        )
        assert action.action_params.location == "Kensington Market"


class TestArchetypeResponse:
    """ArchetypeResponse wraps a list of actions with an optional tweet."""

    def test_valid_response_no_tweet(self):
        resp = ArchetypeResponse(
            actions=[
                ArchetypeAction(action_type="work", duration=4.0, thinking="Focus.")
            ]
        )
        assert resp.tweet is None
        assert len(resp.actions) == 1

    def test_valid_response_with_tweet(self):
        resp = ArchetypeResponse(
            actions=[
                ArchetypeAction(action_type="post", duration=0.1, thinking="Tweeting.")
            ],
            tweet="Just had the best coffee in the Annex!",
        )
        assert resp.tweet == "Just had the best coffee in the Annex!"

    def test_empty_actions_list_allowed(self):
        resp = ArchetypeResponse(actions=[])
        assert resp.actions == []

    def test_multiple_actions(self):
        resp = ArchetypeResponse(
            actions=[
                ArchetypeAction(action_type="eat", duration=0.5, thinking="Breakfast."),
                ArchetypeAction(action_type="commute", duration=0.5, thinking="Bus."),
                ArchetypeAction(action_type="work", duration=4.0, thinking="Morning work."),
            ]
        )
        assert len(resp.actions) == 3


class TestFollowerVariation:
    """FollowerVariation enforces bounded happiness_delta and timing_offset."""

    def test_valid_variation_defaults(self):
        v = FollowerVariation(follower_id=42)
        assert v.timing_offset_minutes == 0
        assert v.happiness_delta == 0
        assert v.tweet_text is None
        assert v.position is None

    def test_happiness_delta_at_bounds(self):
        v_min = FollowerVariation(follower_id=1, happiness_delta=-0.2)
        v_max = FollowerVariation(follower_id=1, happiness_delta=0.2)
        assert v_min.happiness_delta == -0.2
        assert v_max.happiness_delta == 0.2

    def test_happiness_delta_too_low_raises(self):
        with pytest.raises(ValidationError):
            FollowerVariation(follower_id=1, happiness_delta=-0.21)

    def test_happiness_delta_too_high_raises(self):
        with pytest.raises(ValidationError):
            FollowerVariation(follower_id=1, happiness_delta=0.21)

    def test_timing_offset_at_bounds(self):
        v_neg = FollowerVariation(follower_id=1, timing_offset_minutes=-15)
        v_pos = FollowerVariation(follower_id=1, timing_offset_minutes=15)
        assert v_neg.timing_offset_minutes == -15
        assert v_pos.timing_offset_minutes == 15

    def test_timing_offset_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            FollowerVariation(follower_id=1, timing_offset_minutes=16)

    def test_position_list_accepted(self):
        v = FollowerVariation(follower_id=1, position=[43.6532, -79.3832])
        assert v.position == [43.6532, -79.3832]

    def test_tweet_text_accepted(self):
        v = FollowerVariation(follower_id=5, tweet_text="Great day!")
        assert v.tweet_text == "Great day!"


class TestFollowerVariationBatch:
    """FollowerVariationBatch wraps a list of variations."""

    def test_empty_batch(self):
        batch = FollowerVariationBatch(variations=[])
        assert batch.variations == []

    def test_batch_with_variations(self):
        batch = FollowerVariationBatch(
            variations=[
                FollowerVariation(follower_id=1, happiness_delta=0.1),
                FollowerVariation(follower_id=2, happiness_delta=-0.05),
            ]
        )
        assert len(batch.variations) == 2
        assert batch.variations[0].follower_id == 1
