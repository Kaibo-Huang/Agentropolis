"""
Tests for pure helper functions in src/simulation/seeder.py.

These functions are stateless and require no database, so they run fast
as pure unit tests without any async machinery.
"""

import pytest

from src.simulation.seeder import (
    _pick_home_neighborhood,
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
from src.data.industry_mapping import EMPLOYERS, INDUSTRY_HOME_WEIGHTS, INDUSTRIES
from src.data.toronto_zones import ALL_CELLS


class TestEmployerRoundRobin:
    """EMPLOYERS list supports round-robin archetype assignment."""

    def test_employers_is_nonempty_list(self):
        assert isinstance(EMPLOYERS, list)
        assert len(EMPLOYERS) > 0

    def test_each_employer_has_required_keys(self):
        for emp in EMPLOYERS:
            assert "name" in emp, f"Employer missing 'name': {emp}"
            assert "industry" in emp, f"Employer missing 'industry': {emp}"
            assert "work_district" in emp, f"Employer missing 'work_district': {emp}"

    def test_employer_name_is_nonempty_string(self):
        for emp in EMPLOYERS:
            assert isinstance(emp["name"], str)
            assert len(emp["name"]) > 0

    def test_employer_industry_is_known(self):
        for emp in EMPLOYERS:
            assert emp["industry"] in INDUSTRIES, (
                f"Unknown industry '{emp['industry']}' in employer '{emp['name']}'"
            )

    def test_round_robin_cycles_through_all_employers(self):
        n = len(EMPLOYERS)
        # Cycling n * 2 times should visit every employer at least twice
        visited = set()
        for i in range(n * 2):
            emp = EMPLOYERS[i % n]
            visited.add(emp["name"])
        assert visited == {e["name"] for e in EMPLOYERS}

    def test_industries_list_matches_employer_industries(self):
        employer_industries = {e["industry"] for e in EMPLOYERS}
        for ind in employer_industries:
            assert ind in INDUSTRIES


class TestPickHomeNeighborhood:
    """_pick_home_neighborhood returns a valid residential neighborhood name."""

    @pytest.mark.parametrize("industry", INDUSTRIES)
    def test_returns_string_for_known_industry(self, industry):
        result = _pick_home_neighborhood(industry)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("industry", INDUSTRIES)
    def test_result_is_in_home_weights_keys(self, industry):
        weights_map = INDUSTRY_HOME_WEIGHTS[industry]
        valid_neighborhoods = set(weights_map.keys())
        for _ in range(20):
            result = _pick_home_neighborhood(industry)
            assert result in valid_neighborhoods, (
                f"_pick_home_neighborhood({industry!r}) returned unexpected "
                f"value {result!r}"
            )

    def test_unknown_industry_returns_some_string(self):
        result = _pick_home_neighborhood("AlienIndustry")
        assert isinstance(result, str)
        assert len(result) > 0


class TestRandomPosition:
    """_random_position returns a [lat, lng] list within expected Toronto bounds."""

    def test_returns_list_of_two(self):
        pos = _random_position("Financial / St. Lawrence")
        assert isinstance(pos, list)
        assert len(pos) == 2

    def test_values_are_floats(self):
        pos = _random_position("Financial / St. Lawrence")
        assert isinstance(pos[0], float)
        assert isinstance(pos[1], float)

    def test_unknown_region_falls_back_to_toronto_centre(self):
        pos = _random_position("NonExistentRegion")
        # Toronto city centre is approximately 43.65, -79.38
        assert 43.5 <= pos[0] <= 43.8
        assert -79.5 <= pos[1] <= -79.2

    @pytest.mark.parametrize("zone", list(ALL_CELLS.keys())[:5])
    def test_known_zone_within_toronto_bounds(self, zone):
        pos = _random_position(zone)
        # All zones should produce positions within greater Toronto area
        assert 43.5 <= pos[0] <= 43.8, f"lat {pos[0]} out of Toronto range"
        assert -79.6 <= pos[1] <= -79.2, f"lng {pos[1]} out of Toronto range"

    def test_position_is_rounded_to_6_decimal_places(self):
        pos = _random_position("Financial / St. Lawrence")
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
