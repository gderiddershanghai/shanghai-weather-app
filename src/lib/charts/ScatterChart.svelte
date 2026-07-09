<script lang="ts">
	// Temp × AQI interplay scatter (~4.5k points, SVG is fine at r=2).
	// Color = season (Okabe–Ito, colorblind-safe); binned-median line carries
	// the story signal, points are context.
	import { chartState } from '$lib/stores/chartState';
	import { getI18n } from '$lib/i18n';
	import type { CompactTable } from '$lib/data/load';
	import Chart from './primitives/Chart.svelte';
	import AxisX from './primitives/AxisX.svelte';
	import AxisY from './primitives/AxisY.svelte';
	import LinePath from './primitives/LinePath.svelte';

	interface TempAqiTable extends CompactTable {
		binned: {
			season: number;
			tmax_bin: number;
			n: number;
			pm25_median: number;
			o3_median: number | null;
		}[];
	}

	let { tempAqi }: { tempAqi: TempAqiTable } = $props();

	const i18n = getI18n();

	// Okabe–Ito, one hue per season: DJF blue, MAM green, JJA vermillion, SON amber
	const SEASON_COLORS = ['#0072B2', '#009E73', '#D55E00', '#E69F00'];
	// darkened variants for TEXT so labels meet contrast on the paper bg
	const SEASON_TEXT = ['#005a8c', '#00694f', '#a34500', '#8a5f00'];
	const SEASON_KEYS = ['seasons.djf', 'seasons.mam', 'seasons.jja', 'seasons.son'];

	const IDX = $derived({
		tmax: tempAqi.columns.indexOf('tmax'),
		pm25: tempAqi.columns.indexOf('pm25'),
		o3: tempAqi.columns.indexOf('o3'),
		season: tempAqi.columns.indexOf('season')
	});

	const yCol = $derived($chartState.scatterY);

	const points = $derived(
		tempAqi.rows
			.map((r) => ({
				x: r[IDX.tmax] as number,
				y: r[yCol === 'pm25' ? IDX.pm25 : IDX.o3] as number | null,
				season: r[IDX.season] as number
			}))
			.filter(
				(p) =>
					p.y != null &&
					($chartState.seasonFilter == null || p.season === $chartState.seasonFilter)
			)
	);

	const medianLines = $derived.by(() => {
		const filter = $chartState.seasonFilter;
		const seasons = filter == null ? [0, 1, 2, 3] : [filter];
		return seasons.map((s) => ({
			season: s,
			data: tempAqi.binned
				.filter((b) => b.season === s)
				.map((b) => ({
					x: b.tmax_bin + 1,
					y: yCol === 'pm25' ? b.pm25_median : b.o3_median
				}))
		}));
	});

	const xDomain: [number, number] = $derived.by(() => {
		const xs = points.map((p) => p.x);
		return xs.length ? [Math.floor(Math.min(...xs)) - 1, Math.ceil(Math.max(...xs)) + 1] : [0, 40];
	});
	const yDomain: [number, number] = $derived.by(() => {
		const ys = points.map((p) => p.y!) as number[];
		return ys.length ? [0, Math.ceil(Math.max(...ys) / 25) * 25] : [0, 300];
	});

	const tempTicks = $derived.by(() => {
		const ticks = [];
		for (let t = Math.ceil(xDomain[0] / 10) * 10; t <= xDomain[1]; t += 10) {
			ticks.push({ value: t, label: `${t}°C` });
		}
		return ticks;
	});
</script>

<figure class="scatter">
	<Chart {xDomain} {yDomain} height={440} ariaLabel={i18n.t('site.tagline')}>
		{#snippet children({ x, y })}
			<AxisY {x} {y} unit=" AQI" />
			<AxisX {x} {y} ticks={tempTicks} baseline />

			<g class="points" style="shape-rendering: optimizeSpeed">
				{#each points as p, i (i)}
					<circle cx={x(p.x)} cy={y(p.y!)} r="2" fill={SEASON_COLORS[p.season]} opacity="0.35" />
				{/each}
			</g>

			{#each medianLines as { season, data } (season)}
				<LinePath {x} {y} {data} stroke={SEASON_COLORS[season]} strokeWidth={2.5} />
			{/each}

			<!-- direct season labels at line ends (no legend) -->
			{#each medianLines as { season, data } (season)}
				{@const last = data.filter((d) => d.y != null).at(-1)}
				{#if last}
					<text
						x={x(last.x) + 6}
						y={y(last.y!)}
						dy="0.32em"
						fill={SEASON_TEXT[season]}
						class="season-label"
					>
						{i18n.t(SEASON_KEYS[season])}
					</text>
				{/if}
			{/each}
		{/snippet}
	</Chart>
</figure>

<style>
	.scatter {
		position: relative;
		margin: 0;
	}
	.season-label {
		font-size: 0.75rem;
		font-weight: 700;
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3;
	}
</style>
