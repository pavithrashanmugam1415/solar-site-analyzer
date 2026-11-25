from types import SimpleNamespace

from django.test import SimpleTestCase

from .scoring import (
    area_score, calculate_scores, grid_score, infrastructure_score,
    slope_score, solar_score, validate_weights,
)


class FactorScoreTests(SimpleTestCase):
    """Examples taken from Scoring_Calculation_Reference.md."""

    def test_solar_score(self):
        self.assertEqual(solar_score(6.2), 100)
        self.assertAlmostEqual(solar_score(4.5), 60.0)
        self.assertEqual(solar_score(2.8), 0)

    def test_area_score(self):
        self.assertEqual(area_score(95000), 100)
        self.assertAlmostEqual(area_score(25000), 44.44, places=2)
        self.assertEqual(area_score(4500), 0)

    def test_grid_score(self):
        self.assertEqual(grid_score(0.5), 100)
        self.assertAlmostEqual(grid_score(8), 63.16, places=2)
        self.assertEqual(grid_score(25), 0)

    def test_slope_score(self):
        self.assertEqual(slope_score(2.5), 100)
        self.assertAlmostEqual(slope_score(8), 85.0)
        self.assertAlmostEqual(slope_score(18), 20.0)
        self.assertEqual(slope_score(25), 0)

    def test_infrastructure_score(self):
        self.assertEqual(infrastructure_score(0.2), 100)
        self.assertAlmostEqual(infrastructure_score(1.5), 77.78, places=2)
        self.assertEqual(infrastructure_score(6), 0)


class TotalScoreTests(SimpleTestCase):

    def test_site_9_perfect_site(self):
        site = SimpleNamespace(solar_irradiance_kwh=6.2, area_sqm=95000,
                               grid_distance_km=0.5, slope_degrees=0.8,
                               road_distance_km=0.2)
        self.assertEqual(calculate_scores(site)["total"], 100.0)

    def test_custom_weights_change_total(self):
        site = SimpleNamespace(solar_irradiance_kwh=6.0, area_sqm=5000,
                               grid_distance_km=20, slope_degrees=25,
                               road_distance_km=5)
        only_solar = {"solar": 1.0, "area": 0, "grid": 0, "slope": 0, "infrastructure": 0}
        self.assertEqual(calculate_scores(site, only_solar)["total"], 100.0)


class WeightValidationTests(SimpleTestCase):

    def test_valid_weights(self):
        weights = {"solar": 0.4, "area": 0.3, "grid": 0.1, "slope": 0.1, "infrastructure": 0.1}
        self.assertEqual(validate_weights(weights), [])

    def test_weights_must_sum_to_one(self):
        weights = {"solar": 0.5, "area": 0.5, "grid": 0.5, "slope": 0, "infrastructure": 0}
        self.assertTrue(validate_weights(weights))

    def test_missing_and_negative_weights(self):
        errors = validate_weights({"solar": -0.1})
        self.assertTrue(any("Missing" in e for e in errors))
        self.assertTrue(any("between 0 and 1" in e for e in errors))