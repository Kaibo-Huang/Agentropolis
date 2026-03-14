"""
Tests for pure helper functions in src/simulation/seeder.py.

These functions are stateless and require no database, so they run fast
as pure unit tests without any async machinery.
"""

import pytest

from src.simulation.seeder import (
    _proportional_distribution,
    _company_name,
    _random_position,
    _random_age,
    _random_gender,
    _random_race,
    _random_social_class,
    _random_name,
)
from src.data.demographics import (
    AGE_DISTRIBUTION,
    GENDER_DISTRIBUTION,
    RACE_DISTRIBUTION,
    SOCIAL_CLASSES,
)
from src.data.toronto_neighborhoods import NEIGHBORHOOD_BOUNDS


class TestProportionalDistribution:
    """_proportional_distribution allocates totals and sums exactly."""

    def test_output_sums_to_total(self):
        weights = {"a": 0.5, "b": 0.3, "c": 0.2}
        result = _proportional_distribution(100, weights)
        assert sum(result.values()) == 100

    def test_output_keys_match_weights(self):
        weights = {"x": 1.0, "y": 2.0, "z": 3.0}
        result = _proportional_distribution(10, weights)
        assert set(result.keys()) == {"x", "y", "z"}

    def test_all_values_nonnegative(self):
        weights = {"a": 0.1, "b": 0.9}
        result = _proportional_distribution(50, weights)
        for v in result.values():
            assert v >= 0

    def test_single_key_gets_all(self):
        result = _proportional_distribution(7, {"only": 1.0})
        assert result == {"only": 7}

    def test_total_of_one(self):
        weights = {"a": 1, "b": 1, "c": 1}
        result = _proportional_distribution(1, weights)
        assert sum(result.values()) == 1

    def test_equal_weights_approximate_equal_distribution(self):
        weights = {"a": 1, "b": 1, "c": 1, "d": 1}
        result = _proportional_distribution(100, weights)
        assert sum(result.values()) == 100
        # All buckets should be 25
        for v in result.values():
            assert v == 25

    def test_large_total(self):
        weights = {"Finance": 0.2, "Tech": 0.3, "Healthcare": 0.15,
                   "Retail": 0.1, "Manufacturing": 0.1,
                   "Government": 0.05, "Education": 0.1}
        result = _proportional_distribution(10000, weights)
        assert sum(result.values()) == 10000


class TestCompanyName:
    """_company_name generates a non-empty two-word string."""

    def test_returns_string(self):
        name = _company_name("Finance", 0)
        assert isinstance(name, str)

    def test_name_has_two_parts(self):
        name = _company_name("Tech", 0)
        parts = name.split()
        assert len(parts) == 2

    def test_unknown_industry_has_fallback(self):
        name = _company_name("AlienIndustry", 0)
        assert len(name) > 0

    @pytest.mark.parametrize("industry", [
        "Finance", "Tech", "Healthcare", "Retail",
        "Manufacturing", "Government", "Education",
    ])
    def test_all_industries_return_valid_name(self, industry):
        name = _company_name(industry, 0)
        assert len(name) > 0

    def test_different_indices_cycle_names(self):
        names = {_company_name("Tech", i) for i in range(20)}
        # Shouldn't all be identical — cycling through prefixes/suffixes
        assert len(names) > 1


class TestRandomPosition:
    """_random_position returns a [lat, lng] list within expected Toronto bounds."""

    def test_returns_list_of_two(self):
        pos = _random_position("Downtown Core")
        assert isinstance(pos, list)
        assert len(pos) == 2

    def test_values_are_floats(self):
        pos = _random_position("Downtown Core")
        assert isinstance(pos[0], float)
        assert isinstance(pos[1], float)

    def test_unknown_region_falls_back_to_toronto_centre(self):
        pos = _random_position("NonExistentRegion")
        # Toronto city centre is approximately 43.65, -79.38
        assert 43.5 <= pos[0] <= 43.8
        assert -79.5 <= pos[1] <= -79.2

    @pytest.mark.parametrize("region", list(NEIGHBORHOOD_BOUNDS.keys())[:5])
    def test_known_region_within_bounding_box(self, region):
        bounds = NEIGHBORHOOD_BOUNDS[region]
        pos = _random_position(region)
        assert bounds["min_lat"] <= pos[0] <= bounds["max_lat"]
        assert bounds["min_lng"] <= pos[1] <= bounds["max_lng"]

    def test_position_is_rounded_to_6_decimal_places(self):
        pos = _random_position("Downtown Core")
        # round(x, 6) should not change the value
        assert pos[0] == round(pos[0], 6)
        assert pos[1] == round(pos[1], 6)


class TestRandomDemographics:
    """Random demographic samplers return valid values from their distributions."""

    def test_random_age_in_valid_range(self):
        for _ in range(50):
            age = _random_age()
            assert isinstance(age, int)
            # Ages are drawn from AGE_DISTRIBUTION buckets
            min_age = min(lo for lo, _, _ in AGE_DISTRIBUTION)
            max_age = max(hi for _, hi, _ in AGE_DISTRIBUTION)
            assert min_age <= age <= max_age

    def test_random_gender_in_distribution(self):
        valid_genders = set(GENDER_DISTRIBUTION.keys())
        for _ in range(50):
            g = _random_gender()
            assert g in valid_genders

    def test_random_race_in_distribution(self):
        valid_races = set(RACE_DISTRIBUTION.keys())
        for _ in range(50):
            r = _random_race()
            assert r in valid_races

    def test_random_social_class_in_valid_set(self):
        for _ in range(50):
            sc = _random_social_class("Downtown Core")
            assert sc in SOCIAL_CLASSES

    def test_random_social_class_unknown_region_uses_defaults(self):
        for _ in range(20):
            sc = _random_social_class("NoSuchRegion")
            assert sc in SOCIAL_CLASSES

    def test_random_name_returns_two_word_string(self):
        for _ in range(20):
            name = _random_name()
            parts = name.split()
            assert len(parts) == 2
