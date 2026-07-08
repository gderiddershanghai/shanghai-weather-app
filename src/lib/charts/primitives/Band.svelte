<script lang="ts">
	// Area band between two series (e.g. the p05–p95 "normal range").
	import { area, curveMonotoneX } from 'd3';

	interface BandPoint {
		x: number;
		y0: number | null;
		y1: number | null;
	}

	let {
		x,
		y,
		data,
		fill = 'var(--color-band)',
		opacity = 1
	}: {
		x: d3.ScaleLinear<number, number>;
		y: d3.ScaleLinear<number, number>;
		data: BandPoint[];
		fill?: string;
		opacity?: number;
	} = $props();

	// generator is stateless — reuse across renders, only `d` recomputes
	const gen = area<BandPoint>()
		.defined((p) => p.y0 != null && p.y1 != null)
		.curve(curveMonotoneX);

	const d = $derived(
		gen
			.x((p) => x(p.x))
			.y0((p) => y(p.y0!))
			.y1((p) => y(p.y1!))(data) ?? ''
	);
</script>

<path {d} {fill} {opacity} stroke="none" />
