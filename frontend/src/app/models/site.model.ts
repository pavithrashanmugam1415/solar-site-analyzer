// Shapes of the JSON returned by the Django API

export interface SiteScore {
  site_id: number;
  site_name: string;
  latitude: number;
  longitude: number;
  area_sqm: number;
  solar_irradiance_kwh: number;
  grid_distance_km: number;
  slope_degrees: number;
  road_distance_km: number;
  land_type: string;
  region: string;
  solar_irradiance_score: number;
  area_score: number;
  grid_distance_score: number;
  slope_score: number;
  infrastructure_score: number;
  total_score: number;
  category: string;
}

export interface PagedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface BreakdownItem {
  factor: string;
  score: number;
  weight: number;
  weighted_score: number;
}

export interface SiteDetail {
  site_id: number;
  site_name: string;
  latitude: number;
  longitude: number;
  area_sqm: number;
  solar_irradiance_kwh: number;
  grid_distance_km: number;
  slope_degrees: number;
  road_distance_km: number;
  elevation_m: number;
  land_type: string;
  region: string;
  analysis: {
    total_score: number;
    category: string;
    rank: number;
    total_sites: number;
    breakdown: BreakdownItem[];
    analysis_timestamp: string;
  } | null;
}

export interface Weights {
  solar: number;
  area: number;
  grid: number;
  slope: number;
  infrastructure: number;
}

export interface Statistics {
  summary: {
    total_sites: number;
    average_score: number;
    min_score: number;
    max_score: number;
    std_dev: number;
    avg_solar: number;
    avg_area: number;
    avg_grid: number;
    avg_slope: number;
    avg_infrastructure: number;
  };
  category_distribution: Record<string, number>;
  by_land_type: { land_type: string; site_count: number; average_score: number }[];
  current_weights: Weights;
  top_10: SiteScore[];
}

export interface SiteFilters {
  minScore?: number | null;
  maxScore?: number | null;
  landType?: string;
  ordering?: string;
}