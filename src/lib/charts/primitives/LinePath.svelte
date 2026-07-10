<script lang="ts">
	// Single line series (median, thresholds, rolling means).
	import { curveMonotoneX, line } from 'd3';

	interface LinePoint {
		x: number;
		y: number | null;
	}

	let {
		x,
		y,
		data,
		stroke = 'var(--color-median)',
		strokeWidth = 2,
		dashed = false,
		opacity = 1
	}: {
		x: d3.ScaleLinear<number, number>;
		y: d3.ScaleLinear<number, number>;
		data: LinePoint[];
		stroke?: string;
		strokeWidth?: number;
		dashed?: boolean;
		opacity?: number;
	} = $props();

	const gen = line<LinePoint>()
		.defined((p) => p.y != null)
		.curve(curveMonotoneX);

	const d = $derived(gen.x((p) => x(p.x)).y((p) => y(p.y!))(data) ?? '');
</script>

<path
	{d}
	fill="none"
	{stroke}
	stroke-width={strokeWidth}
	stroke-dasharray={dashed ? '5 4' : undefined}
	stroke-linecap="round"
	{opacity}
/>
