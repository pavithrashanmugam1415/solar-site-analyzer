from django.db import models


class Site(models.Model):
    """A possible location for a solar farm (one row from the CSV)."""
    site_id = models.AutoField(primary_key=True)
    site_name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    area_sqm = models.IntegerField()
    solar_irradiance_kwh = models.DecimalField(max_digits=4, decimal_places=2)
    grid_distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    slope_degrees = models.DecimalField(max_digits=4, decimal_places=2)
    road_distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    elevation_m = models.IntegerField()
    land_type = models.CharField(max_length=50, db_index=True)
    region = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sites"

    def __str__(self):
        return self.site_name


class AnalysisParameter(models.Model):
    """One weight used in the score formula (e.g. solar = 0.35)."""
    param_id = models.AutoField(primary_key=True)
    parameter_name = models.CharField(max_length=100, unique=True)
    weight_value = models.DecimalField(max_digits=4, decimal_places=3)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analysis_parameters"


class AnalysisResult(models.Model):
    """The calculated scores for one site, plus the weights used."""
    result_id = models.AutoField(primary_key=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE,
                             related_name="results", db_column="site_id")
    solar_irradiance_score = models.DecimalField(max_digits=5, decimal_places=2)
    area_score = models.DecimalField(max_digits=5, decimal_places=2)
    grid_distance_score = models.DecimalField(max_digits=5, decimal_places=2)
    slope_score = models.DecimalField(max_digits=5, decimal_places=2)
    infrastructure_score = models.DecimalField(max_digits=5, decimal_places=2)
    total_suitability_score = models.DecimalField(max_digits=5, decimal_places=2, db_index=True)
    analysis_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    parameters_snapshot = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "analysis_results"