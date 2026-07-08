<script lang="ts">
	// Year × month heatmap over monthly.json rollups. Sequential single-hue
	// scale (never rainbow); cells show exact value on hover.
	import { interpolateBlues, interpolateYlOrRd, scaleSequential } from 'd3';
	import { chartState } from '$lib/stores/chartState';
	import { getI18n } from '$lib/i18n';
	import { monthLabel } from '$lib/utils/format';
	import type { CompactTable } from '$lib/data/load';
	import Tooltip from './primitives/Tooltip.svelte';

	let { monthly }: { monthly: CompactTable } = $props();

	const i18n = getI18n();

	// blue for rain, warm ramp for everything else
	const RAIN_METRICS = new Set(['prcp_sum', 'wet_days', 'prcp_max_day']);

	// map chartState.metric to a monthly column (fallback: days ≥ 35°C)
	const METRIC_TO_COLUMN: Record<string, string> = {
		tmax: 'tmax_mean',
		tmin: 'tmin_mean',
		prcp: 'prcp_sum',
		gmax: 'gust_max',
		pm25: 'pm25_median'
	};

	const columnName = $derived(METRIC_TO_COLUMN[$chartState.metric] ?? 'days_ge_35');
	const colIdx = $derived(monthly.columns.indexOf(columnName));
	const yearIdx = $derived(monthly.columns.indexOf('year'));
	const monthIdx = $derived(monthly.columns.indexOf('month'));

	const cells = $derived(
		monthly.rows
			.map((r) => ({
				year: r[yearIdx] as number,
				month: r[monthIdx] as number,
				value: r[colIdx] as number | null
			}))
			.filter((c) => c.value != null)
	);

	const years = $derived([...new Set(cells.map((c) => c.year))].sort((a, b) => a - b));

	const color = $derived.by(() => {
		const values = cells.map((c) => c.value!) as number[];
		const interp = RAIN_METRICS.has(columnName) ? interpolateBlues : interpolateYlOrRd;
		return scaleSequential(interp).domain([Math.min(...values), Math.max(...values)]);
	});

	const CELL = 16;
	const GAP = 2;
	const LABEL_W = 44;
	const LABEL_H = 22;

	const width = $derived(LABEL_W + 12 * (CELL + GAP));
	const height = $derived(LABEL_H + years.length * (CELL + GAP));

	let hovered = $state<{ cell: (typeof cells)[number]; px: number; py: number } | null>(null);
	let frameWidth = $state(0);
</script>

<figure class="heatmap" bind:clientWidth={frameWidth}>
	<svg {width} {height} viewBox="0 0 {width} {height}" role="img" aria-label={columnName}>
		{#each Array(12) as _, m (m)}
			<text
				x={LABEL_W + m * (CELL + GAP) + CELL / 2}
				y={LABEL_H - 8}
				text-anchor="middle"
				class="label"
			>
				{monthLabel(m, i18n.lang).slice(0, i18n.lang === 'zh' ? 2 : 1)}
			</text>
		{/each}
		{#each years as year, yi (year)}
			{#if year % 5 === 0}
				<text x={LABEL_W - 6} y={LABEL_H + yi * (CELL + GAP) + CELL / 2} dy="0.32em" text-anchor="end" class="label">
					{year}
				</text>
			{/if}
		{/each}
		{#each cells as cell (cell.year * 100 + cell.month)}
			{@const px = LABEL_W + (cell.month - 1) * (CELL + GAP)}
			{@const py = LABEL_H + years.indexOf(cell.year) * (CELL + GAP)}
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
	</svg>

	{#if hovered}
		<Tooltip px={hovered.px} py={hovered.py} {frameWidth}>
			<strong>{hovered.cell.year} · {monthLabel(hovered.cell.month - 1, i18n.lang)}</strong><br />
			{hovered.cell.value}
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
</style>
