// Shared sequential ramps — every heatmap starts on the band beige (so the
// lowest value is visibly "on the paper", distinct from coverage-hidden blank
// cells) and ends in its metric family's deep anchor. One definition, used
// everywhere, per the same-category-same-color rule. See review/color-audit.md.
import { interpolateLab } from 'd3';

const RAMP_FLOOR = '#f3e8d2'; // --color-band

export const rampHeat = interpolateLab(RAMP_FLOOR, '#8a1f2b'); // deep --color-hot
export const rampRain = interpolateLab(RAMP_FLOOR, '#0e5a50'); // deep --chapter-rain teal
export const rampWind = interpolateLab(RAMP_FLOOR, '#4a5568'); // --color-wind slate
export const rampHaze = interpolateLab(RAMP_FLOOR, '#452a6b'); // deep --chapter-aqi purple
