<script lang="ts">
	// Chart frame: measures its own width, builds x/y scales, hands them to
	// children via a snippet parameter. All chart primitives are pure SVG;
	// D3 is used for math only.
	import { scaleLinear } from 'd3';
	import type { Snippet } from 'svelte';

	interface ChartCtx {
		x: d3.ScaleLinear<number, number>;
		y: d3.ScaleLinear<number, number>;
		width: number;
		height: number;
		margins: { top: number; right: number; bottom: number; left: number };
	}

	let {
		xDomain,
		yDomain,
		height = 420,
		marginTop = 24,
		marginRight = 24,
		marginBottom = 32,
		marginLeft = 44,
		ariaLabel = '',
		children
	}: {
		xDomain: [number, number];
		yDomain: [number, number];
		height?: number;
		marginTop?: number;
		marginRight?: number;
		marginBottom?: number;
		marginLeft?: number;
		ariaLabel?: string;
		children: Snippet<[ChartCtx]>;
	} = $props();

	let width = $state(0);

	const x = $derived(
		scaleLinear()
			.domain(xDomain)
			.range([marginLeft, Math.max(width - marginRight, marginLeft + 1)])
	);
	const y = $derived(
		scaleLinear()
			.domain(yDomain)
			.range([height - marginBottom, marginTop])
	);
	const margins = $derived({
		top: marginTop,
		right: marginRight,
		bottom: marginBottom,
		left: marginLeft
	});
</script>

<div class="chart-frame" bind:clientWidth={width}>
	{#if width > 0}
		<svg {width} {height} viewBox="0 0 {width} {height}" role="img" aria-label={ariaLabel}>
			{@render children({ x, y, width, height, margins })}
		</svg>
	{/if}
</div>

<style>
	.chart-frame {
		position: relative;
		width: 100%;
	}
	svg {
		display: block;
		overflow: visible;
	}
</style>
