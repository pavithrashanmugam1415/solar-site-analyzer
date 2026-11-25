from django.core.management.base import BaseCommand

from solar.services import run_analysis


class Command(BaseCommand):
    help = "Calculate suitability scores for all sites using the stored weights"

    def handle(self, *args, **options):
        count = run_analysis()
        self.stdout.write(self.style.SUCCESS(f"Scored {count} sites"))