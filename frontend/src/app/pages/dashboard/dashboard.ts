import { Component, ElementRef, OnDestroy, OnInit, computed, inject, signal, viewChild } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart, registerables } from 'chart.js';

import { Statistics, Weights } from '../../models/site.model';
import { SiteService } from '../../services/site.service';
import { CATEGORIES, colorFor } from '../../score-colors';

Chart.register(...registerables);

/** Labels shown next to each weight slider. */
const WEIGHT_LABELS: Record<keyof Weights, string> = {
  solar: 'Solar irradiance',
  area: 'Land area',
  grid: 'Grid distance',
  slope: 'Slope',
  infrastructure: 'Road access',
};

@Component({
  selector: 'app-dashboard',
  imports: [FormsModule, DecimalPipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit, OnDestroy {
  private siteService = inject(SiteService);
  private charts: Chart[] = [];

  categoryCanvas = viewChild.required<ElementRef<HTMLCanvasElement>>('categoryCanvas');
  landTypeCanvas = viewChild.required<ElementRef<HTMLCanvasElement>>('landTypeCanvas');
  factorCanvas = viewChild.required<ElementRef<HTMLCanvasElement>>('factorCanvas');

  stats = signal<Statistics | null>(null);
  error = signal('');
  saving = signal(false);
  message = signal('');

  // Weights form (edited with sliders)
  weights = signal<Weights>({ solar: 0.35, area: 0.25, grid: 0.2, slope: 0.15, infrastructure: 0.05 });
  weightKeys = Object.keys(WEIGHT_LABELS) as (keyof Weights)[];
  weightLabels = WEIGHT_LABELS;
  weightTotal = computed(() => {
    const w = this.weights();
    return Math.round((w.solar + w.area + w.grid + w.slope + w.infrastructure) * 100) / 100;
  });
  weightsValid = computed(() => Math.abs(this.weightTotal() - 1) < 0.001);

  exportMinScore: number | null = null;
  colorFor = colorFor;

  ngOnInit(): void {
    this.loadStatistics();
  }

  ngOnDestroy(): void {
    this.charts.forEach((chart) => chart.destroy());
  }

  loadStatistics(): void {
    this.error.set('');
    this.siteService.getStatistics().subscribe({
      next: (stats) => {
        this.stats.set(stats);
        this.weights.set({ ...stats.current_weights });
        this.drawCharts(stats);
      },
      error: () => this.error.set('Could not load statistics. Is the Django server running on port 8000?'),
    });
  }

  setWeight(key: keyof Weights, value: number): void {
    this.weights.update((w) => ({ ...w, [key]: Number(value) }));
  }

  resetWeights(): void {
    this.weights.set({ solar: 0.35, area: 0.25, grid: 0.2, slope: 0.15, infrastructure: 0.05 });
  }

  /** Send the weights to POST /api/analyze, then reload the numbers. */
  recalculate(): void {
    if (!this.weightsValid()) return;
    this.saving.set(true);
    this.message.set('');
    this.siteService.analyze(this.weights()).subscribe({
      next: (response) => {
        this.message.set(response.message);
        this.saving.set(false);
        this.loadStatistics();
      },
      error: (err) => {
        const detail = err.error?.weights ?? 'Recalculation failed.';
        this.message.set(Array.isArray(detail) ? detail.join(' ') : String(detail));
        this.saving.set(false);
      },
    });
  }

  download(format: 'csv' | 'json'): void {
    window.open(this.siteService.exportUrl(format, this.exportMinScore), '_blank');
  }

  /** (Re)draw the three charts with the latest statistics. */
  private drawCharts(stats: Statistics): void {
    this.charts.forEach((chart) => chart.destroy());

    const categoryChart = new Chart(this.categoryCanvas().nativeElement, {
      type: 'bar',
      data: {
        labels: CATEGORIES,
        datasets: [{
          label: 'Number of sites',
          data: CATEGORIES.map((c) => stats.category_distribution[c] ?? 0),
          backgroundColor: CATEGORIES.map(colorFor),
        }],
      },
      options: { responsive: true, plugins: { legend: { display: false } } },
    });

    const landTypeChart = new Chart(this.landTypeCanvas().nativeElement, {
      type: 'bar',
      data: {
        labels: stats.by_land_type.map((row) => `${row.land_type} (${row.site_count})`),
        datasets: [{
          label: 'Average score',
          data: stats.by_land_type.map((row) => row.average_score),
          backgroundColor: '#1a73e8',
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { x: { min: 0, max: 100 } },
      },
    });

    // Which factors are strong or weak across all sites (average score out of 100)
    const factorChart = new Chart(this.factorCanvas().nativeElement, {
      type: 'bar',
      data: {
        labels: ['Solar', 'Area', 'Grid distance', 'Slope', 'Road access'],
        datasets: [{
          label: 'Average factor score',
          data: [
            stats.summary.avg_solar, stats.summary.avg_area, stats.summary.avg_grid,
            stats.summary.avg_slope, stats.summary.avg_infrastructure,
          ],
          backgroundColor: ['#fbbc04', '#34a853', '#1a73e8', '#9334e6', '#ea4335'],
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { min: 0, max: 100 } },
      },
    });

    this.charts = [categoryChart, landTypeChart, factorChart];
  }
}