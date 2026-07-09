<script lang="ts">
	// The hero: XKCD-style day-of-year climatology.
	//   band  = smoothed p05–p95 "normal range" (tmin_p05 .. tmax_p95)
	//   line  = smoothed p50 of daily highs
	//   dots  = p99-breaking days (hot above band, cold below), curated events ringed
	// Question the chart answers at a glance: "are extreme days piling up recently?"
	import { chartState } from '$lib/stores/chartState';
	import { tweenedDomains } from '$lib/stores/tweens';
	import { getI18n } from '$lib/i18n';
	import { formatDate, formatTemp, monthLabel } from '$lib/utils/format';
	import type { Climatology, CuratedEvent, OutliersTable } from '$lib/data/load';
	import Chart from './primitives/Chart.svelte';
	import AxisX from './primitives/AxisX.svelte';
	import AxisY from './primitives/AxisY.svelte';
	import Band from './primitives/Band.svelte';
	import LinePath from './primitives/LinePath.svelte';
	import Dots, { type Dot } from './primitives/Dots.svelte';
	import Tooltip from './primitives/Tooltip.svelte';
	import EventCard from './primitives/EventCard.svelte';

	let {
		clim,
		outliers,
		curatedEvents = []
	}: {
		clim: Climatology;
		outliers: OutliersTable;
		curatedEvents?: CuratedEvent[];
	} = $props();

	const i18n = getI18n();

	// --- series selection (real vs feels-like) --------------------------------
	const feels = $derived($chartState.tempMode === 'feels_like');
	const hi = $derived(feels ? clim.atmax_p50 : clim.tmax_p50);
	const hiP95 = $derived(feels ? clim.atmax_p95 : clim.tmax_p95);
	const hiP99 = $derived(feels ? clim.atmax_p99 : clim.tmax_p99);
	const loP05 = $derived(feels ? clim.atmin_p05 : clim.tmin_p05);

	const bandData = $derived(
		clim.doy.map((doy, i) => ({ x: doy, y0: loP05[i], y1: hiP95[i] }))
	);
	const medianData = $derived(clim.doy.map((doy, i) => ({ x: doy, y: hi[i] })));
	const p99Data = $derived(clim.doy.map((doy, i) => ({ x: doy, y: hiP99[i] })));

	// --- outlier dots ----------------------------------------------------------
	// outliers.json columns: [date, doy, series, value, severity, baseline_p50]
	// series enum: 0 real_hot, 1 real_cold, 2 feel_hot, 3 feel_cold
	const OUT = { date: 0, doy: 1, series: 2, value: 3, severity: 4 } as const;

	const curatedByDate = $derived(new Map(curatedEvents.map((e) => [e.date, e])));

	function dateIntToIso(dateInt: number): string {
		const s = String(dateInt);
		return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
	}

	const dots: Dot[] = $derived.by(() => {
		const s = $chartState;
		if (s.dotThreshold === 'none') return [];
		const wantHot = s.dotTail !== 'cold';
		const wantCold = s.dotTail !== 'hot';
		const hotSeries = feels ? 2 : 0;
		const coldSeries = feels ? 3 : 1;
		const result: Dot[] = [];
		for (const row of outliers.rows) {
			const series = row[OUT.series] as number;
			const isHot = series === hotSeries && wantHot;
			const isCold = series === coldSeries && wantCold;
			if (!isHot && !isCold) continue;
			const doy = row[OUT.doy] as number;
			if (doy < s.xDomain[0] || doy > s.xDomain[1]) continue;
			const iso = dateIntToIso(row[OUT.date] as number);
			result.push({
				id: `${series}-${row[OUT.date]}`,
				x: doy,
				y: row[OUT.value] as number,
				kind: isHot ? 'hot' : 'cold',
				featured: curatedByDate.has(iso)
			});
		}
		return result;
	});

	// --- domains ---------------------------------------------------------------
	const yDomain: [number, number] = $derived.by(() => {
		if ($tweenedDomains.yDomain) return $tweenedDomains.yDomain;
		// auto: fit band + dots with padding
		const values = [
			...loP05.filter((v): v is number => v != null),
			...hiP99.filter((v): v is number => v != null),
			...dots.map((d) => d.y)
		];
		return [Math.floor(Math.min(...values)) - 3, Math.ceil(Math.max(...values)) + 3];
	});

	// month tick at the first day of each month (non-leap DOY starts)
	const MONTH_STARTS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];
	const monthTicks = $derived(
		MONTH_STARTS.map((doy, m) => ({ value: doy + 14, label: monthLabel(m, i18n.lang) })).filter(
			(t) => t.value >= $tweenedDomains.xDomain[0] && t.value <= $tweenedDomains.xDomain[1]
		)
	);

	// --- interaction -----------------------------------------------------------
	let hovered = $state<{ dot: Dot; px: number; py: number } | null>(null);
	let frameWidth = $state(0);

	const focusedEvent = $derived(
		$chartState.focusedEventId
			? (curatedEvents.find((e) => e.id === $chartState.focusedEventId) ?? null)
			: null
	);
	let focusedPos = $state<{ px: number; py: number } | null>(null);

	function handleSelect(dot: Dot, px: number, py: number) {
		const iso = dateIntToIso(Number(dot.id.split('-')[1]));
		const event = curatedByDate.get(iso);
		if (event) {
			focusedPos = { px, py };
			chartState.update((s) => ({ ...s, focusedEventId: event.id }));
		}
	}

	function closeCard() {
		chartState.update((s) => ({ ...s, focusedEventId: null }));
		focusedPos = null;
	}

	const hoveredIso = $derived(
		hovered ? dateIntToIso(Number(hovered.dot.id.split('-')[1])) : null
	);
</script>

<figure class="climatology" bind:clientWidth={frameWidth}>
	<Chart
		xDomain={$tweenedDomains.xDomain}
		{yDomain}
		height={460}
		ariaLabel={i18n.t('site.tagline')}
	>
		{#snippet children({ x, y })}
			<AxisY {x} {y} unit="°C" />
			<AxisX {x} {y} ticks={monthTicks} />

			{#if $chartState.showBand}
				<Band {x} {y} data={bandData} />
			{/if}

			<!-- on-chart key: readers must not need the prose to decode the marks -->
			<g class="chart-key" aria-hidden="true" transform="translate({x.range()[0] + 6}, {y.range()[1] + 4})">
				{#if $chartState.showBand}
					<rect x="0" y="0" width="14" height="9" rx="2" class="key-band" />
					<text x="19" y="8">{i18n.t('chart.key.band')}</text>
				{/if}
				{#if $chartState.showMedian}
					<line x1="0" x2="14" y1="20" y2="20" class="key-median" />
					<text x="19" y="23">{i18n.t('chart.key.median')}</text>
				{/if}
				{#if dots.length > 0}
					<circle cx="4" cy="34" r="3.5" class="key-dot hot" />
					<circle cx="11" cy="34" r="3.5" class="key-dot cold" />
					<text x="19" y="38">{i18n.t('chart.key.dots')}</text>
				{/if}
			</g>
			{#if $chartState.showP99}
				<LinePath {x} {y} data={p99Data} stroke="var(--color-hot)" strokeWidth={1} dashed opacity={0.7} />
			{/if}
			{#if $chartState.showMedian}
				<LinePath {x} {y} data={medianData} />
			{/if}

			<Dots
				{x}
				{y}
				{dots}
				onfocus={(dot, px, py) => (hovered = { dot, px, py })}
				onblur={() => (hovered = null)}
				onselect={handleSelect}
			/>
		{/snippet}
	</Chart>

	{#if hovered && !focusedEvent}
		<Tooltip px={hovered.px} py={hovered.py} {frameWidth}>
			<strong>{hoveredIso ? formatDate(hoveredIso, i18n.lang) : ''}</strong><br />
			{formatTemp(hovered.dot.y)}
			{#if hovered.dot.featured}
				<br /><em>{i18n.lang === 'zh' ? '点击查看故事' : 'click for the story'}</em>
			{/if}
		</Tooltip>
	{/if}

	{#if focusedEvent}
		{#if focusedPos}
			<div class="card-anchor" style:left="{focusedPos.px}px" style:top="{focusedPos.py}px">
				<EventCard event={focusedEvent} onclose={closeCard} />
			</div>
		{:else}
			<!-- story-driven focus (no click position): pin top-right -->
			<div class="card-fixed">
				<EventCard event={focusedEvent} onclose={closeCard} />
			</div>
		{/if}
	{/if}
</figure>

<style>
	.climatology {
		position: relative;
		margin: 0;
	}
	.card-anchor {
		position: absolute;
	}
	.card-fixed {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
	}
	.card-fixed :global(.event-card) {
		position: static;
	}
	.chart-key text {
		font-size: 0.7rem;
		fill: var(--color-ink-muted);
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3;
	}
	.chart-key .key-band {
		fill: var(--color-band);
		stroke: var(--color-median);
		stroke-width: 0.5;
	}
	.chart-key .key-median {
		stroke: var(--color-median);
		stroke-width: 2;
		stroke-linecap: round;
	}
	.chart-key .key-dot.hot {
		fill: var(--color-hot);
	}
	.chart-key .key-dot.cold {
		fill: var(--color-cold);
	}
	.card-anchor :global(.event-card) {
		transform: translate(12px, -50%);
	}
	@media (max-width: 640px) {
		.card-anchor :global(.event-card) {
			transform: none;
		}
	}
</style>
