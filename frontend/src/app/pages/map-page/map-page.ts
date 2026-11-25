import { AfterViewInit, Component, OnDestroy, computed, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';

import { SiteDetail, SiteScore } from '../../models/site.model';
import { SiteService } from '../../services/site.service';
import { CATEGORIES, CATEGORY_COLORS, colorFor } from '../../score-colors';

@Component({
  selector: 'app-map-page',
  imports: [FormsModule, DecimalPipe],
  templateUrl: './map-page.html',
  styleUrl: './map-page.css',
})
export class MapPage implements AfterViewInit, OnDestroy {
  private siteService = inject(SiteService);
  private map?: L.Map;
  private markerLayer = L.layerGroup();

  // Page state (signals update the screen automatically)
  sites = signal<SiteScore[]>([]);
  allLandTypes = signal<string[]>([]);
  selected = signal<SiteDetail | null>(null);
  loading = signal(false);
  error = signal('');

  // Filter values bound to the form
  minScore = 0;
  landType = '';
  ordering = '-score';

  categories = CATEGORIES;
  categoryColors = CATEGORY_COLORS;
  colorFor = colorFor;
  siteCount = computed(() => this.sites().length);

  ngAfterViewInit(): void {
    this.initMap();
    this.loadSites(true);
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  /** Create the Leaflet map centred on the Coimbatore / Tiruppur area. */
  private initMap(): void {
    this.map = L.map('site-map').setView([11.0, 77.1], 9);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(this.map);
    this.markerLayer.addTo(this.map);
  }

  /** Fetch sites from the API using the current filters. */
  loadSites(firstLoad = false): void {
    this.loading.set(true);
    this.error.set('');
    this.siteService
      .getSites({ minScore: this.minScore, landType: this.landType, ordering: this.ordering })
      .subscribe({
        next: (response) => {
          this.sites.set(response.results);
          if (firstLoad) {
            const types = [...new Set(response.results.map((s) => s.land_type))].sort();
            this.allLandTypes.set(types);
          }
          this.drawMarkers(response.results, firstLoad);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('Could not load sites. Is the Django server running on port 8000?');
          this.loading.set(false);
        },
      });
  }

  /** One coloured circle per site; colour = score category. */
  private drawMarkers(sites: SiteScore[], fitToSites: boolean): void {
    this.markerLayer.clearLayers();
    for (const site of sites) {
      const marker = L.circleMarker([site.latitude, site.longitude], {
        radius: 9,
        color: '#333333',
        weight: 1,
        fillColor: colorFor(site.category),
        fillOpacity: 0.9,
      });
      marker.bindTooltip(`${site.site_name}: ${site.total_score.toFixed(1)}`);
      marker.on('click', () => this.selectSite(site.site_id));
      marker.addTo(this.markerLayer);
    }
    if (fitToSites && sites.length && this.map) {
      const bounds = L.latLngBounds(sites.map((s) => [s.latitude, s.longitude] as L.LatLngTuple));
      this.map.fitBounds(bounds, { padding: [30, 30] });
    }
  }

  /** Load the full score breakdown for one site and zoom to it. */
  selectSite(id: number): void {
    this.siteService.getSite(id).subscribe({
      next: (detail) => {
        this.selected.set(detail);
        this.map?.setView([detail.latitude, detail.longitude], 12);
      },
      error: () => this.error.set('Could not load site details.'),
    });
  }

  clearFilters(): void {
    this.minScore = 0;
    this.landType = '';
    this.ordering = '-score';
    this.loadSites();
  }

  closeDetail(): void {
    this.selected.set(null);
  }
}