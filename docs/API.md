# API Documentation

Base URL (local): `http://127.0.0.1:8000/api`

- All responses are JSON, except `GET /export?format=csv`, which returns a CSV file.
- Scores are from 0 to 100, rounded to 2 decimals.
- Each endpoint can also be opened in a browser (Django REST Framework shows a readable page).

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/sites` | List sites with latest scores (filter, sort, paginate) |
| GET | `/sites/{id}` | One site with full score breakdown and rank |
| POST | `/analyze` | Recalculate all scores with custom weights |
| GET | `/statistics` | Summary statistics across all sites |
| GET | `/export` | Download results as CSV or JSON |

## Score categories

| Total score | Category |
| --- | --- |
| 80 – 100 | Excellent |
| 60 – 79.99 | Good |
| 40 – 59.99 | Fair |
| 20 – 39.99 | Poor |
| 0 – 19.99 | Very Poor |

---

## GET /api/sites

All sites with their latest scores, highest score first by default.

| Parameter | Type | Description | Example |
| --- | --- | --- | --- |
| `min_score` | number 0–100 | Sites with score ≥ this value | `70` |
| `max_score` | number 0–100 | Sites with score ≤ this value | `90` |
| `land_type` | text | Sites of this land type | `Agricultural` |
| `ordering` | text | `score`, `name`, `area`, `solar`, `grid_distance`, `slope`; add `-` for descending | `-score` (default) |
| `limit` | integer | Results per page (default 50) | `10` |
| `offset` | integer | Results to skip | `20` |

Example: `GET /api/sites?min_score=90&limit=1`

    {
      "count": 34,
      "next": "http://127.0.0.1:8000/api/sites?limit=1&min_score=90&offset=1",
      "previous": null,
      "results": [
        {
          "site_id": 4, "site_name": "Udumalpet Solar Park",
          "latitude": 10.5857, "longitude": 77.2486, "area_sqm": 78000,
          "solar_irradiance_kwh": 6.1, "grid_distance_km": 0.8, "slope_degrees": 2.1,
          "road_distance_km": 0.5, "land_type": "Wasteland", "region": "Tamil Nadu",
          "solar_irradiance_score": 100.0, "area_score": 100.0, "grid_distance_score": 100.0,
          "slope_score": 100.0, "infrastructure_score": 100.0,
          "total_score": 100.0, "category": "Excellent"
        }
      ]
    }

Errors (400): `{"min_score": "Must be a number."}`, `{"min_score": "Must be between 0 and 100."}`, `{"ordering": "Use one of: score, name, area, solar, grid_distance, slope (prefix - for descending)."}`

---

## GET /api/sites/{id}

One site with all its data plus the analysis: total score, category, rank, and each factor's score, weight and points.

Example: `GET /api/sites/1`

    {
      "site_id": 1, "site_name": "Periyanaickenpalayam Site",
      "latitude": 11.0765, "longitude": 76.9872, "area_sqm": 45000,
      "solar_irradiance_kwh": 5.8, "grid_distance_km": 2.5, "slope_degrees": 3.2,
      "road_distance_km": 0.8, "elevation_m": 425,
      "land_type": "Agricultural", "region": "Tamil Nadu",
      "analysis": {
        "total_score": 95.31, "category": "Excellent", "rank": 28, "total_sites": 50,
        "breakdown": [
          { "factor": "solar",          "score": 100.0, "weight": 0.35, "weighted_score": 35.0 },
          { "factor": "area",           "score": 88.89, "weight": 0.25, "weighted_score": 22.22 },
          { "factor": "grid",           "score": 92.11, "weight": 0.2,  "weighted_score": 18.42 },
          { "factor": "slope",          "score": 100.0, "weight": 0.15, "weighted_score": 15.0 },
          { "factor": "infrastructure", "score": 93.33, "weight": 0.05, "weighted_score": 4.67 }
        ]
      }
    }

- `rank` = 1 + number of sites with a higher score.
- Error: **404** `{"detail": "No Site matches the given query."}` for an unknown id.

---

## POST /api/analyze

Recalculates the scores of all sites with new weights and saves them as the current weights. All 5 weights are required, each between 0 and 1, and they must add up to 1.0.

| Key | Factor | Default |
| --- | --- | --- |
| `solar` | Solar irradiance | 0.35 |
| `area` | Land area | 0.25 |
| `grid` | Distance to power grid | 0.20 |
| `slope` | Terrain slope | 0.15 |
| `infrastructure` | Distance to road | 0.05 |

Request body:

    {"weights": {"solar": 0.5, "area": 0.2, "grid": 0.15, "slope": 0.1, "infrastructure": 0.05}}

Response (200):

    {
      "message": "Recalculated scores for 50 sites.",
      "weights": {"solar": 0.5, "area": 0.2, "grid": 0.15, "slope": 0.1, "infrastructure": 0.05},
      "top_10": ["... 10 sites, same fields as GET /api/sites ..."]
    }

Errors (400), all problems listed at once:

    {"weights": ["Weights must add up to 1.0 (got 1.800)"]}
    {"weights": ["Missing weights: grid, infrastructure, slope", "Weight 'solar' must be between 0 and 1"]}

---

## GET /api/statistics

Summary statistics over all sites. No parameters. (Shortened.)

    {
      "summary": {
        "total_sites": 50, "average_score": 89.52, "min_score": 37.44, "max_score": 100.0,
        "std_dev": 15.32, "avg_solar": 96.56, "avg_area": 83.87, "avg_grid": 83.98,
        "avg_slope": 93.61, "avg_infrastructure": 78.31
      },
      "category_distribution": {"Excellent": 43, "Good": 3, "Fair": 2, "Poor": 2, "Very Poor": 0},
      "by_land_type": [{"land_type": "Wasteland", "site_count": 2, "average_score": 99.47}],
      "current_weights": {"solar": 0.35, "area": 0.25, "grid": 0.2, "slope": 0.15, "infrastructure": 0.05},
      "top_10": ["... 10 sites ..."]
    }

---

## GET /api/export

Downloads results with the same filters as `/api/sites`, all matching sites, no pagination.

| Parameter | Values | Default |
| --- | --- | --- |
| `format` | `csv` or `json` | `json` |
| `min_score` | number 0–100 | none |

Examples: `GET /api/export?format=csv&min_score=90` downloads `solar_sites.csv`; `GET /api/export?format=json` downloads `solar_sites.json`.

Error (400): `{"format": "Use csv or json."}`

---

## Status codes

| Code | Meaning |
| --- | --- |
| 200 | Success |
| 400 | Invalid input; the body says which field and why |
| 404 | Site or URL not found |
| 405 | Wrong HTTP method (for example `GET /api/analyze`) |
| 500 | Server error (for example the database is not reachable) |