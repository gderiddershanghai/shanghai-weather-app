<script lang="ts">
	// Year × month heatmap over monthly.json rollups. Sequential single-hue
	// scales (per-metric: red family reserved for heat, blue for rain, purple
	// for haze). Cells with sparse coverage are hidden — a lone partial month
	// must not masquerade as a trend. Gradient legend + units included.
	import { interpolateBlues, interpolatePurples, interpolateYlOrRd, scaleSequential } from 'd3';
	import { chartState } from '$lib/stores/chartState';
	import { getI18n } from '$lib/i18n';
	import { monthLabel } from '$lib/utils/format';
	import type { CompactTable } from '$lib/data/load';
	import Tooltip from './primitives/Tooltip.svelte';

	let { monthly }: { monthly: CompactTable } = $props();

	const i18n = getI18n();

	// metric -> monthly column, unit, color ramp
	const METRIC_CONFIG: Record<
		string,
		{ column: string; unit: string; ramp: (t: number) => string }
	> = {
		tmax: { column: 'tmax_mean', unit: '°C', ramp: interpolateYlOrRd },
		tmin: { column: 'tmin_mean', unit: '°C', ramp: interpolateYlOrRd },
		prcp: { column: 'prcp_sum', unit: 'mm', ramp: interpolateBlues },
		gmax: { column: 'gust_max', unit: 'km/h', ramp: interpolateBlues },
		pm25: { column: 'pm25_median', unit: ' US AQI', ramp: interpolatePurples }
	};

	const config = $derived(METRIC_CONFIG[$chartState.metric] ?? METRIC_CONFIG.tmax);
	const colIdx = $derived(monthly.columns.indexOf(config.column));
	const yearIdx = $derived(monthly.columns.indexOf('year'));
	const monthIdx = $derived(monthly.columns.indexOf('month'));
	const daysIdx = $derived(monthly.columns.indexOf('days'));
	const pm25DaysIdx = $derived(monthly.columns.indexOf('pm25_days'));

	// Coverage guard: hide cells built from < 20 days of data (partial months).
	const MIN_DAYS = 20;

	const cells = $derived(
		monthly.rows
			.map((r) => ({
				year: r[yearIdx] as number,
				month: r[monthIdx] as number,
				value: r[colIdx] as number | null,
				coverage:
					($chartState.metric === 'pm25'
						? (r[pm25DaysIdx] as number | null)
						: (r[daysIdx] as number | null)) ?? 0
			}))
			.filter((c) => c.value != null && c.coverage >= MIN_DAYS)
	);

	const years = $derived([...new Set(cells.map((c) => c.year))].sort((a, b) => a - b));

	const domain: [number, number] = $derived.by(() => {
		const values = cells.map((c) => c.value!) as number[];
		return [Math.min(...values), Math.max(...values)];
	});
	const color = $derived(scaleSequential(config.ramp).domain(domain));

	// Transposed: years run left->right (time reads like text), 12 month rows
	// always fit vertically — the chart can never overflow the deck.
	const CELL = 16;
	const GAP = 2;
	const LABEL_W = 48;
	const LABEL_H = 22;
	const LEGEND_H = 40;

	const width = $derived(LABEL_W + years.length * (CELL + GAP));
	const height = $derived(LABEL_H + 12 * (CELL + GAP) + LEGEND_H);

	const legendStops = [0, 0.25, 0.5, 0.75, 1];
	const legendY = $derived(LABEL_H + 12 * (CELL + GAP) + 14);

	let hovered = $state<{ cell: (typeof cells)[number]; px: number; py: number } | null>(null);
	let frameWidth = $state(0);
</script>

<figure class="heatmap" bind:clientWidth={frameWidth}>
	<svg {width} {height} viewBox="0 0 {width} {height}" role="img" aria-label={config.column}>
		{#each years as year, yi (year)}
			{#if year % 5 === 0}
				<text
					x={LABEL_W + yi * (CELL + GAP) + CELL / 2}
					y={LABEL_H - 8}
					text-anchor="middle"
					class="label"
					class:decade={year % 10 === 0}
				>
					{year}
				</text>
			{/if}
		{/each}
		{#each Array(12) as _, m (m)}
			<text
				x={LABEL_W - 6}
				y={LABEL_H + m * (CELL + GAP) + CELL / 2}
				dy="0.32em"
				text-anchor="end"
				class="label"
			>
				{monthLabel(m, i18n.lang)}
			</text>
		{/each}
		{#each cells as cell (cell.year * 100 + cell.month)}
			{@const px = LABEL_W + years.indexOf(cell.year) * (CELL + GAP)}
			{@const py = LABEL_H + (cell.month - 1) * (CELL + GAP)}
			<rect
				x={px}
				y={py}
				width={CELL}
				height={CELL}
				rx="2"
				fill={color(cell.value!)}
				onmouseenter={() => (hovered = { cell, px: px + CELL / 2, py })}
				onmouseleave={() => (hovered = null)}
				role="presentation"
			/>
		{/each}

		<!-- gradient legend: 5 stops, min/max labeled with unit -->
		<g class="legend" aria-hidden="true">
			{#each legendStops as stop, i (stop)}
				<rect
					x={LABEL_W + i * 26}
					y={legendY}
					width="26"
					height="10"
					fill={color(domain[0] + stop * (domain[1] - domain[0]))}
				/>
			{/each}
			<text x={LABEL_W - 4} y={legendY + 9} text-anchor="end" class="label">
				{Math.round(domain[0])}
			</text>
			<text x={LABEL_W + 5 * 26 + 4} y={legendY + 9} class="label">
				{Math.round(domain[1])}{config.unit}
			</text>
		</g>
	</svg>

	{#if hovered}
		<Tooltip px={hovered.px} py={hovered.py} {frameWidth}>
			<strong>{hovered.cell.year} · {monthLabel(hovered.cell.month - 1, i18n.lang)}</strong><br />
			{hovered.cell.value}{config.unit}
		</Tooltip>
	{/if}
</figure>

<style>
	.heatmap {
		position: relative;
		margin: 0;
		overflow-x: auto;
	}
	.label {
		font-size: 0.65rem;
		fill: var(--color-ink-muted);
	}
	.label.decade {
		font-weight: 700;
		fill: var(--color-ink);
	}
</style>
