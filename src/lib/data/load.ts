// Fetch + cache derived JSON payloads (built by pipeline/build_derived.py).
// All paths go through the GitHub Pages base path.

import { base } from '$app/paths';

export interface Climatology {
	doy: number[];
	date_ref: string[];
	tmax_p50: (number | null)[];
	tmax_p95: (number | null)[];
	tmax_p99: (number | null)[];
	tmin_p50: (number | null)[];
	tmin_p05: (number | null)[];
	tmin_p01: (number | null)[];
	atmax_p50: (number | null)[];
	atmax_p95: (number | null)[];
	atmax_p99: (number | null)[];
	atmin_p50: (number | null)[];
	atmin_p05: (number | null)[];
	atmin_p01: (number | null)[];
}

export interface CompactTable {
	columns: string[];
	rows: (number | null)[][];
}

export interface OutliersTable extends CompactTable {
	series_enum: string[];
}

export interface YearlyTable extends CompactTable {
	/** anomaly reference period, e.g. [1980, 2009] */
	baseline: [number, number];
}

export interface TempEvent {
	id: string;
	type: string;
	start: string;
	end: string;
	days: number;
	peak_date: string;
	peak_value: number;
	peak_severity: number;
	year: number;
}

export interface EventLink {
	outlet: string | null;
	headline: string | null;
	url: string | null;
}

export interface CuratedEvent {
	id: string;
	category: 'HOT' | 'COLD' | 'RAIN' | 'TYPHOON' | 'AQI';
	date: string;
	start: string;
	end: string;
	days: number;
	doy: number;
	year: number;
	real_c: number | null;
	feels_c: number | null;
	note: { en: string | null; zh: string | null };
	links: { en: EventLink | null; zh: EventLink | null };
	image: string | null;
}

export interface Meta {
	built_at: string;
	weather: { start: string; end: string; rows: number };
	aqi?: { start: string; end: string; rows: number; pm25_start: string };
	counts: { outlier_days: number; temp_events: number; curated_events: number };
	config: Record<string, number>;
}

const cache = new Map<string, Promise<unknown>>();

function loadJson<T>(name: string): Promise<T> {
	let promise = cache.get(name);
	if (!promise) {
		promise = fetch(`${base}/data/derived/${name}`).then((r) => {
			if (!r.ok) throw new Error(`failed to load ${name}: ${r.status}`);
			return r.json();
		});
		cache.set(name, promise);
	}
	return promise as Promise<T>;
}

export const loadMeta = () => loadJson<Meta>('meta.json');
export const loadClimatology = () => loadJson<Climatology>('climatology.json');
export const loadDaily = () => loadJson<CompactTable>('daily.json');
export const loadOutliers = () => loadJson<OutliersTable>('outliers.json');
export const loadTempEvents = () => loadJson<TempEvent[]>('temp-events.json');
export const loadCuratedEvents = () => loadJson<CuratedEvent[]>('events-curated.json');
export const loadYearly = () => loadJson<YearlyTable>('yearly.json');

/** Resolve an event image path (relative in JSON) against the base path. */
export const eventImageUrl = (image: string | null) =>
	image ? `${base}/data/derived/${image}` : null;
