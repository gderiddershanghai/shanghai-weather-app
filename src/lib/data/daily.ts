// Column-index accessors for the compact daily table (daily.json).
// MUST match pipeline/config.py DAILY_COMPACT_COLUMNS — asserted at load time.

import type { CompactTable } from './load';

export const COL = {
	date: 0, // yyyymmdd int
	tmax: 1,
	tmin: 2,
	tmean: 3,
	prcp: 4,
	prcp_h: 5,
	atmax: 6,
	atmin: 7,
	sun_h: 8,
	wmax: 9,
	gmax: 10,
	wmean: 11
} as const;

export type DailyMetric = keyof typeof COL;

const EXPECTED = Object.keys(COL);

/** Throws if the pipeline's column order drifted from this enum. */
export function assertDailyColumns(table: CompactTable): void {
	const got = table.columns.join(',');
	const want = EXPECTED.join(',');
	if (got !== want) {
		throw new Error(`daily.json column drift: expected [${want}] got [${got}]`);
	}
}

/** yyyymmdd int -> { year, month (1-12), day } without Date object overhead. */
export function splitDateInt(dateInt: number) {
	const year = Math.floor(dateInt / 10000);
	const month = Math.floor((dateInt % 10000) / 100);
	const day = dateInt % 100;
	return { year, month, day };
}

/** yyyymmdd int -> local Date (for d3 time scales). */
export function dateIntToDate(dateInt: number): Date {
	const { year, month, day } = splitDateInt(dateInt);
	return new Date(year, month - 1, day);
}
