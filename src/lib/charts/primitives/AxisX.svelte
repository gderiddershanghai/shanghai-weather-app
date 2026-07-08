<script lang="ts">
	// Horizontal axis: parent supplies tick positions + labels (keeps this
	// primitive idiom-agnostic: DOY months, years, temperature bins...).
	// Decluttered by default: no axis line, no tick marks, just labels.
	interface Tick {
		value: number;
		label: string;
	}

	let {
		x,
		y,
		ticks,
		baseline = false
	}: {
		x: d3.ScaleLinear<number, number>;
		y: d3.ScaleLinear<number, number>;
		ticks: Tick[];
		baseline?: boolean;
	} = $props();

	const [y0] = $derived(y.range());
</script>

<g class="axis axis-x" aria-hidden="true">
	{#if baseline}
		<line x1={x.range()[0]} x2={x.range()[1]} y1={y0} y2={y0} class="baseline" />
	{/if}
	{#each ticks as tick (tick.value)}
		<text x={x(tick.value)} y={y0 + 20} text-anchor="middle">{tick.label}</text>
	{/each}
</g>

<style>
	text {
		font-size: 0.75rem;
		fill: var(--color-ink-muted);
	}
	.baseline {
		stroke: var(--color-border);
		stroke-width: 1;
	}
</style>
