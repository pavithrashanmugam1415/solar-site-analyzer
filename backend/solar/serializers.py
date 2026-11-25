from rest_framework import serializers

from .models import AnalysisResult, Site
from .scoring import score_category, validate_weights


class SiteSerializer(serializers.ModelSerializer):
    """All raw data for one site (from the CSV)."""

    class Meta:
        model = Site
        fields = [
            "site_id", "site_name", "latitude", "longitude", "area_sqm",
            "solar_irradiance_kwh", "grid_distance_km", "slope_degrees",
            "road_distance_km", "elevation_m", "land_type", "region",
        ]


class SiteScoreSerializer(serializers.ModelSerializer):
    """
    One row for lists, the map and exports: basic site info + latest scores.
    Built from an AnalysisResult, reading the site fields through `site`.
    """
    site_id = serializers.IntegerField(source="site.site_id")
    site_name = serializers.CharField(source="site.site_name")
    latitude = serializers.FloatField(source="site.latitude")
    longitude = serializers.FloatField(source="site.longitude")
    area_sqm = serializers.IntegerField(source="site.area_sqm")
    solar_irradiance_kwh = serializers.FloatField(source="site.solar_irradiance_kwh")
    grid_distance_km = serializers.FloatField(source="site.grid_distance_km")
    slope_degrees = serializers.FloatField(source="site.slope_degrees")
    road_distance_km = serializers.FloatField(source="site.road_distance_km")
    land_type = serializers.CharField(source="site.land_type")
    region = serializers.CharField(source="site.region")
    total_score = serializers.FloatField(source="total_suitability_score")
    category = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisResult
        fields = [
            "site_id", "site_name", "latitude", "longitude", "area_sqm",
            "solar_irradiance_kwh", "grid_distance_km", "slope_degrees",
            "road_distance_km", "land_type", "region",
            "solar_irradiance_score", "area_score", "grid_distance_score",
            "slope_score", "infrastructure_score", "total_score", "category",
        ]

    def get_category(self, obj):
        return score_category(float(obj.total_suitability_score))


class WeightsSerializer(serializers.Serializer):
    """Validates the body of POST /api/analyze: {"weights": {...}}."""
    weights = serializers.DictField(child=serializers.FloatField())

    def validate_weights(self, value):
        errors = validate_weights(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value