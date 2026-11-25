import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from '../api.config';
import {
  PagedResponse, SiteDetail, SiteFilters, SiteScore, Statistics, Weights,
} from '../models/site.model';

/** All calls to the Django API live here, so components stay simple. */
@Injectable({ providedIn: 'root' })
export class SiteService {
  private http = inject(HttpClient);

  getSites(filters: SiteFilters = {}): Observable<PagedResponse<SiteScore>> {
    return this.http.get<PagedResponse<SiteScore>>(`${API_URL}/sites`, {
      params: this.toParams(filters),
    });
  }

  getSite(id: number): Observable<SiteDetail> {
    return this.http.get<SiteDetail>(`${API_URL}/sites/${id}`);
  }

  getStatistics(): Observable<Statistics> {
    return this.http.get<Statistics>(`${API_URL}/statistics`);
  }

  analyze(weights: Weights): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${API_URL}/analyze`, { weights });
  }

  /** Link for downloading results; the browser handles the file download. */
  exportUrl(format: 'csv' | 'json', minScore?: number | null): string {
    const params = new HttpParams({ fromObject: { format } });
    const withMin = minScore != null ? params.set('min_score', minScore) : params;
    return `${API_URL}/export?${withMin.toString()}`;
  }

  private toParams(filters: SiteFilters): HttpParams {
    let params = new HttpParams().set('limit', 100);
    if (filters.minScore != null) params = params.set('min_score', filters.minScore);
    if (filters.maxScore != null) params = params.set('max_score', filters.maxScore);
    if (filters.landType) params = params.set('land_type', filters.landType);
    if (filters.ordering) params = params.set('ordering', filters.ordering);
    return params;
  }
}