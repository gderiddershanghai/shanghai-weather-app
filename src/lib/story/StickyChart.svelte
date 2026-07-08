<script lang="ts">
	// Resolves chartState.chartType to the right chart component.
	// (timeseries / heatmap / scatter arrive with chapters 4–6.)
	import { chartState } from '$lib/stores/chartState';
	import ClimatologyChart from '$lib/charts/ClimatologyChart.svelte';
	import type { Climatology, CuratedEvent, Meta, OutliersTable } from '$lib/data/load';
	import { getI18n } from '$lib/i18n';
	import { formatDate } from '$lib/utils/format';

	let {
		clim,
		outliers,
		curatedEvents,
		meta
	}: {
		clim: Climatology | null;
		outliers: OutliersTable | null;
		curatedEvents: CuratedEvent[];
		meta: Meta | null;
	} = $props();

	const i18n = getI18n();
</script>

<div class="sticky-chart">
	{#if $chartState.chartType === 'climatology' && clim && outliers}
		<ClimatologyChart {clim} {outliers} {curatedEvents} />
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
