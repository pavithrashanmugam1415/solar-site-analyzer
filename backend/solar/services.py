"""Business logic that uses the database: running an analysis for all sites."""

from django.db import transaction

from .models import AnalysisParameter, AnalysisResult, Site
from .scoring import DEFAULT_WEIGHTS, calculate_scores

# 25Nov26
from django.db.models import Max

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


def latest_results():
    """
    The newest AnalysisResult for each site (one row per site).
    Every analysis run adds new rows, so we pick the highest result_id per site.
    """
    latest_ids = (
        AnalysisResult.objects.values("site_id")
        .annotate(latest_id=Max("result_id"))
        .values("latest_id")
    )
    return AnalysisResult.objects.filter(result_id__in=latest_ids).select_related("site")


def save_weights(weights):
    """Store custom weights as the current weights in analysis_parameters."""
    for key, name in PARAMETER_NAMES.items():
        AnalysisParameter.objects.update_or_create(
            parameter_name=name, defaults={"weight_value": weights[key], "is_active": True}
        )