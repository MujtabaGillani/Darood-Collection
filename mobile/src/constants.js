// Chart time-range presets (mirror the web dashboard buttons).
export const RANGES = [
  { key: 'today', label: 'Today', g: 'day', days: 1 },
  { key: '7d', label: '7 Days', g: 'day', days: 7 },
  { key: 'weeks', label: 'Weeks', g: 'week', days: 84 },
  { key: 'months', label: 'Months', g: 'month', days: 365 },
  { key: 'years', label: 'Years', g: 'year', days: null },
];

export function rangeParams(range, extra = {}) {
  const r = RANGES.find((x) => x.key === range) || RANGES[1];
  const params = { granularity: r.g, ...extra };
  if (r.days) params.days = r.days;
  return params;
}

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Format a start/end ISO pair as "3 Jul – 9 Jul" (adds the year only when the
// range spans different years).
export function formatRange(startISO, endISO) {
  if (!startISO || !endISO) return '';
  const fmt = (iso, withYear) => {
    const [y, m, d] = iso.split('-');
    return `${parseInt(d, 10)} ${MON[parseInt(m, 10) - 1]}${withYear ? ` ${y}` : ''}`;
  };
  const spansYears = startISO.slice(0, 4) !== endISO.slice(0, 4);
  return `${fmt(startISO, spansYears)} – ${fmt(endISO, spansYears)}`;
}
