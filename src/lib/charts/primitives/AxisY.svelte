<script lang="ts">
	// Vertical axis with faint horizontal gridlines. Unit goes on the top
	// tick only ("40°C") — less ink than labeling every tick.
	let {
		x,
		y,
		tickCount = 5,
		unit = ''
	}: {
		x: d3.ScaleLinear<number, number>;
		y: d3.ScaleLinear<number, number>;
		tickCount?: number;
		unit?: string;
	} = $props();

	const ticks = $derived(y.ticks(tickCount));
	const [x0, x1] = $derived(x.range());
</script>

<g class="axis axis-y" aria-hidden="true">
	{#each ticks as tick, i (tick)}
		<line x1={x0} x2={x1} y1={y(tick)} y2={y(tick)} class="grid" />
		<text x={x0 - 8} y={y(tick)} dy="0.32em" text-anchor="end">
			{tick}{i === ticks.length - 1 ? unit : ''}
		</text>
	{/each}
</g>

<style>
	text {
		font-size: 0.75rem;
		fill: var(--color-ink-muted);
		font-variant-numeric: tabular-nums;
	}
	.grid {
		stroke: var(--color-border);
		stroke-width: 0.5;
		opacity: 0.6;
	}
</style>
