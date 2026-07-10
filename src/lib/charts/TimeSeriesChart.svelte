<script lang="ts">
	// Long-run time series: faint daily values + bold rolling mean.
	// x = decimal years; reads metric/rollingWindow/xDomain from chartState.
	import { chartState } from '$lib/stores/chartState';
	import { tweenedDomains } from '$lib/stores/tweens';
	import { getI18n } from '$lib/i18n';
	import { COL } from '$lib/data/daily';
	import { metricSeries, rollingMean } from '$lib/data/transforms';
	import type { CompactTable } from '$lib/data/load';
	import Chart from './primitives/Chart.svelte';
	import AxisX from './primitives/AxisX.svelte';
	import AxisY from './primitives/AxisY.svelte';
	import LinePath from './primitives/LinePath.svelte';

	let { daily }: { daily: CompactTable } = $props();

	const i18n = getI18n();

	const METRIC_UNITS: Record<string, string> = {
		tmax: '°C',
		tmin: '°C',
		tmean: '°C',
		atmax: '°C',
		atmin: '°C',
		prcp: 'mm',
		sun_h: 'h',
		wmax: 'km/h',
		gmax: 'km/h',
		wmean: 'km/h'
	};

	const colIndex = $derived(
		$chartState.metric in COL ? COL[$chartState.metric as keyof typeof COL] : COL.tmax
	);
	const yearRange = $derived($tweenedDomains.xDomain);

	const raw = $derived(
		metricSeries(daily, colIndex, [Math.floor(yearRange[0]), Math.ceil(yearRange[1])])
	);
	const smoothed = $derived(rollingMean(raw, $chartState.rollingWindow));

	const yDomain: [number, number] = $derived.by(() => {
		if ($tweenedDomains.yDomain) return $tweenedDomains.yDomain;
		const ys = raw.map((p) => p.y).filter((v): v is number => v != null);
		if (!ys.length) return [0, 1];
		return [Math.floor(Math.min(...ys, 0)), Math.ceil(Math.max(...ys)) + 2];
	});

	const yearTicks = $derived.by(() => {
		const [y0, y1] = yearRange;
		const span = y1 - y0;
		const stepSize = span > 30 ? 10 : span > 12 ? 5 : 1;
		const ticks = [];
		for (let y = Math.ceil(y0 / stepSize) * stepSize; y <= y1; y += stepSize) {
			ticks.push({ value: y, label: String(y) });
		}
		return ticks;
	});
</script>

<figure class="timeseries">
	<Chart xDomain={yearRange} {yDomain} height={440} ariaLabel={i18n.t('site.tagline')}>
		{#snippet children({ x, y })}
			<AxisY {x} {y} unit={METRIC_UNITS[$chartState.metric] ?? ''} />
			<AxisX {x} {y} ticks={yearTicks} baseline />

			{#if $chartState.rollingWindow > 1}
				<LinePath
					{x}
					{y}
					data={raw}
					stroke="var(--color-ink-muted)"
					strokeWidth={0.5}
					opacity={0.35}
				/>
				<LinePath {x} {y} data={smoothed} stroke="var(--color-hot)" strokeWidth={2.5} />
			{:else}
				<LinePath {x} {y} data={raw} stroke="var(--color-ink)" strokeWidth={0.8} opacity={0.8} />
			{/if}
		{/snippet}
	</Chart>
</figure>

<style>
	.timeseries {
		position: relative;
		margin: 0;
	}
</style>
