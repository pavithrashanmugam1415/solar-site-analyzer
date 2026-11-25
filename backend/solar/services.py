"""Business logic that uses the database: running an analysis for all sites."""

from django.db import transaction

from .models import AnalysisParameter, AnalysisResult, Site
from .scoring import DEFAULT_WEIGHTS, calculate_scores

# Maps our short weight keys to the parameter names stored in MySQL
PARAMETER_NAMES = {
    "solar": "solar_irradiance_weight",
    "area": "area_weight",
    "grid": "grid_distance_weight",
    "slope": "slope_weight",
    "infrastructure": "infrastructure_weight",
}


def get_current_weights():
    """Read the active weights from the analysis_parameters table."""
    stored = {
        p.parameter_name: float(p.weight_value)
        for p in AnalysisParameter.objects.filter(is_active=True)
    }
    return {
        key: stored.get(name, DEFAULT_WEIGHTS[key])
        for key, name in PARAMETER_NAMES.items()
    }


@transaction.atomic
def run_analysis(weights=None):
    """
    Score every site with the given weights (or the stored ones) and save
    one new AnalysisResult per site. Returns the number of sites scored.
    """
    weights = weights or get_current_weights()
    results = []
    for site in Site.objects.all():
        scores = calculate_scores(site, weights)
        results.append(AnalysisResult(
            site=site,
            solar_irradiance_score=scores["solar"],
            area_score=scores["area"],
            grid_distance_score=scores["grid"],
            slope_score=scores["slope"],
            infrastructure_score=scores["infrastructure"],
            total_suitability_score=scores["total"],
            parameters_snapshot=weights,
        ))
    AnalysisResult.objects.bulk_create(results)
    return len(results)