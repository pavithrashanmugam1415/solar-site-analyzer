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




from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Site
from .services import run_analysis


class ApiTests(APITestCase):
    """API tests run on a temporary test database with 2 sites."""

    def setUp(self):
        base = dict(latitude=11.0, longitude=77.0, elevation_m=300,
                    land_type="Agricultural", region="Tamil Nadu")
        Site.objects.create(site_id=1, site_name="Perfect site", area_sqm=95000,
                            solar_irradiance_kwh=6.2, grid_distance_km=0.5,
                            slope_degrees=0.8, road_distance_km=0.2, **base)
        Site.objects.create(site_id=2, site_name="Weak site", area_sqm=15000,
                            solar_irradiance_kwh=4.2, grid_distance_km=15.2,
                            slope_degrees=18.5, road_distance_km=5.5, **base)
        run_analysis()

    def test_list_sites_sorted_by_score(self):
        response = self.client.get(reverse("site-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["site_name"], "Perfect site")

    def test_min_score_filter(self):
        response = self.client.get(reverse("site-list"), {"min_score": 90})
        self.assertEqual(response.data["count"], 1)

    def test_invalid_min_score_returns_400(self):
        response = self.client.get(reverse("site-list"), {"min_score": "abc"})
        self.assertEqual(response.status_code, 400)

    def test_site_detail_and_404(self):
        response = self.client.get(reverse("site-detail", args=[1]))
        self.assertEqual(response.data["analysis"]["total_score"], 100.0)
        self.assertEqual(response.data["analysis"]["rank"], 1)
        self.assertEqual(self.client.get(reverse("site-detail", args=[999])).status_code, 404)

    def test_analyze_with_bad_weights_returns_400(self):
        response = self.client.post(reverse("analyze"),
                                    {"weights": {"solar": 0.9, "area": 0.9}}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_analyze_with_custom_weights(self):
        weights = {"solar": 1.0, "area": 0, "grid": 0, "slope": 0, "infrastructure": 0}
        response = self.client.post(reverse("analyze"), {"weights": weights}, format="json")
        self.assertEqual(response.status_code, 200)
        weak = self.client.get(reverse("site-detail", args=[2])).data
        self.assertEqual(weak["analysis"]["total_score"], 48.0)

    def test_statistics(self):
        response = self.client.get(reverse("statistics"))
        self.assertEqual(response.data["summary"]["total_sites"], 2)
        self.assertEqual(response.data["summary"]["max_score"], 100.0)

    def test_export_csv(self):
        response = self.client.get(reverse("export"), {"format": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Perfect site", response.content.decode())