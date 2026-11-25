// import { Routes } from '@angular/router';

// export const routes: Routes = [];

import { Routes } from '@angular/router';

// Each page is lazy-loaded: its code (Leaflet, Chart.js) downloads only when the page is opened
export const routes: Routes = [
  { path: '', redirectTo: 'map', pathMatch: 'full' },
  {
    path: 'map',
    loadComponent: () => import('./pages/map-page/map-page').then((m) => m.MapPage),
    title: 'Map | Solar Site Analyzer',
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard').then((m) => m.Dashboard),
    title: 'Dashboard | Solar Site Analyzer',
  },
  { path: '**', redirectTo: 'map' },
];