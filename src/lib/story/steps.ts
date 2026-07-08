// Story steps as data. Each step is a PARTIAL chart preset — unspecified keys
// carry over from the previous step, so consecutive steps morph naturally.
// Copy lives in i18n/copy.json under "steps.<id>.title" / "steps.<id>.body".

import type { ChartState } from '$lib/stores/chartState';

export interface StoryStep {
	id: string;
	chapter: 'hook' | 'heat' | 'cold' | 'rain' | 'aqi' | 'interplay' | 'explore';
	chart: Partial<ChartState>;
	/** annotation ids to show (sets chart.activeAnnotations) */
	annotations?: string[];
	/** curated event id whose EventCard opens on activation */
	focusEvent?: string;
	/** payloads to prefetch when the PREVIOUS step activates */
	dataNeeds?: ('daily' | 'aqi' | 'tempAqi')[];
}

// Summer ≈ Jun–Sep, deep winter ≈ Jan–Mar (DOY ranges)
const SUMMER: [number, number] = [152, 273];
const WINTER: [number, number] = [1, 90];
const FULL_YEAR: [number, number] = [1, 365];

export const steps: StoryStep[] = [
	// --- Hook -----------------------------------------------------------------
	{
		id: 'hook-1',
		chapter: 'hook',
		chart: {
			chartType: 'climatology',
			tempMode: 'real',
			xDomain: FULL_YEAR,
			showBand: true,
			showMedian: true,
			showP99: false,
			dotThreshold: 'none',
			dotTail: 'both',
			focusedEventId: null
		}
	},
	{
		id: 'hook-2',
		chapter: 'hook',
		chart: {
			dotThreshold: 'p99',
			overlayEvents: ['curated']
		}
	},

	// --- Heat -------------------------------------------------------------------
	{
		id: 'heat-1',
		chapter: 'heat',
		chart: {
			xDomain: SUMMER,
			dotTail: 'hot',
			tempMode: 'real',
			focusedEventId: null
		}
	},
	{
		id: 'heat-2',
		chapter: 'heat',
		chart: {},
		focusEvent: 'hot-2024-08-03'
	},
	{
		id: 'heat-3',
		chapter: 'heat',
		chart: { tempMode: 'feels_like' },
		focusEvent: 'hot-1988-07-17'
	},

	// --- Cold -------------------------------------------------------------------
	{
		id: 'cold-1',
		chapter: 'cold',
		chart: {
			xDomain: WINTER,
			dotTail: 'cold',
			tempMode: 'real',
			focusedEventId: null
		}
	},
	{
		id: 'cold-2',
		chapter: 'cold',
		chart: {},
		focusEvent: 'cold-2016-01-24'
	},
	{
		id: 'cold-3',
		chapter: 'cold',
		chart: { tempMode: 'feels_like' },
		focusEvent: 'cold-1980-01-31'
	},

	// --- Rain & storms -----------------------------------------------------------
	{
		id: 'rain-1',
		chapter: 'rain',
		chart: {
			chartType: 'heatmap',
			metric: 'prcp',
			focusedEventId: null
		},
		dataNeeds: ['daily']
	},
	{
		id: 'rain-2',
		chapter: 'rain',
		chart: {
			chartType: 'timeseries',
			metric: 'prcp',
			rollingWindow: 365,
			xDomain: [1980, 2026]
		}
	},
	{
		id: 'rain-3',
		chapter: 'rain',
		chart: {
			metric: 'gmax',
			rollingWindow: 1
		}
	},

	// --- Air --------------------------------------------------------------------
	{
		id: 'aqi-1',
		chapter: 'aqi',
		chart: {
			chartType: 'heatmap',
			metric: 'pm25'
		}
	},
	{
		id: 'aqi-2',
		chapter: 'aqi',
		chart: {}
	},

	// --- Interplay ----------------------------------------------------------------
	{
		id: 'interplay-1',
		chapter: 'interplay',
		chart: {
			chartType: 'scatter',
			scatterY: 'pm25',
			seasonFilter: null
		}
	},
	{
		id: 'interplay-2',
		chapter: 'interplay',
		chart: {
			seasonFilter: 0
		}
	},

	// --- Wrap ---------------------------------------------------------------------
	{
		id: 'wrap-1',
		chapter: 'explore',
		chart: {
			chartType: 'climatology',
			xDomain: FULL_YEAR,
			tempMode: 'real',
			dotTail: 'both',
			dotThreshold: 'p99',
			seasonFilter: null,
			focusedEventId: null
		}
	}
];

export const stepById = new Map(steps.map((s) => [s.id, s]));
