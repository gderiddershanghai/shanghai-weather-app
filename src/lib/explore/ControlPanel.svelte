<script lang="ts">
	// Explore controls — every widget writes the SAME chartState store the
	// story drives. Controls render conditionally on chartType.
	import {
		applyPreset,
		chartState,
		EXPLORE_DEFAULTS,
		resetChart,
		type ChartType,
		type DotTail,
		type DotThreshold,
		type Season,
		type TempMode,
		type TrendMetric
	} from '$lib/stores/chartState';
	import { getI18n } from '$lib/i18n';

	const i18n = getI18n();

	const CHART_TYPES: ChartType[] = ['climatology', 'yearly', 'timeseries', 'heatmap', 'scatter'];
	const TREND_METRICS: TrendMetric[] = [
		'stripes',
		'summer',
		'winter',
		'hotDays',
		'prcp',
		'gust',
		'pm25'
	];
	const TEMP_MODES: TempMode[] = ['real', 'feels_like'];
	const THRESHOLDS: DotThreshold[] = ['p99', 'p95', 'none'];
	const TAILS: DotTail[] = ['hot', 'cold', 'both'];
	const WINDOWS = [1, 30, 365] as const;
	const METRICS = ['tmax', 'tmin', 'prcp', 'gmax', 'pm25'] as const;
	const SEASON_KEYS = ['seasons.djf', 'seasons.mam', 'seasons.jja', 'seasons.son'];

	const FULL_YEAR: [number, number] = [1, 365];
	const ALL_YEARS: [number, number] = [1980, 2026];

	function setChartType(chartType: ChartType) {
		// each view needs its own x-domain semantics
		applyPreset({
			chartType,
			xDomain: chartType === 'climatology' ? FULL_YEAR : ALL_YEARS,
			focusedEventId: null
		});
	}
</script>

<div class="controls" role="group" aria-label={i18n.t('explore.title')}>
	<fieldset>
		<legend>{i18n.t('explore.chartType')}</legend>
		{#each CHART_TYPES as type (type)}
			<button class:on={$chartState.chartType === type} onclick={() => setChartType(type)}>
				{i18n.t(`explore.chartType.${type}`)}
			</button>
		{/each}
	</fieldset>

	{#if $chartState.chartType === 'climatology'}
		<fieldset>
			<legend>{i18n.t('explore.tempMode')}</legend>
			{#each TEMP_MODES as mode (mode)}
				<button
					class:on={$chartState.tempMode === mode}
					onclick={() => applyPreset({ tempMode: mode })}
				>
					{i18n.t(`explore.tempMode.${mode}`)}
				</button>
			{/each}
		</fieldset>
		<fieldset>
			<legend>{i18n.t('explore.dots')}</legend>
			{#each THRESHOLDS as t (t)}
				<button
					class:on={$chartState.dotThreshold === t}
					onclick={() => applyPreset({ dotThreshold: t })}
				>
					{i18n.t(`explore.dots.${t}`)}
				</button>
			{/each}
		</fieldset>
		<fieldset>
			<legend>{i18n.t('explore.tail')}</legend>
			{#each TAILS as tail (tail)}
				<button
					class:on={$chartState.dotTail === tail}
					onclick={() => applyPreset({ dotTail: tail })}
				>
					{i18n.t(`explore.tail.${tail}`)}
				</button>
			{/each}
		</fieldset>
	{/if}

	{#if $chartState.chartType === 'yearly'}
		<fieldset>
			<legend>{i18n.t('explore.metric')}</legend>
			{#each TREND_METRICS as m (m)}
				<button
					class:on={$chartState.trendMetric === m}
					onclick={() => applyPreset({ trendMetric: m })}
				>
					{i18n.t(`trend.${m}`)}
				</button>
			{/each}
		</fieldset>
	{/if}

	{#if $chartState.chartType === 'timeseries' || $chartState.chartType === 'heatmap'}
		<fieldset>
			<legend>{i18n.t('explore.metric')}</legend>
			{#each METRICS as m (m)}
				<button class:on={$chartState.metric === m} onclick={() => applyPreset({ metric: m })}>
					{i18n.t(`explore.metric.${m}`)}
				</button>
			{/each}
		</fieldset>
	{/if}

	{#if $chartState.chartType === 'timeseries'}
		<fieldset>
			<legend>{i18n.t('explore.smoothing')}</legend>
			{#each WINDOWS as w (w)}
				<button
					class:on={$chartState.rollingWindow === w}
					onclick={() => applyPreset({ rollingWindow: w })}
				>
					{i18n.t(`explore.smoothing.${w}`)}
				</button>
			{/each}
		</fieldset>
	{/if}

	{#if $chartState.chartType === 'scatter'}
		<fieldset>
			<legend>{i18n.t('explore.tail')}</legend>
			<button
				class:on={$chartState.seasonFilter == null}
				onclick={() => applyPreset({ seasonFilter: null })}
			>
				{i18n.t('seasons.all')}
			</button>
			{#each SEASON_KEYS as key, s (key)}
				<button
					class:on={$chartState.seasonFilter === s}
					onclick={() => applyPreset({ seasonFilter: s as Season })}
				>
					{i18n.t(key)}
				</button>
			{/each}
		</fieldset>
	{/if}

	<button class="reset" onclick={() => resetChart(EXPLORE_DEFAULTS)}>
		{i18n.t('explore.reset')}
	</button>
</div>

<style>
	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem 1.25rem;
		align-items: flex-end;
		padding: 0.75rem 0;
	}
	fieldset {
		border: none;
		margin: 0;
		padding: 0;
		display: flex;
		gap: 0.25rem;
	}
	legend {
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-ink-muted);
		padding: 0 0 0.25rem;
	}
	button {
		font: inherit;
		font-size: 0.85rem;
		padding: 0.3rem 0.7rem;
		border: 1px solid var(--color-border);
		border-radius: 999px;
		background: var(--color-paper);
		cursor: pointer;
	}
	button.on {
		background: var(--color-ink);
		color: var(--color-paper);
		border-color: var(--color-ink);
	}
	.reset {
		margin-left: auto;
		border-style: dashed;
	}
</style>
