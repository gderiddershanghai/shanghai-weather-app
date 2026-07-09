// THE chart state store: the single source of truth that both Story mode
// (scroll-driven step presets) and Explore mode (UI controls) drive.
// Chart components only ever READ this store — they never care who set it.

import { writable } from 'svelte/store';
import type { DailyMetric } from '$lib/data/daily';

export type ChartType = 'climatology' | 'timeseries' | 'heatmap' | 'scatter' | 'aqiScale';
export type TempMode = 'real' | 'feels_like';
export type DotThreshold = 'p99' | 'p95' | 'none';
export type DotTail = 'hot' | 'cold' | 'both';
export type EventOverlay = 'curated' | 'heat_wave' | 'cold_wave' | 'rain' | 'wind';
/** 0=DJF 1=MAM 2=JJA 3=SON */
export type Season = 0 | 1 | 2 | 3;

export interface ChartState {
	chartType: ChartType;
	tempMode: TempMode;
	/** metric for timeseries/heatmap views */
	metric: DailyMetric | 'pm25';
	/** climatology: DOY [1,365]; timeseries/heatmap/scatter: year range */
	xDomain: [number, number];
	/** null = auto-fit */
	yDomain: [number, number] | null;
	showBand: boolean;
	showMedian: boolean;
	showP99: boolean;
	dotThreshold: DotThreshold;
	dotTail: DotTail;
	highlightYears: number[];
	overlayEvents: EventOverlay[];
	/** rolling mean window (days) for timeseries; 1 = raw */
	rollingWindow: 1 | 30 | 365;
	scatterX: 'tmax' | 'tmin';
	scatterY: 'pm25' | 'o3';
	seasonFilter: Season | null;
	activeAnnotations: string[];
	/** curated event id whose EventCard is open */
	focusedEventId: string | null;
}

export const CHART_DEFAULTS: ChartState = {
	chartType: 'climatology',
	tempMode: 'real',
	metric: 'tmax',
	xDomain: [1, 365],
	yDomain: null,
	showBand: true,
	showMedian: true,
	showP99: false,
	dotThreshold: 'none',
	dotTail: 'both',
	highlightYears: [],
	overlayEvents: [],
	rollingWindow: 1,
	scatterX: 'tmax',
	scatterY: 'pm25',
	seasonFilter: null,
	activeAnnotations: [],
	focusedEventId: null
};

export const EXPLORE_DEFAULTS: ChartState = {
	...CHART_DEFAULTS,
	dotThreshold: 'p99',
	overlayEvents: ['curated']
};

export const chartState = writable<ChartState>({ ...CHART_DEFAULTS });

/**
 * Merge a partial preset into the current state. Story steps use partial
 * presets so unspecified keys carry over — consecutive steps morph naturally.
 */
export function applyPreset(preset: Partial<ChartState>): void {
	chartState.update((s) => ({ ...s, ...preset }));
}

export function resetChart(to: ChartState = CHART_DEFAULTS): void {
	chartState.set({ ...to });
}
