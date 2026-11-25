"""
Suitability scoring for solar sites.

Every factor is turned into a score from 0 to 100, then the five scores
are combined with weights (which must add up to 1.0) into one total score.
Formulas follow Scoring_Calculation_Reference.md.
"""

DEFAULT_WEIGHTS = {
    "solar": 0.35,
    "area": 0.25,
    "grid": 0.20,
    "slope": 0.15,
    "infrastructure": 0.05,
}


def solar_score(irradiance_kwh):
    """100 at >= 5.5 kWh/m2/day, 0 below 3.0, straight line in between."""
    if irradiance_kwh >= 5.5:
        return 100.0
    if irradiance_kwh < 3.0:
        return 0.0
    return (irradiance_kwh - 3.0) / 2.5 * 100


def area_score(area_sqm):
    """100 at >= 50,000 m2, 0 below 5,000 m2, straight line in between."""
    if area_sqm >= 50000:
        return 100.0
    if area_sqm < 5000:
        return 0.0
    return (area_sqm - 5000) / 45000 * 100


def grid_score(grid_distance_km):
    """100 at <= 1 km, 0 at >= 20 km. Closer to the grid is better."""
    if grid_distance_km <= 1:
        return 100.0
    if grid_distance_km >= 20:
        return 0.0
    return 100 - (grid_distance_km - 1) / 19 * 100


def slope_score(slope_degrees):
    """100 at <= 5 deg, 50 at 15 deg, 0 above 20 deg. Flatter is better."""
    if slope_degrees <= 5:
        return 100.0
    if slope_degrees > 20:
        return 0.0
    if slope_degrees <= 15:
        return 100 - (slope_degrees - 5) / 10 * 50
    return 50 - (slope_degrees - 15) / 5 * 50


def infrastructure_score(road_distance_km):
    """100 at <= 0.5 km from a road, 0 at >= 5 km."""
    if road_distance_km <= 0.5:
        return 100.0
    if road_distance_km >= 5:
        return 0.0
    return 100 - (road_distance_km - 0.5) / 4.5 * 100


def validate_weights(weights):
    """
    Check custom weights. Returns a list of error messages (empty = valid).
    Rules: all 5 keys present, each between 0 and 1, total equal to 1.0.
    """
    errors = []
    missing = set(DEFAULT_WEIGHTS) - set(weights)
    extra = set(weights) - set(DEFAULT_WEIGHTS)
    if missing:
        errors.append(f"Missing weights: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Unknown weights: {', '.join(sorted(extra))}")
    for key, value in weights.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"Weight '{key}' must be a number")
        elif not 0 <= value <= 1:
            errors.append(f"Weight '{key}' must be between 0 and 1")
    if not errors and abs(sum(weights.values()) - 1.0) > 0.001:
        errors.append(f"Weights must add up to 1.0 (got {sum(weights.values()):.3f})")
    return errors


def calculate_scores(site, weights=None):
    """
    Calculate all scores for one site.

    `site` can be a Site model or any object with the CSV field names.
    Returns a dict with the five factor scores and the weighted total,
    each rounded to 2 decimals.
    """
    weights = weights or DEFAULT_WEIGHTS
    scores = {
        "solar": solar_score(float(site.solar_irradiance_kwh)),
        "area": area_score(float(site.area_sqm)),
        "grid": grid_score(float(site.grid_distance_km)),
        "slope": slope_score(float(site.slope_degrees)),
        "infrastructure": infrastructure_score(float(site.road_distance_km)),
    }
    total = sum(scores[key] * weights[key] for key in scores)
    result = {key: round(value, 2) for key, value in scores.items()}
    result["total"] = round(total, 2)
    return result


def score_category(total):
    """Label a total score, using the bands from the reference document."""
    if total >= 80:
        return "Excellent"
    if total >= 60:
        return "Good"
    if total >= 40:
        return "Fair"
    if total >= 20:
        return "Poor"
    return "Very Poor"