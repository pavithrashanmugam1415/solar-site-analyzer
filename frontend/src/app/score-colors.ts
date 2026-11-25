// One colour per score category, used by the map, legend and tables
export const CATEGORY_COLORS: Record<string, string> = {
  'Excellent': '#1a9850',
  'Good': '#91cf60',
  'Fair': '#fee08b',
  'Poor': '#fc8d59',
  'Very Poor': '#d73027',
};

export const CATEGORIES = Object.keys(CATEGORY_COLORS);

export function colorFor(category: string): string {
  return CATEGORY_COLORS[category] ?? '#999999';
}