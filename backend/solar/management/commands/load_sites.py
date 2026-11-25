import csv

from django.core.management.base import BaseCommand

from solar.models import AnalysisParameter, Site

# Default weights from the assessment (they add up to 1.0)
DEFAULT_WEIGHTS = {
    "solar_irradiance_weight": 0.35,
    "area_weight": 0.25,
    "grid_distance_weight": 0.20,
    "slope_weight": 0.15,
    "infrastructure_weight": 0.05,
}


class Command(BaseCommand):
    help = "Load solar sites from the CSV file and add default weights"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to solar_sites_data.csv")

    def handle(self, *args, **options):
        # 1. Default weights (only added if missing)
        for name, value in DEFAULT_WEIGHTS.items():
            AnalysisParameter.objects.get_or_create(
                parameter_name=name, defaults={"weight_value": value}
            )

        # 2. Sites from CSV (update if exists, else create -> safe to run again)
        count = 0
        with open(options["csv_path"], newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                Site.objects.update_or_create(
                    site_id=int(row["site_id"]),
                    defaults={
                        "site_name": row["site_name"],
                        "latitude": row["latitude"],
                        "longitude": row["longitude"],
                        "area_sqm": int(row["area_sqm"]),
                        "solar_irradiance_kwh": row["solar_irradiance_kwh"],
                        "grid_distance_km": row["grid_distance_km"],
                        "slope_degrees": row["slope_degrees"],
                        "road_distance_km": row["road_distance_km"],
                        "elevation_m": int(row["elevation_m"]),
                        "land_type": row["land_type"],
                        "region": row["region"],
                    },
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Loaded {count} sites"))