// Light client-side transforms over the compact tables. Anything statistical
// (quantiles, smoothing, event detection) stays in the Python pipeline.

import type { CompactTable } from './load';
import { COL, splitDateInt } from './daily';

export interface XY {
	x: number;
	y: number | null;
}

/** dateInt -> decimal year (for time-series x scales), e.g. 20160124 -> 2016.063 */
export function decimalYear(dateInt: number): number {
	const { year, month, day } = splitDateInt(dateInt);
	const doy = Math.min((month - 1) * 30.44 + day, 365);
	return year + doy / 365;
}

/** Extract one metric as {x: decimalYear, y} points, filtered to a year range. */
export function metricSeries(
	table: CompactTable,
	col: number,
	yearRange: [number, number]
): XY[] {
	const out: XY[] = [];
	for (const row of table.rows) {
		const dateInt = row[COL.date] as number;
		const year = Math.floor(dateInt / 10000);
		if (year < yearRange[0] || year > yearRange[1]) continue;
		out.push({ x: decimalYear(dateInt), y: row[col] as number | null });
	}
	return out;
}

/** Centered rolling mean, ignoring nulls; window in points (≈days). */
export function rollingMean(points: XY[], window: number): XY[] {
	if (window <= 1) return points;
	const half = Math.floor(window / 2);
	const out: XY[] = new Array(points.length);
	// prefix sums (O(n) for any window size)
	const prefix: number[] = new Array(points.length + 1).fill(0);
	const counts: number[] = new Array(points.length + 1).fill(0);
	for (let i = 0; i < points.length; i++) {
		const y = points[i].y;
		prefix[i + 1] = prefix[i] + (y ?? 0);
		counts[i + 1] = counts[i] + (y == null ? 0 : 1);
	}
	for (let i = 0; i < points.length; i++) {
		const lo = Math.max(0, i - half);
		const hi = Math.min(points.length, i + half + 1);
		const sum = prefix[hi] - prefix[lo];
		const count = counts[hi] - counts[lo];
		out[i] = { x: points[i].x, y: count > 0 ? sum / count : null };
	}
	return out;
}

/** Count of days per year matching a predicate on one column. */
export function daysPerYear(
	table: CompactTable,
	col: number,
	predicate: (v: number) => boolean
): { year: number; count: number }[] {
	const byYear = new Map<number, number>();
	for (const row of table.rows) {
		const v = row[col] as number | null;
		if (v == null) continue;
		const year = Math.floor((row[COL.date] as number) / 10000);
		if (predicate(v)) byYear.set(year, (byYear.get(year) ?? 0) + 1);
		else if (!byYear.has(year)) byYear.set(year, 0);
	}
	return [...byYear.entries()].map(([year, count]) => ({ year, count })).sort((a, b) => a.year - b.year);
}
