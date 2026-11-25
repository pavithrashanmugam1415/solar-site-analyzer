import csv

from django.db.models import Avg, Count, Max, Min, StdDev
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Site
from .scoring import score_category
from .serializers import SiteScoreSerializer, SiteSerializer, WeightsSerializer
from .services import get_current_weights, latest_results, run_analysis, save_weights

# Allowed values for ?ordering= (a whitelist, so users cannot sort by any column)
ORDERING_FIELDS = {
    "score": "total_suitability_score",
    "name": "site__site_name",
    "area": "site__area_sqm",
    "solar": "site__solar_irradiance_kwh",
    "grid_distance": "site__grid_distance_km",
    "slope": "site__slope_degrees",
}


def get_number_param(request, name, minimum=0, maximum=100):
    """Read an optional number from the query string and check its range."""
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return None
    try:
        value = float(raw)
    except ValueError:
        raise ValidationError({name: "Must be a number."})
    if not minimum <= value <= maximum:
        raise ValidationError({name: f"Must be between {minimum} and {maximum}."})
    return value


def filtered_results(request):
    """Latest results filtered by min_score, max_score, land_type and sorted by ordering."""
    queryset = latest_results()
    min_score = get_number_param(request, "min_score")
    max_score = get_number_param(request, "max_score")
    if min_score is not None and max_score is not None and min_score > max_score:
        raise ValidationError({"min_score": "Must not be greater than max_score."})
    if min_score is not None:
        queryset = queryset.filter(total_suitability_score__gte=min_score)
    if max_score is not None:
        queryset = queryset.filter(total_suitability_score__lte=max_score)

    land_type = request.query_params.get("land_type")
    if land_type:
        queryset = queryset.filter(site__land_type=land_type)

    ordering = request.query_params.get("ordering", "-score")
    field = ORDERING_FIELDS.get(ordering.lstrip("-"))
    if field is None:
        raise ValidationError({"ordering": f"Use one of: {', '.join(ORDERING_FIELDS)} (prefix - for descending)."})
    return queryset.order_by(("-" if ordering.startswith("-") else "") + field)


class SiteListView(APIView):
    """GET /api/sites - all sites with their latest scores (filter, sort, paginate)."""

    def get(self, request):
        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(filtered_results(request), request, view=self)
        return paginator.get_paginated_response(SiteScoreSerializer(page, many=True).data)


class SiteDetailView(APIView):
    """GET /api/sites/<id> - one site with the full score breakdown."""

    def get(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        result = site.results.order_by("-result_id").first()
        data = SiteSerializer(site).data
        if result is None:
            data["analysis"] = None
            return Response(data)

        weights = result.parameters_snapshot or get_current_weights()
        factors = {
            "solar": float(result.solar_irradiance_score),
            "area": float(result.area_score),
            "grid": float(result.grid_distance_score),
            "slope": float(result.slope_score),
            "infrastructure": float(result.infrastructure_score),
        }
        total = float(result.total_suitability_score)
        rank = latest_results().filter(total_suitability_score__gt=total).count() + 1
        data["analysis"] = {
            "total_score": total,
            "category": score_category(total),
            "rank": rank,
            "total_sites": Site.objects.count(),
            "breakdown": [
                {
                    "factor": key,
                    "score": score,
                    "weight": weights[key],
                    "weighted_score": round(score * weights[key], 2),
                }
                for key, score in factors.items()
            ],
            "analysis_timestamp": result.analysis_timestamp,
        }
        return Response(data)


class AnalyzeView(APIView):
    """POST /api/analyze - recalculate all scores with custom weights."""

    def post(self, request):
        serializer = WeightsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        weights = serializer.validated_data["weights"]
        save_weights(weights)
        count = run_analysis(weights)
        top_10 = latest_results().order_by("-total_suitability_score")[:10]
        return Response(
            {
                "message": f"Recalculated scores for {count} sites.",
                "weights": weights,
                "top_10": SiteScoreSerializer(top_10, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class StatisticsView(APIView):
    """GET /api/statistics - summary numbers across all sites."""

    def get(self, request):
        results = latest_results()
        summary = results.aggregate(
            total_sites=Count("result_id"),
            average_score=Avg("total_suitability_score"),
            min_score=Min("total_suitability_score"),
            max_score=Max("total_suitability_score"),
            std_dev=StdDev("total_suitability_score"),
            avg_solar=Avg("solar_irradiance_score"),
            avg_area=Avg("area_score"),
            avg_grid=Avg("grid_distance_score"),
            avg_slope=Avg("slope_score"),
            avg_infrastructure=Avg("infrastructure_score"),
        )
        summary = {k: round(float(v), 2) if v is not None else None for k, v in summary.items()}
        summary["total_sites"] = int(summary["total_sites"] or 0)

        # How many sites fall in each category band
        bands = {"Excellent": 0, "Good": 0, "Fair": 0, "Poor": 0, "Very Poor": 0}
        for score in results.values_list("total_suitability_score", flat=True):
            bands[score_category(float(score))] += 1

        by_land_type = [
            {
                "land_type": row["site__land_type"],
                "site_count": row["site_count"],
                "average_score": round(float(row["average_score"]), 2),
            }
            for row in results.values("site__land_type")
            .annotate(site_count=Count("result_id"), average_score=Avg("total_suitability_score"))
            .order_by("-average_score")
        ]

        return Response({
            "summary": summary,
            "category_distribution": bands,
            "by_land_type": by_land_type,
            "current_weights": get_current_weights(),
            "top_10": SiteScoreSerializer(
                results.order_by("-total_suitability_score")[:10], many=True
            ).data,
        })


class ExportView(APIView):
    """GET /api/export?format=csv|json&min_score=70 - download results."""

    def get(self, request):
        export_format = request.query_params.get("format", "json").lower()
        if export_format not in ("csv", "json"):
            raise ValidationError({"format": "Use csv or json."})

        rows = SiteScoreSerializer(filtered_results(request), many=True).data

        if export_format == "json":
            response = Response(rows)
            response["Content-Disposition"] = 'attachment; filename="solar_sites.json"'
            return response

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="solar_sites.csv"'
        writer = csv.DictWriter(response, fieldnames=SiteScoreSerializer.Meta.fields)
        writer.writeheader()
        writer.writerows(rows)
        return response