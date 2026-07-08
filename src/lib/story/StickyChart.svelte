<script lang="ts">
	// Resolves chartState.chartType to the right chart component.
	import { chartState } from '$lib/stores/chartState';
	import ClimatologyChart from '$lib/charts/ClimatologyChart.svelte';
	import TimeSeriesChart from '$lib/charts/TimeSeriesChart.svelte';
	import MonthlyHeatmap from '$lib/charts/MonthlyHeatmap.svelte';
	import ScatterChart from '$lib/charts/ScatterChart.svelte';
	import type {
		Climatology,
		CompactTable,
		CuratedEvent,
		Meta,
		OutliersTable
	} from '$lib/data/load';
	import { getI18n } from '$lib/i18n';
	import { formatDate } from '$lib/utils/format';

	let {
		clim,
		outliers,
		curatedEvents,
		meta,
		daily = null,
		monthly = null,
		tempAqi = null
	}: {
		clim: Climatology | null;
		outliers: OutliersTable | null;
		curatedEvents: CuratedEvent[];
		meta: Meta | null;
		daily?: CompactTable | null;
		monthly?: CompactTable | null;
		tempAqi?: (CompactTable & { binned: any[] }) | null;
	} = $props();

	const i18n = getI18n();
</script>

<div class="sticky-chart">
	{#if $chartState.chartType === 'climatology' && clim && outliers}
		<ClimatologyChart {clim} {outliers} {curatedEvents} />
	{:else if $chartState.chartType === 'timeseries' && daily}
		<TimeSeriesChart {daily} />
	{:else if $chartState.chartType === 'heatmap' && monthly}
		<MonthlyHeatmap {monthly} />
	{:else if $chartState.chartType === 'scatter' && tempAqi}
		<ScatterChart {tempAqi} />
	{/if}

	{#if meta}
		<p class="provenance">
			{i18n.t('footer.dataThrough')}
			{formatDate(meta.weather.end, i18n.lang)} · Open-Meteo (ERA5) · n={meta.weather.rows.toLocaleString()}
		</p>
	{/if}
</div>

<style>
	.sticky-chart {
		width: 100%;
		max-width: 1100px;
		margin: 0 auto;
		padding: 0 1rem;
	}
	.provenance {
		margin: 0.25rem 0 0;
		font-size: 0.72rem;
		color: var(--color-ink-muted);
		text-align: right;
	}
</style>
