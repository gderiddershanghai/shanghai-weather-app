<script lang="ts">
	// Explore mode: same charts, same store — user-driven instead of scroll-driven.
	import { onMount } from 'svelte';
	import { getI18n } from '$lib/i18n';
	import { chartState, resetChart, EXPLORE_DEFAULTS } from '$lib/stores/chartState';
	import ControlPanel from '$lib/explore/ControlPanel.svelte';
	import ClimatologyChart from '$lib/charts/ClimatologyChart.svelte';
	import TimeSeriesChart from '$lib/charts/TimeSeriesChart.svelte';
	import MonthlyHeatmap from '$lib/charts/MonthlyHeatmap.svelte';
	import ScatterChart from '$lib/charts/ScatterChart.svelte';
	import {
		loadClimatology,
		loadCuratedEvents,
		loadDaily,
		loadMeta,
		loadOutliers,
		type Climatology,
		type CompactTable,
		type CuratedEvent,
		type Meta,
		type OutliersTable
	} from '$lib/data/load';
	import { assertDailyColumns } from '$lib/data/daily';
	import { base } from '$app/paths';
	import { formatDate } from '$lib/utils/format';

	const i18n = getI18n();

	let clim = $state<Climatology | null>(null);
	let outliers = $state<OutliersTable | null>(null);
	let curatedEvents = $state<CuratedEvent[]>([]);
	let daily = $state<CompactTable | null>(null);
	let monthly = $state<CompactTable | null>(null);
	let tempAqi = $state<(CompactTable & { binned: never[] }) | null>(null);
	let meta = $state<Meta | null>(null);
	let loadError = $state<string | null>(null);

	onMount(async () => {
		resetChart(EXPLORE_DEFAULTS);
		try {
			[clim, outliers, curatedEvents, meta, daily] = await Promise.all([
				loadClimatology(),
				loadOutliers(),
				loadCuratedEvents(),
				loadMeta(),
				loadDaily()
			]);
			assertDailyColumns(daily!);
			// heavier extras load after first paint
			const [m, ta] = await Promise.all([
				fetch(`${base}/data/derived/monthly.json`).then((r) => r.json()),
				fetch(`${base}/data/derived/temp-aqi.json`).then((r) => r.json())
			]);
			monthly = m;
			tempAqi = ta;
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
		}
	});
</script>

<section class="explore">
	<h1>{i18n.t('explore.title')}</h1>

	{#if loadError}
		<p class="error">data failed to load: {loadError}</p>
	{:else}
		<ControlPanel />

		<div class="chart-area">
			{#if $chartState.chartType === 'climatology' && clim && outliers}
				<ClimatologyChart {clim} {outliers} {curatedEvents} />
			{:else if $chartState.chartType === 'timeseries' && daily}
				<TimeSeriesChart {daily} />
			{:else if $chartState.chartType === 'heatmap' && monthly}
				<MonthlyHeatmap {monthly} />
			{:else if $chartState.chartType === 'scatter' && tempAqi}
				<ScatterChart {tempAqi} />
			{:else}
				<p class="loading">…</p>
			{/if}
		</div>

		{#if meta}
			<p class="provenance">
				{i18n.t('footer.dataThrough')}
				{formatDate(meta.weather.end, i18n.lang)}
			</p>
		{/if}
	{/if}
</section>

<style>
	.explore {
		max-width: 1100px;
		margin: 0 auto;
		padding: 1rem;
	}
	.chart-area {
		min-height: 460px;
	}
	.loading {
		text-align: center;
		color: var(--color-ink-muted);
		padding: 4rem 0;
	}
	.provenance {
		font-size: 0.72rem;
		color: var(--color-ink-muted);
		text-align: right;
	}
	.error {
		color: var(--color-hot);
	}
</style>
