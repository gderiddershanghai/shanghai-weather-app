<script lang="ts">
	// "Same air, different color": the US EPA and China GB 3095 AQI category
	// breakpoints on one shared PM2.5 concentration axis, with a marker showing
	// a typical bad 2014 winter day landing in different categories.
	// Static/pedagogical — no chartState dependency beyond being mounted.
	import { scaleLinear } from 'd3';
	import { getI18n } from '$lib/i18n';

	const i18n = getI18n();

	// Standard AQI category colors (toned for the paper background) — the SAME
	// colors in both rows; only the breakpoints differ. That's the whole point.
	const CATEGORY_COLORS = ['#6fbf73', '#e6c84a', '#e8853d', '#d64545', '#8f3f97', '#7e0023'];

	// PM2.5 24h breakpoints (µg/m³). US: pre-2024 EPA values — these are what
	// aqicn's historical index conversions used. CN: GB 3095 / HJ 633.
	const US_BREAKS = [0, 12, 35.5, 55.5, 150.5, 250.5];
	const CN_BREAKS = [0, 35, 75, 115, 150, 250];

	const US_LABELS = {
		en: ['Good', 'Moderate', 'Unhealthy (sensitive)', 'Unhealthy', 'Very unhealthy', 'Hazardous'],
		zh: ['好', '中等', '对敏感人群不健康', '不健康', '非常不健康', '危险']
	};
	const CN_LABELS = {
		en: ['Excellent', 'Good', 'Light', 'Moderate', 'Heavy', 'Severe'],
		zh: ['优', '良', '轻度污染', '中度污染', '重度污染', '严重污染']
	};

	const MARKER = 42; // µg/m³ — ≈ the 2014 median winter day (US AQI ~116)
	const MAX = 260;

	let width = $state(0);
	const HEIGHT = 240;
	const M = { top: 56, right: 16, bottom: 36, left: 96 };
	const ROW_H = 44;
	const ROW_GAP = 18;

	const x = $derived(
		scaleLinear()
			.domain([0, MAX])
			.range([M.left, Math.max(width - M.right, M.left + 1)])
	);

	function bands(breaks: number[]) {
		return breaks.map((b, i) => ({
			x0: b,
			x1: i < breaks.length - 1 ? breaks[i + 1] : MAX,
			color: CATEGORY_COLORS[i],
			idx: i
		}));
	}

	const rows = $derived([
		{ label: i18n.t('aqiScale.us'), bands: bands(US_BREAKS), labels: US_LABELS[i18n.lang], y: M.top },
		{
			label: i18n.t('aqiScale.cn'),
			bands: bands(CN_BREAKS),
			labels: CN_LABELS[i18n.lang],
			y: M.top + ROW_H + ROW_GAP
		}
	]);

	const axisTicks = [0, 50, 100, 150, 200, 250];
	const axisY = $derived(M.top + 2 * ROW_H + ROW_GAP + 8);
</script>

<figure class="aqi-scale" bind:clientWidth={width}>
	{#if width > 0}
		<svg {width} height={HEIGHT} viewBox="0 0 {width} {HEIGHT}" role="img" aria-label={i18n.t('aqiScale.axis')}>
			{#each rows as row (row.label)}
				<text x={M.left - 8} y={row.y + ROW_H / 2} dy="0.32em" text-anchor="end" class="row-label">
					{row.label}
				</text>
				{#each row.bands as band (band.idx)}
					{@const bx = x(band.x0)}
					{@const bw = x(band.x1) - x(band.x0)}
					<rect x={bx} y={row.y} width={bw} height={ROW_H} fill={band.color} />
					{#if bw > 58}
						<text x={bx + bw / 2} y={row.y + ROW_H / 2} dy="0.32em" text-anchor="middle" class="band-label" class:on-dark={band.idx >= 3}>
							{row.labels[band.idx]}
						</text>
					{/if}
				{/each}
			{/each}

			<!-- shared concentration axis -->
			{#each axisTicks as tick (tick)}
				<text x={x(tick)} y={axisY + 14} text-anchor="middle" class="tick">{tick}</text>
				<line x1={x(tick)} x2={x(tick)} y1={axisY - 4} y2={axisY + 2} class="tick-line" />
			{/each}
			<text x={(x(0) + x(MAX)) / 2} y={axisY + 32} text-anchor="middle" class="axis-title">
				{i18n.t('aqiScale.axis')}
			</text>

			<!-- the "same day, two verdicts" marker -->
			<line x1={x(MARKER)} x2={x(MARKER)} y1={M.top - 22} y2={axisY} class="marker" />
			<circle cx={x(MARKER)} cy={M.top - 22} r="4" class="marker-dot" />
			<text x={x(MARKER) + 8} y={M.top - 26} class="marker-label">
				{i18n.t('aqiScale.marker')}
			</text>
		</svg>
	{/if}
</figure>

<style>
	.aqi-scale {
		width: 100%;
		margin: 0;
	}
	svg {
		display: block;
		overflow: visible;
	}
	.row-label {
		font-size: 0.8rem;
		font-weight: 700;
		fill: var(--color-ink);
	}
	.band-label {
		font-size: 0.7rem;
		fill: var(--color-ink);
	}
	.band-label.on-dark {
		fill: var(--color-paper);
	}
	.tick {
		font-size: 0.7rem;
		fill: var(--color-ink-muted);
		font-variant-numeric: tabular-nums;
	}
	.tick-line {
		stroke: var(--color-ink-muted);
		stroke-width: 1;
	}
	.axis-title {
		font-size: 0.75rem;
		fill: var(--color-ink-muted);
	}
	.marker {
		stroke: var(--color-ink);
		stroke-width: 1.5;
		stroke-dasharray: 4 3;
	}
	.marker-dot {
		fill: var(--color-ink);
	}
	.marker-label {
		font-size: 0.75rem;
		font-weight: 700;
		fill: var(--color-ink);
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3;
	}
</style>
