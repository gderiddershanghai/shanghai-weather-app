<script lang="ts">
	// Yearly trend views, driven by chartState.trendMetric:
	//   stripes — Ed Hawkins-style warming stripes (annual tmean anomaly)
	//   summer/winter/prcp/gust/pm25 — one dot+line per year, 10-yr mean
	//     overlay, the five most extreme years labeled directly
	//   hotDays — bars of 35°C+ days per year
	// All values precomputed in pipeline/yearly.py; this file only draws.
	import { interpolateRdBu } from 'd3';
	import { chartState } from '$lib/stores/chartState';
	import type { TrendMetric } from '$lib/stores/chartState';
	import { getI18n } from '$lib/i18n';
	import type { YearlyTable } from '$lib/data/load';
	import Chart from './primitives/Chart.svelte';
	import AxisX from './primitives/AxisX.svelte';
	import AxisY from './primitives/AxisY.svelte';
	import LinePath from './primitives/LinePath.svelte';
	import Tooltip from './primitives/Tooltip.svelte';

	let { yearly }: { yearly: YearlyTable } = $props();

	const i18n = getI18n();

	const col = $derived(Object.fromEntries(yearly.columns.map((c, i) => [c, i])));

	interface MetricConfig {
		yCol: string;
		smCol?: string;
		unit: string;
		color: string;
		/** 'top' = label the 5 largest values, 'bottom' = 5 smallest */
		rank: 'top' | 'bottom';
		bars?: boolean;
	}
	const METRIC_CONFIG: Record<Exclude<TrendMetric, 'stripes'>, MetricConfig> = {
		summer: {
			yCol: 'summer_tmax',
			smCol: 'summer_tmax_sm',
			unit: '°C',
			color: 'var(--color-hot)',
			rank: 'top'
		},
		winter: {
			yCol: 'winter_tmin',
			smCol: 'winter_tmin_sm',
			unit: '°C',
			color: 'var(--color-cold)',
			rank: 'bottom'
		},
		hotDays: { yCol: 'days_ge_35', unit: '', color: 'var(--color-hot)', rank: 'top', bars: true },
		prcp: {
			yCol: 'prcp',
			smCol: 'prcp_sm',
			unit: ' mm',
			color: 'var(--chapter-rain)',
			rank: 'top'
		},
		gust: { yCol: 'gust_max', unit: ' km/h', color: 'var(--color-wind)', rank: 'top' },
		pm25: { yCol: 'pm25_median', unit: '', color: 'var(--chapter-aqi)', rank: 'top' }
	};

	const metric = $derived($chartState.trendMetric);
	const cfg = $derived(metric === 'stripes' ? null : METRIC_CONFIG[metric]);

	interface Pt {
		year: number;
		value: number;
		sm: number | null;
	}
	const points: Pt[] = $derived.by(() => {
		if (!cfg) return [];
		return yearly.rows
			.filter((r) => r[col[cfg.yCol]] != null)
			.map((r) => ({
				year: r[col.year] as number,
				value: r[col[cfg.yCol]] as number,
				sm: cfg.smCol ? (r[col[cfg.smCol]] as number | null) : null
			}));
	});

	const ranked = $derived.by(() => {
		const n = Math.min(5, Math.max(3, Math.floor(points.length / 4)));
		const sorted = [...points].sort((a, b) =>
			cfg?.rank === 'bottom' ? a.value - b.value : b.value - a.value
		);
		return new Map(sorted.slice(0, n).map((p, i) => [p.year, i + 1]));
	});

	const xDomain: [number, number] = $derived(
		points.length ? [points[0].year - 0.5, points[points.length - 1].year + 0.5] : [1979.5, 2026.5]
	);
	const yDomain: [number, number] = $derived.by(() => {
		if (!points.length) return [0, 1];
		const vals = points.map((p) => p.value);
		const lo = Math.min(...vals);
		const hi = Math.max(...vals);
		const pad = (hi - lo) * 0.12 || 1;
		return cfg?.bars ? [0, hi + pad] : [lo - pad, hi + pad];
	});

	const DECADES = [1980, 1990, 2000, 2010, 2020];
	const yearTicks = $derived(
		DECADES.filter((y) => y >= xDomain[0] && y <= xDomain[1]).map((y) => ({
			value: y,
			label: String(y)
		}))
	);

	// --- warming stripes ---------------------------------------------------
	interface Stripe {
		year: number;
		anom: number;
		tmean: number;
	}
	const stripes: Stripe[] = $derived(
		yearly.rows
			.filter((r) => r[col.anom] != null)
			.map((r) => ({
				year: r[col.year] as number,
				anom: r[col.anom] as number,
				tmean: r[col.tmean] as number
			}))
	);
	const anomMax = $derived(Math.max(...stripes.map((s) => Math.abs(s.anom)), 0.1));
	// RdBu reversed: negative anomaly = blue, positive = red; clamp softly so
	// one runaway year doesn't wash out the rest
	const stripeColor = (anom: number) => interpolateRdBu(0.5 - (anom / anomMax) * 0.48);

	// --- interaction ---------------------------------------------------------
	let hover = $state<{ year: number; value: number; px: number; py: number } | null>(null);
	let frameWidth = $state(0);

	const fmtVal = (v: number) =>
		cfg?.bars || metric === 'pm25' ? String(Math.round(v)) : v.toFixed(1);
	const pm25Unit = i18n.lang === 'zh' ? ' 美标AQI' : ' US AQI';
	const unitLabel = $derived(metric === 'pm25' ? pm25Unit : (cfg?.unit ?? ''));
</script>

<figure class="yearly-trend" bind:clientWidth={frameWidth}>
	{#if metric === 'stripes'}
		<Chart
			{xDomain}
			yDomain={[0, 1]}
			height={380}
			marginLeft={12}
			marginRight={12}
			ariaLabel={i18n.t('trend.caption.stripes')}
		>
			{#snippet children({ x, y })}
				{@const [y0, y1] = y.range()}
				{#each stripes as s (s.year)}
					<rect
						x={x(s.year - 0.5)}
						y={y1}
						width={x(s.year + 0.5) - x(s.year - 0.5)}
						height={y0 - y1}
						fill={stripeColor(s.anom)}
						role="presentation"
						onmouseenter={() =>
							(hover = { year: s.year, value: s.anom, px: x(s.year), py: y1 + 24 })}
						onmouseleave={() => (hover = null)}
					/>
				{/each}
				<AxisX {x} {y} ticks={yearTicks} />
				<!-- anchor labels: coolest early year vs the recent extreme -->
				{#if stripes.length}
					{@const last = stripes[stripes.length - 1]}
					<text x={x(stripes[0].year - 0.5)} y={y1 - 8} class="stripe-label">
						{stripes[0].year}: {stripes[0].anom > 0 ? '+' : ''}{stripes[0].anom.toFixed(1)}°C
					</text>
					<text x={x(last.year + 0.5)} y={y1 - 8} text-anchor="end" class="stripe-label">
						{last.year}: {last.anom > 0 ? '+' : ''}{last.anom.toFixed(1)}°C
					</text>
				{/if}
			{/snippet}
		</Chart>
	{:else if cfg}
		<Chart {xDomain} {yDomain} height={380} ariaLabel={i18n.t(`trend.caption.${metric}`)}>
			{#snippet children({ x, y })}
				<AxisY {x} {y} unit={unitLabel} />
				<AxisX {x} {y} ticks={yearTicks} baseline={cfg.bars} />

				{#if cfg.bars}
					{#each points as p (p.year)}
						<rect
							x={x(p.year - 0.42)}
							y={y(p.value)}
							width={x(p.year + 0.42) - x(p.year - 0.42)}
							height={Math.max(y(y.domain()[0]) - y(p.value), 0)}
							fill={cfg.color}
							opacity={ranked.has(p.year) ? 1 : 0.55}
							role="presentation"
							onmouseenter={() =>
								(hover = { year: p.year, value: p.value, px: x(p.year), py: y(p.value) })}
							onmouseleave={() => (hover = null)}
						/>
					{/each}
				{:else}
					<LinePath
						{x}
						{y}
						data={points.map((p) => ({ x: p.year, y: p.value }))}
						stroke="var(--color-ink-muted)"
						strokeWidth={1}
						opacity={0.45}
					/>
					{#if cfg.smCol}
						<LinePath
							{x}
							{y}
							data={points.filter((p) => p.sm != null).map((p) => ({ x: p.year, y: p.sm! }))}
							stroke={cfg.color}
							strokeWidth={2.5}
						/>
					{/if}
					{#each points as p (p.year)}
						<circle
							cx={x(p.year)}
							cy={y(p.value)}
							r={ranked.has(p.year) ? 5 : 2.6}
							class="pt"
							style:fill={ranked.has(p.year) ? cfg.color : 'var(--color-ink-muted)'}
							opacity={ranked.has(p.year) ? 1 : 0.55}
							role="presentation"
							onmouseenter={() =>
								(hover = { year: p.year, value: p.value, px: x(p.year), py: y(p.value) })}
							onmouseleave={() => (hover = null)}
						/>
					{/each}
				{/if}

				<!-- direct labels on the ranked years -->
				{#each points.filter((p) => ranked.has(p.year)) as p (p.year)}
					{@const above = cfg.rank === 'top'}
					<text
						x={x(p.year)}
						y={cfg.bars ? y(p.value) - 6 : y(p.value) + (above ? -10 : 16)}
						text-anchor="middle"
						class="rank-label"
						style:fill={cfg.color}
					>
						{p.year}{ranked.get(p.year) === 1 ? ` · ${fmtVal(p.value)}${unitLabel}` : ''}
					</text>
				{/each}

				{#if cfg.smCol}
					<g class="chart-key" transform="translate({x.range()[0] + 6}, {y.range()[1] + 4})">
						<line x1="0" x2="14" y1="4" y2="4" stroke={cfg.color} stroke-width="2.5" />
						<text x="19" y="8">{i18n.t('trend.smoothedKey')}</text>
					</g>
				{/if}
			{/snippet}
		</Chart>
	{/if}

	{#if hover}
		<Tooltip px={hover.px} py={hover.py} {frameWidth}>
			<strong>{hover.year}</strong><br />
			{#if metric === 'stripes'}
				{hover.value > 0 ? '+' : ''}{hover.value.toFixed(2)}°C
			{:else}
				{fmtVal(hover.value)}{unitLabel}
			{/if}
		</Tooltip>
	{/if}

	<figcaption>{i18n.t(`trend.caption.${metric}`)}</figcaption>
</figure>

<style>
	.yearly-trend {
		position: relative;
		margin: 0;
	}
	rect,
	.pt {
		cursor: default;
	}
	.pt {
		stroke: var(--color-paper);
		stroke-width: 1;
	}
	.rank-label {
		font-size: 0.72rem;
		font-weight: 700;
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3;
	}
	.stripe-label {
		font-size: 0.75rem;
		font-weight: 700;
		fill: var(--color-ink);
	}
	.chart-key text {
		font-size: 0.7rem;
		fill: var(--color-ink-muted);
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3;
	}
	figcaption {
		margin-top: 0.4rem;
		font-size: 0.8rem;
		color: var(--color-ink-muted);
	}
</style>
